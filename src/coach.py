"""AI Leadership Coach using Claude (Anthropic API or AWS Bedrock)."""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List

from dotenv import load_dotenv

from .utils import load_config, load_leadership_principles

logger = logging.getLogger("zoom_coach")

load_dotenv()


SYSTEM_ROLE = (
    "You are an expert leadership coach helping a leader improve their "
    "effectiveness. Analyze meetings and provide actionable, specific feedback "
    "based on their personal leadership principles."
)


class _AnthropicProvider:
    """Calls Claude via the Anthropic API."""

    powered_by = "Claude"

    def __init__(self):
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Please add it to your .env file."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_id = os.getenv(
            "ANTHROPIC_MODEL", "claude-sonnet-4-20250514"
        )

    def invoke(self, system: list, user_prompt: str, max_tokens: int) -> str:
        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text


class _BedrockProvider:
    """Calls Claude via AWS Bedrock with streaming output."""

    powered_by = "Claude via AWS Bedrock"

    def __init__(self):
        import boto3

        missing = [v for v in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY") if not os.getenv(v)]
        if missing:
            raise ValueError(
                f"Missing AWS credentials: {', '.join(missing)}\n"
                "Please run 'claude-up' first to authenticate with AWS Bedrock."
            )

        self.region = os.getenv("AWS_REGION", "us-west-2")

        use_fast = os.getenv("USE_FAST_MODEL", "false").lower() == "true"
        if use_fast:
            self.model_id = os.getenv(
                "ANTHROPIC_SMALL_FAST_MODEL",
                "us.anthropic.claude-haiku-4-5-20251001-v1:0",
            )
        else:
            self.model_id = os.getenv(
                "ANTHROPIC_MODEL",
                "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            )

        try:
            self.client = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.region,
            )
            logger.info(f"Connected to AWS Bedrock in {self.region}")
            logger.info(f"Using model: {self.model_id}")
        except Exception as e:
            raise ValueError(
                f"Failed to connect to AWS Bedrock: {e}\n"
                "Make sure you've run 'claude-up' to authenticate."
            )

    def invoke(self, system: list, user_prompt: str, max_tokens: int) -> str:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        response = self.client.invoke_model_with_response_stream(
            modelId=self.model_id,
            body=json.dumps(request_body),
        )

        text_parts = []
        input_tokens = 0
        output_tokens = 0
        for event in response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            event_type = chunk.get("type")
            if event_type == "content_block_delta":
                delta = chunk.get("delta", {})
                if delta.get("type") == "text_delta":
                    text_parts.append(delta.get("text", ""))
            elif event_type == "message_start":
                input_tokens = chunk.get("message", {}).get("usage", {}).get("input_tokens", 0)
            elif event_type == "message_delta":
                output_tokens = chunk.get("usage", {}).get("output_tokens", output_tokens)
        logger.info(f"Token usage - Input: {input_tokens}, Output: {output_tokens}")
        return "".join(text_parts)


def _build_provider():
    """Select the Claude backend based on USE_BEDROCK env var."""
    if os.getenv("USE_BEDROCK", "false").lower() == "true":
        return _BedrockProvider()
    return _AnthropicProvider()


class LeadershipCoach:
    """AI-powered leadership coach using Claude."""

    def __init__(self, provider=None):
        self.provider = provider or _build_provider()
        self.config = load_config()["coaching"]
        self.leadership_principles = load_leadership_principles()
        # Bedrock streaming path uses a tighter token budget; Anthropic can afford more.
        self.max_tokens = 3500 if isinstance(self.provider, _BedrockProvider) else 8000

    def analyze_meeting(
        self, meeting_data: Dict, calendar_availability: List[datetime]
    ) -> Dict:
        """Analyze a meeting and produce a structured coaching analysis."""
        logger.info(f"Analyzing meeting: {meeting_data['title']}")

        prompt = self._build_analysis_prompt(meeting_data, calendar_availability)
        system = [
            {"type": "text", "text": SYSTEM_ROLE},
            {
                "type": "text",
                "text": f"# Leader's Personal Principles\n\n{self.leadership_principles}",
                "cache_control": {"type": "ephemeral"},
            },
        ]

        try:
            analysis_text = self.provider.invoke(system, prompt, self.max_tokens)
        except Exception as e:
            logger.error(f"Error during coaching analysis: {e}")
            return {
                "error": str(e),
                "meeting_summary": meeting_data.get("summary", ""),
                "action_items": meeting_data.get("action_items", []),
            }

        logger.info("Meeting analysis complete")
        return {
            "meeting_title": meeting_data["title"],
            "meeting_date": meeting_data.get("date"),
            "analysis_date": datetime.now().isoformat(),
            "full_analysis": analysis_text,
            "original_action_items": meeting_data.get("action_items", []),
            "available_slots": [slot.isoformat() for slot in calendar_availability[:10]],
        }

    def _build_analysis_prompt(
        self, meeting_data: Dict, calendar_availability: List[datetime]
    ) -> str:
        """Build the user prompt for Claude."""
        lenses = []
        if self.config.get("include_communication_analysis", True):
            lenses.append("Communication (listening, questions, facilitation)")
        if self.config.get("include_decision_making_review", True):
            lenses.append("Decision Making (data, input-seeking, reasoning)")
        if self.config.get("include_team_dynamics", True):
            lenses.append("Team Dynamics (psychological safety, empowerment)")
        if self.config.get("include_time_management", True):
            lenses.append("Time Management (load, delegation)")
        lenses_text = "; ".join(lenses) if lenses else "Communication; Decision Making"

        return f"""Analyze this meeting and coach the leader against their principles. Be concise and specific — aim for tight bullets, not essays.

# Meeting
**Title:** {meeting_data['title']}
**Date:** {meeting_data.get('date', 'Unknown')}
**Participants:** {', '.join(meeting_data.get('participants', ['Unknown']))}

## Summary
{meeting_data.get('summary', 'No summary available')}

## Key Points
{_format_list(meeting_data.get('key_points', []))}

## Action Items
{_format_action_items(meeting_data.get('action_items', []))}

## Decisions
{_format_list(meeting_data.get('decisions', []))}

## Open Questions
{_format_list(meeting_data.get('questions', []))}

# Calendar Availability (next 10 slots)
{_format_availability(calendar_availability[:10])}

# Output (use these exact sections, keep each tight)

## 1. Action Items — Prioritized
For each action item: priority (H/M/L), estimated duration, who should own it (delegate vs. leader), 1-line reasoning.

## 2. Recommended Schedule
Map leader-owned items to specific slots above. Format: `Task — Slot — Duration — Why`.

## 3. Coaching (lenses: {lenses_text})
2-4 crisp observations tied to the leader's principles. Cite a specific moment per observation.

## 4. Growth + Wins
- 2 growth areas (specific, actionable, tied to principles)
- 2 wins to reinforce
"""

    def generate_coaching_report(self, analysis: Dict, output_path: str) -> None:
        """Write a markdown coaching report to disk."""
        lines = [
            "# Leadership Coaching Report",
            "",
            f"**Meeting:** {analysis['meeting_title']}",
            f"**Meeting Date:** {analysis.get('meeting_date', 'Unknown')}",
            f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            "",
            analysis["full_analysis"],
            "",
            "---",
            "",
            "## Original Action Items",
            "",
        ]
        for item in analysis.get("original_action_items", []):
            parts = [f"- {item['task']}"]
            if item.get("owner"):
                parts.append(f"(Owner: {item['owner']})")
            if item.get("due_date"):
                parts.append(f"(Due: {item['due_date']})")
            lines.append(" ".join(parts))

        lines.extend([
            "",
            "---",
            "",
            "*Generated by Zoom Leadership Coach*",
            f"*Powered by {self.provider.powered_by}*",
            "",
        ])

        with open(output_path, "w") as f:
            f.write("\n".join(lines))
        logger.info(f"Coaching report saved to {output_path}")


def _format_list(items: List[str]) -> str:
    if not items:
        return "None"
    return "\n".join(f"- {item}" for item in items)


def _format_action_items(items: List[Dict]) -> str:
    if not items:
        return "None"
    formatted = []
    for item in items:
        parts = [f"- {item['task']}"]
        if item.get("owner"):
            parts.append(f"(Owner: {item['owner']})")
        if item.get("due_date"):
            parts.append(f"(Due: {item['due_date']})")
        formatted.append(" ".join(parts))
    return "\n".join(formatted)


def _format_availability(slots: List[datetime]) -> str:
    if not slots:
        return "No availability data"
    return "\n".join(
        f"{i}. {slot.strftime('%A, %B %d at %I:%M %p')}"
        for i, slot in enumerate(slots, 1)
    )
