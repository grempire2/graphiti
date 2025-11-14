"""
Copyright 2024, Zep Software, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import logging
import typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import groq
    from groq import AsyncGroq
    from groq.types.chat import ChatCompletionMessageParam
else:
    try:
        import groq
        from groq import AsyncGroq
        from groq.types.chat import ChatCompletionMessageParam
    except ImportError:
        raise ImportError(
            "groq is required for GroqClient. Install it with: pip install graphiti-core[groq]"
        ) from None
from pydantic import BaseModel

from ..prompts.models import Message
from .client import LLMClient
from .config import LLMConfig, ModelSize
from .errors import RateLimitError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "llama-3.1-70b-versatile"
DEFAULT_MAX_TOKENS = 2048


class GroqClient(LLMClient):
    def __init__(self, config: LLMConfig | None = None, cache: bool = False):
        if config is None:
            config = LLMConfig(max_tokens=DEFAULT_MAX_TOKENS)
        elif config.max_tokens is None:
            config.max_tokens = DEFAULT_MAX_TOKENS
        super().__init__(config, cache)

        self.client = AsyncGroq(api_key=config.api_key)

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        msgs: list[ChatCompletionMessageParam] = []
        for m in messages:
            if m.role == "user":
                msgs.append({"role": "user", "content": m.content})
            elif m.role == "system":
                msgs.append({"role": "system", "content": m.content})
        try:
            # Only force JSON format when we need structured output
            # (when response_model is provided, the base class adds JSON instructions to the prompt)
            request_params = {
                "model": self.model or DEFAULT_MODEL,
                "messages": msgs,
                "temperature": self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
            }
            if response_model is not None:
                # Use Groq's structured outputs with JSON schema enforcement
                # This ensures API-level schema validation, similar to Gemini
                json_schema = response_model.model_json_schema()
                request_params["response_format"] = {
                    "type": "json_schema",
                    "json_schema": json_schema,
                }

            response = await self.client.chat.completions.create(**request_params)
            result = response.choices[0].message.content or ""

            # If structured output was requested, parse and validate
            if response_model is not None:
                try:
                    parsed_json = json.loads(result)
                    
                    # Groq's json_schema format might wrap the response in a 'properties' key
                    # Try to unwrap if needed. Check if the top-level dict only has 'properties'
                    # and the properties dict contains the actual model fields
                    if isinstance(parsed_json, dict):
                        # If we have a 'properties' key and it contains the model fields, use it
                        if 'properties' in parsed_json and isinstance(parsed_json.get('properties'), dict):
                            properties = parsed_json['properties']
                            # Check if properties contains fields that match the model
                            # (e.g., duplicate_facts, contradicted_facts, fact_type for EdgeDuplicate)
                            model_fields = set(response_model.model_fields.keys())
                            if model_fields.intersection(properties.keys()):
                                parsed_json = properties
                    
                    # Validate against the response model for additional safety
                    # (API should enforce this, but we validate as a safeguard)
                    validated_model = response_model.model_validate(parsed_json)
                    # Return as a dictionary for API consistency
                    return validated_model.model_dump()
                except Exception as e:
                    logger.error(f"Failed to parse structured response: {e}")
                    logger.error(
                        f"Response: {result[:1000]}..."
                        if len(result) > 1000
                        else f"Response: {result}"
                    )
                    if 'parsed_json' in locals():
                        logger.error(f"Parsed JSON structure: {parsed_json}")
                    raise Exception(f"Failed to parse structured response: {e}") from e
            else:
                # For plain text responses, try to parse as JSON first
                # If that fails, wrap the text in a dict
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {"content": result}
        except groq.RateLimitError as e:
            raise RateLimitError from e
        except Exception as e:
            logger.error(f"Error in generating LLM response: {e}")
            raise
