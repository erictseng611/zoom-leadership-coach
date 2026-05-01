"""AI Leadership Coach using AWS Bedrock."""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List

import boto3
from dotenv import load_dotenv

from .utils import load_config, load_leadership_principles

logger = logging.getLogger("zoom_coach")

load_dotenv()


class BedrockLeadershipCoach:
    """AI-powered leadership coach using AWS Bedrock."""

    def __init__(self):
        """Initialize the Bedrock leadership coach."""
        # Check for AWS credentials from claude-up
        required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise ValueError(
                f"Missing AWS credentials: {', '.join(missing_vars)}\n"
                "Please run 'claude-up' first to authenticate with AWS Bedrock."
            )

        # Get region (default to us-west-2 if not specified)
        self.region = os.getenv("AWS_REGION", "us-west-2")

        # --fast / USE_FAST_MODEL=true selects Haiku for 3-5x speedup, and
        # overrides any globally-set ANTHROPIC_MODEL (e.g. from claude-up).
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

        # Initialize Bedrock client
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

        self.config = load_config()["coaching"]
        self.leadership_principles = load_leadership_principles()

    def analyze_meeting(
        self, meeting_data: Dict, calendar_availability: List[datetime]
    ) -> Dict:
        """
        Analyze meeting and provide leadership coaching.

        Args:
            meeting_data: Parsed meeting data
            calendar_availability: List of available time slots

        Returns:
            Coaching analysis with action items and suggestions
        """
        logger.info(f"Analyzing meeting: {meeting_data['title']}")

        # Build the analysis prompt
        prompt = self._build_analysis_prompt(meeting_data, calendar_availability)

        try:
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 3500,
                "system": [
                    {
                        "type": "text",
                        "text": "You are an expert leadership coach helping a leader improve their effectiveness. "
                        "Analyze meetings and provide actionable, specific feedback based on their personal leadership principles.",
                    },
                    {
                        "type": "text",
                        "text": f"# Leader's Personal Principles\n\n{self.leadership_principles}",
                        "cache_control": {"type": "ephemeral"},
                    },
                ],
                "messages": [{"role": "user", "content": prompt}],
            }

            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(request_body),
            )

            analysis_text = ""
            input_tokens = 0
            output_tokens = 0
            sys.stdout.write("\n")
            for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])
                event_type = chunk.get("type")
                if event_type == "content_block_delta":
                    delta = chunk.get("delta", {})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")
                        analysis_text += text
                        sys.stdout.write(text)
                        sys.stdout.flush()
                elif event_type == "message_start":
                    usage = chunk.get("message", {}).get("usage", {})
                    input_tokens = usage.get("input_tokens", 0)
                elif event_type == "message_delta":
                    usage = chunk.get("usage", {})
                    output_tokens = usage.get("output_tokens", output_tokens)
            sys.stdout.write("\n")
            sys.stdout.flush()

            logger.info(
                f"Token usage - Input: {input_tokens}, Output: {output_tokens}"
            )

            parsed_analysis = self._parse_coaching_response(
                analysis_text, meeting_data, calendar_availability
            )

            logger.info("Meeting analysis complete")
            return parsed_analysis

        except Exception as e:
            logger.error(f"Error during coaching analysis: {e}")
            return {
                "error": str(e),
                "meeting_summary": meeting_data.get("summary", ""),
                "action_items": meeting_data.get("action_items", []),
            }

    def _build_analysis_prompt(
        self, meeting_data: Dict, calendar_availability: List[datetime]
    ) -> str:
        """Build the prompt for Claude analysis."""
        availability_summary = self._format_availability(calendar_availability[:10])

        coaching_lenses = []
        if self.config.get("include_communication_analysis", True):
            coaching_lenses.append("Communication (listening, questions, facilitation)")
        if self.config.get("include_decision_making_review", True):
            coaching_lenses.append("Decision Making (data, input-seeking, reasoning)")
        if self.config.get("include_team_dynamics", True):
            coaching_lenses.append("Team Dynamics (psychological safety, empowerment)")
        if self.config.get("include_time_management", True):
            coaching_lenses.append("Time Management (load, delegation)")
        lenses_text = "; ".join(coaching_lenses) if coaching_lenses else "Communication; Decision Making"

        prompt = f"""Analyze this meeting and coach the leader against their principles. Be concise and specific — aim for tight bullets, not essays.

# Meeting
**Title:** {meeting_data['title']}
**Date:** {meeting_data.get('date', 'Unknown')}
**Participants:** {', '.join(meeting_data.get('participants', ['Unknown']))}

## Summary
{meeting_data.get('summary', 'No summary available')}

## Key Points
{self._format_list(meeting_data.get('key_points', []))}

## Action Items
{self._format_action_items(meeting_data.get('action_items', []))}

## Decisions
{self._format_list(meeting_data.get('decisions', []))}

## Open Questions
{self._format_list(meeting_data.get('questions', []))}

# Calendar Availability (next 10 slots)
{availability_summary}

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

        return prompt

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items for the prompt."""
        if not items:
            return "None"
        return "\n".join(f"- {item}" for item in items)

    def _format_action_items(self, items: List[Dict]) -> str:
        """Format action items for the prompt."""
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

    def _format_availability(self, slots: List[datetime]) -> str:
        """Format available time slots."""
        if not slots:
            return "No availability data"

        formatted = []
        for i, slot in enumerate(slots, 1):
            formatted.append(f"{i}. {slot.strftime('%A, %B %d at %I:%M %p')}")

        return "\n".join(formatted)

    def _parse_coaching_response(
        self, response_text: str, meeting_data: Dict, calendar_availability: List[datetime]
    ) -> Dict:
        """Parse Claude's response into structured data."""
        return {
            "meeting_title": meeting_data["title"],
            "meeting_date": meeting_data.get("date"),
            "analysis_date": datetime.now().isoformat(),
            "full_analysis": response_text,
            "original_action_items": meeting_data.get("action_items", []),
            "available_slots": [
                slot.isoformat() for slot in calendar_availability[:10]
            ],
        }

    def generate_coaching_report(self, analysis: Dict, output_path: str) -> None:
        """
        Generate a markdown coaching report.

        Args:
            analysis: Coaching analysis data
            output_path: Path to save the report
        """
        report = f"""# Leadership Coaching Report

**Meeting:** {analysis['meeting_title']}
**Meeting Date:** {analysis.get('meeting_date', 'Unknown')}
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

{analysis['full_analysis']}

---

## Original Action Items

"""

        for item in analysis.get("original_action_items", []):
            report += f"- {item['task']}"
            if item.get("owner"):
                report += f" (Owner: {item['owner']})"
            if item.get("due_date"):
                report += f" (Due: {item['due_date']})"
            report += "\n"

        report += f"""
---

*Generated by Zoom Leadership Coach*
*Powered by Claude via AWS Bedrock*
"""

        with open(output_path, "w") as f:
            f.write(report)

        logger.info(f"Coaching report saved to {output_path}")
