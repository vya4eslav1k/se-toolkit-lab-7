"""
LLM Client with tool calling support.

Sends messages to the LLM with tool definitions and executes tool calls.
"""

import httpx
import json
from typing import Optional, Any
from dataclasses import dataclass
from config import load_config


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""
    name: str
    arguments: dict[str, Any]


class LLMClient:
    """Client for LLM with tool calling support."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create an HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        system_prompt: Optional[str] = None,
    ) -> tuple[str, list[ToolCall]]:
        """
        Send a chat message to the LLM.

        Args:
            messages: Conversation history (list of {role, content} dicts)
            tools: List of tool schemas for function calling
            system_prompt: Optional system prompt to prepend

        Returns:
            Tuple of (response_text, list_of_tool_calls)
        """
        client = self._get_client()

        # Build messages with system prompt
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        # Build request body
        body: dict = {
            "model": self.model,
            "messages": all_messages,
        }

        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        try:
            response = client.post("/chat/completions", json=body)
            response.raise_for_status()
            data = response.json()

            # Extract response
            choice = data["choices"][0]["message"]
            content = choice.get("content", "")

            # Extract tool calls
            tool_calls = []
            if "tool_calls" in choice and choice["tool_calls"]:
                for tc in choice["tool_calls"]:
                    if tc.get("type") == "function":
                        func = tc.get("function", {})
                        try:
                            args = json.loads(func.get("arguments", "{}"))
                        except json.JSONDecodeError:
                            args = {}
                        tool_calls.append(ToolCall(
                            name=func.get("name", ""),
                            arguments=args,
                        ))

            return content, tool_calls

        except httpx.HTTPStatusError as e:
            raise LLMError(f"HTTP {e.response.status_code}: {e.response.text}") from e
        except httpx.HTTPError as e:
            raise LLMError(f"HTTP error: {type(e).__name__}: {e}") from e
        except Exception as e:
            raise LLMError(f"LLM error: {type(e).__name__}: {e}") from e

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None


class LLMError(Exception):
    """Custom exception for LLM errors."""
    pass


def get_llm_client() -> LLMClient:
    """Create an LLM client from config."""
    config = load_config()
    return LLMClient(
        api_key=config["LLM_API_KEY"],
        base_url=config["LLM_API_BASE_URL"],
        model=config["LLM_API_MODEL"],
    )
