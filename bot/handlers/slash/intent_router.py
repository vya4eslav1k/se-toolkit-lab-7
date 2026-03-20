"""
Intent router for natural language queries.

Routes user messages to the LLM, which decides which tools to call.
Tool results are fed back to the LLM for final answer generation.
"""

import sys
import json
from typing import Optional

from services.api_client import LmsApiClient, LmsApiError
from services.llm_client import LLMClient, ToolCall, get_llm_client, LLMError
from config import load_config


# Define all 9 backend endpoints as LLM tool schemas
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get the list of all labs and tasks. Use this to discover what labs are available or to get lab identifiers.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get the list of enrolled students and their group assignments. Use this to find information about learners.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution (4 buckets) for a specific lab. Use this to see how scores are distributed across ranges.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                    },
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average scores and attempt counts for a specific lab. Use this to see which tasks are hardest or easiest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                    },
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get submission timeline (submissions per day) for a specific lab. Use this to see activity patterns over time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                    },
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group scores and student counts for a specific lab. Use this to compare group performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                    },
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top N learners by score for a specific lab. Use this to find the best performing students.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top learners to return, default 5",
                    },
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get completion rate percentage for a specific lab. Use this to see what percentage of students completed the lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                    },
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Trigger an ETL sync to refresh data from the autochecker. Use this when the user asks to update or refresh the data.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

# System prompt for tool use
SYSTEM_PROMPT = """You are an AI assistant for a Learning Management System (LMS). You have access to tools that fetch data about labs, students, scores, and analytics.

When a user asks a question:
1. First understand what they're asking
2. Call the appropriate tool(s) to get the data
3. Feed the tool results back to analyze
4. Provide a clear, helpful answer based on the actual data

Available tools:
- get_items: List all labs and tasks (use to find lab IDs)
- get_learners: List enrolled students
- get_scores: Score distribution for a lab
- get_pass_rates: Per-task pass rates for a lab
- get_timeline: Submission timeline for a lab
- get_groups: Per-group performance for a lab
- get_top_learners: Top students for a lab
- get_completion_rate: Completion percentage for a lab
- trigger_sync: Refresh data from autochecker

For questions about "which lab has the lowest/highest pass rate", you need to:
1. First call get_items to get all lab IDs
2. Then call get_pass_rates for each lab
3. Compare the results and identify the answer

For greetings or unclear messages, respond helpfully without using tools.

Always base your answers on the actual data returned by tools. If you don't have data, say so clearly."""


class IntentRouter:
    """Routes natural language queries to LLM with tool execution."""

    def __init__(self):
        self.llm = get_llm_client()
        self.api = LmsApiClient(
            base_url=load_config()["LMS_API_URL"],
            api_key=load_config()["LMS_API_KEY"],
        )

    def _execute_tool(self, tool_call: ToolCall) -> str:
        """Execute a tool call and return the result as a JSON string."""
        name = tool_call.name
        args = tool_call.arguments

        print(f"[tool] LLM called: {name}({args})", file=sys.stderr)

        try:
            if name == "get_items":
                result = self.api.get_items()
            elif name == "get_learners":
                # Not implemented in api_client yet, return placeholder
                result = []
            elif name == "get_scores":
                # Maps to analytics/scores endpoint
                result = self._call_analytics("scores", args.get("lab", ""))
            elif name == "get_pass_rates":
                result = self.api.get_pass_rates(args.get("lab", ""))
            elif name == "get_timeline":
                result = self._call_analytics("timeline", args.get("lab", ""))
            elif name == "get_groups":
                result = self._call_analytics("groups", args.get("lab", ""))
            elif name == "get_top_learners":
                result = self._call_analytics(
                    "top-learners",
                    args.get("lab", ""),
                    limit=args.get("limit", 5),
                )
            elif name == "get_completion_rate":
                result = self._call_analytics("completion-rate", args.get("lab", ""))
            elif name == "trigger_sync":
                result = self._trigger_sync()
            else:
                result = {"error": f"Unknown tool: {name}"}

            # Convert result to JSON string for LLM
            result_str = json.dumps(result)
            print(f"[tool] Result: {len(result_str)} chars", file=sys.stderr)
            return result_str

        except LmsApiError as e:
            error_msg = json.dumps({"error": f"Tool {name} error: {e.message}"})
            print(f"[tool] Error: {error_msg}", file=sys.stderr)
            return error_msg
        except Exception as e:
            error_msg = json.dumps({"error": f"Tool {name} error: {type(e).__name__}: {e}"})
            print(f"[tool] Error: {error_msg}", file=sys.stderr)
            return error_msg

    def _call_analytics(
        self,
        endpoint: str,
        lab: str,
        limit: Optional[int] = None,
    ) -> list:
        """Call an analytics endpoint."""
        import httpx
        config = load_config()
        url = f"{config['LMS_API_URL']}/analytics/{endpoint}"
        params = {"lab": lab}
        if limit:
            params["limit"] = limit
        try:
            with httpx.Client() as client:
                response = client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {config['LMS_API_KEY']}"},
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise LmsApiError(f"analytics/{endpoint}: {type(e).__name__}: {e}")

    def _trigger_sync(self) -> dict:
        """Trigger ETL sync."""
        import httpx
        config = load_config()
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{config['LMS_API_URL']}/pipeline/sync",
                    headers={
                        "Authorization": f"Bearer {config['LMS_API_KEY']}",
                        "Content-Type": "application/json",
                    },
                    json={},
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise LmsApiError(f"pipeline/sync: {type(e).__name__}: {e}")

    def route(self, message: str) -> str:
        """
        Route a natural language message through the LLM.

        The LLM decides which tools to call. Tool results are fed back
        to the LLM for final answer generation.

        Args:
            message: User's natural language query

        Returns:
            The LLM's final response
        """
        # Initial conversation state
        messages = [{"role": "user", "content": message}]

        # Maximum iterations to prevent infinite loops
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            try:
                # Call LLM with tools
                response_text, tool_calls = self.llm.chat(
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    system_prompt=SYSTEM_PROMPT,
                )

                # If no tool calls, return the response
                if not tool_calls:
                    return response_text

                # Execute tool calls and collect results
                tool_results = []
                for tc in tool_calls:
                    result = self._execute_tool(tc)
                    tool_results.append({
                        "tool_call_id": tc.name,  # Simplified ID
                        "role": "tool",
                        "name": tc.name,
                        "content": result,
                    })

                # Add tool results to conversation
                print(
                    f"[summary] Feeding {len(tool_results)} tool result(s) back to LLM",
                    file=sys.stderr,
                )

                # Simplified approach: append tool results as a user message
                # This works better with models that don't fully support tool calling
                if tool_results:
                    tool_summary = "Here are the results from the tools you called:\n\n"
                    for result in tool_results:
                        tool_summary += f"=== {result['name']} ===\n{result['content']}\n\n"
                    tool_summary += "Now provide a helpful answer to the user's original question based on this data."
                    
                    messages.append({"role": "user", "content": tool_summary})

            except LLMError as e:
                return f"LLM error: {e}"
            except Exception as e:
                return f"Unexpected error: {type(e).__name__}: {e}"

        return "I'm having trouble answering this question. Please try rephrasing or use a slash command like /help."


def handle_natural_language(message: str) -> str:
    """
    Handle a natural language message using the intent router.

    This is the entry point for plain text queries.
    """
    router = IntentRouter()
    return router.route(message)
