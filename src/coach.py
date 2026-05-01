"""AI Leadership Coach using Claude API."""

import logging
import os
from datetime import datetime
from typing import Dict, List

import anthropic
from dotenv import load_dotenv

from .utils import load_config, load_leadership_principles

logger = logging.getLogger("zoom_coach")

load_dotenv()


class LeadershipCoach:
    """AI-powered leadership coach using Claude."""

    def __init__(self):
        """Initialize the leadership coach."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Please add it to your .env file."
            )

        self.client = anthropic.Anthropic(api_key=api_key)
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
            # Call Claude API with prompt caching for leadership principles
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                system=[
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
                messages=[{"role": "user", "content": prompt}],
            )

            analysis_text = response.content[0].text

            # Parse the response into structured format
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

        prompt = f"""Analyze this meeting and provide leadership coaching based on the leader's personal principles.

# Meeting Information

**Title:** {meeting_data['title']}
**Date:** {meeting_data.get('date', 'Unknown')}
**Participants:** {', '.join(meeting_data.get('participants', ['Unknown']))}

## Summary
{meeting_data.get('summary', 'No summary available')}

## Key Points
{self._format_list(meeting_data.get('key_points', []))}

## Action Items
{self._format_action_items(meeting_data.get('action_items', []))}

## Decisions Made
{self._format_list(meeting_data.get('decisions', []))}

## Questions/Open Items
{self._format_list(meeting_data.get('questions', []))}

# Calendar Availability (Next 10 Slots)
{availability_summary}

# Your Task

Provide a comprehensive leadership coaching analysis with the following sections:

## 1. Meeting Effectiveness Assessment
- Evaluate the meeting based on the leader's principles
- What went well? What could be improved?
- Rate the meeting on: clarity of outcomes, participant engagement, decision quality

## 2. Action Item Analysis & Prioritization
- Review all action items from the meeting
- Assign clear priorities (High/Medium/Low) with reasoning
- Estimate realistic time duration for each task (15min, 30min, 1hr, 2hr, etc.)
- Identify which items can be delegated and to whom
- Flag any action items the leader should NOT personally handle

## 3. Recommended Schedule
- Suggest specific time slots from the available calendar for each action item
- Consider:
  - Priority and due dates
  - Task duration
  - Energy levels (complex tasks in focus time)
  - Dependencies between tasks
- Format: "Task name - [Time slot] - Duration - Reasoning"

## 4. Leadership Insights
Based on the leader's principles, provide specific coaching on:
"""

        if self.config.get("include_communication_analysis", True):
            prompt += """
- **Communication**: How well did the leader listen? Ask questions? Facilitate discussion?
"""

        if self.config.get("include_decision_making_review", True):
            prompt += """
- **Decision Making**: Were decisions data-informed? Did they seek input? Communicate reasoning?
"""

        if self.config.get("include_team_dynamics", True):
            prompt += """
- **Team Dynamics**: How did they build psychological safety? Empower the team?
"""

        if self.config.get("include_time_management", True):
            prompt += """
- **Time Management**: Are they taking on too much? Delegating effectively?
"""

        prompt += """
## 5. Areas for Growth
- Identify 2-3 specific, actionable areas for improvement
- Reference specific moments from this meeting
- Tie back to the leader's stated development goals

## 6. Wins & Reinforcement
- Highlight 2-3 things the leader did well
- Reinforce behaviors that align with their principles

Be specific, actionable, and constructive. Use examples from the meeting content when possible.
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
        # For now, return the full text analysis
        # In a production version, you could parse sections more carefully

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
*Powered by Claude*
"""

        with open(output_path, "w") as f:
            f.write(report)

        logger.info(f"Coaching report saved to {output_path}")
