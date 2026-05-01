"""Parse Zoom meeting summaries and extract structured information."""

import html
import logging
import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Dict, List, Optional

logger = logging.getLogger("zoom_coach")


class _TextExtractor(HTMLParser):
    """HTMLParser that emits plain text, inserting newlines at block elements."""

    BLOCK_TAGS = {
        "p", "div", "br", "li", "ul", "ol", "tr", "td", "th", "table",
        "thead", "tbody", "h1", "h2", "h3", "h4", "h5", "h6", "section",
        "article", "header", "footer",
    }
    SKIP_TAGS = {"style", "script", "head"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._parts: List[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        elif tag in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def _looks_like_html(body: str) -> bool:
    # Treat it as HTML if it contains a closing tag or a well-known block tag.
    return bool(re.search(r"</\w+>|<(p|div|br|li|ul|ol|table|td|tr)\b", body, re.IGNORECASE))


def _html_to_text(body: str) -> str:
    """Convert an HTML body to clean plain text."""
    extractor = _TextExtractor()
    try:
        extractor.feed(body)
        extractor.close()
    except Exception as error:
        logger.warning(f"HTML parse failed, falling back to regex strip: {error}")
        stripped = re.sub(r"<[^>]+>", " ", body)
        return html.unescape(stripped)

    text = extractor.get_text()
    # Collapse runs of whitespace per line; collapse runs of blank lines.
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    collapsed: List[str] = []
    blank = False
    for line in lines:
        if line:
            collapsed.append(line)
            blank = False
        elif not blank:
            collapsed.append("")
            blank = True
    return "\n".join(collapsed).strip()


def _is_garbage_line(line: str) -> bool:
    """Reject lines that are clearly not meaningful content."""
    if not line:
        return True
    # Anything still containing angle brackets after HTML strip is HTML leakage.
    if "<" in line or ">" in line:
        return True
    # Reject lines that are overwhelmingly punctuation / non-alphabetic.
    alpha = sum(1 for c in line if c.isalpha())
    if alpha < 3 or alpha / len(line) < 0.4:
        return True
    return False


class MeetingSummaryParser:
    """Parser for Zoom meeting summaries."""

    def __init__(self):
        """Initialize parser."""
        pass

    def parse(self, email_body: str, email_subject: str = "") -> Dict:
        """
        Parse meeting summary from email body.

        Args:
            email_body: Raw email body text (plain or HTML)
            email_subject: Email subject line

        Returns:
            Structured meeting data
        """
        # Zoom delivers HTML bodies; convert to plain text before extracting
        # sections so regex anchors and line splits don't match HTML fragments.
        if _looks_like_html(email_body):
            body = _html_to_text(email_body)
        else:
            body = email_body

        # Extract meeting title
        meeting_title = self._extract_meeting_title(body, email_subject)

        # Extract sections
        summary = self._extract_section(body, ["summary", "meeting summary"])
        action_items = self._extract_action_items(body)
        participants = self._extract_participants(body)
        key_points = self._extract_key_points(body)
        decisions = self._extract_decisions(body)
        questions = self._extract_questions(body)

        # Try to extract meeting date/time
        meeting_date = self._extract_date(body)

        return {
            "title": meeting_title,
            "date": meeting_date,
            "summary": summary,
            "participants": participants,
            "key_points": key_points,
            "action_items": action_items,
            "decisions": decisions,
            "questions": questions,
            "raw_content": email_body,
        }

    def _extract_meeting_title(self, body: str, subject: str) -> str:
        """Extract meeting title from body or subject."""
        # Try to find meeting title in body
        title_patterns = [
            r"Meeting:\s*(.+?)(?:\n|$)",
            r"Topic:\s*(.+?)(?:\n|$)",
            r"Subject:\s*(.+?)(?:\n|$)",
        ]

        for pattern in title_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback to subject line
        if "Meeting assets" in subject:
            return subject.replace("Meeting assets", "").strip(" -:")

        return "Meeting"

    def _extract_section(self, body: str, section_names: List[str]) -> str:
        """Extract a specific section from the body."""
        for section_name in section_names:
            # Look for section header followed by content
            pattern = rf"{section_name}[:\s]*(.+?)(?=\n\n|\n[A-Z][a-z]+:|\Z)"
            match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return ""

    # Regexes used to detect the end of the action-items section. Zoom footers
    # and the start of the next top-level heading all count as section ends.
    _ACTION_SECTION_END = re.compile(
        r"(?:^|\n)\s*("
        r"view in zoom"
        r"|ai can make mistakes"
        r"|please rate"
        r"|thank you for choosing zoom"
        r"|the zoom team"
        r"|zoom\.com"
        r"|decisions?"
        r"|summary"
        r"|key points?"
        r"|questions?"
        r"|open items?"
        r"|participants?"
        r"|highlights?"
        r"|next meeting"
        r")\b",
        re.IGNORECASE,
    )

    def _extract_action_items(self, body: str) -> List[Dict]:
        """Extract action items from the body."""
        action_items: List[Dict] = []

        section_headers = [
            r"action items?",
            r"next steps",
            r"to-?dos?",
        ]

        content = ""
        for header in section_headers:
            header_match = re.search(rf"\b{header}\b[:\s]*\n", body, re.IGNORECASE)
            if not header_match:
                continue
            start = header_match.end()
            tail = body[start:]
            end_match = self._ACTION_SECTION_END.search(tail)
            content = tail[: end_match.start()] if end_match else tail
            break

        if not content.strip():
            return action_items

        current_owner: Optional[str] = None
        for raw_line in content.split("\n"):
            line = raw_line.strip()
            if not line:
                continue

            # Strip bullet markers
            line = re.sub(r"^[-•*\d.)\]]\s*", "", line).strip()

            if _is_garbage_line(line):
                continue

            # Owner header (e.g. "Bowei", "Eric") — check before the length
            # filter so short names aren't skipped.
            if self._looks_like_owner_header(line):
                current_owner = line
                continue

            if len(line) < 5:
                continue

            inline_owner = self._extract_owner(line)
            due_date = self._extract_due_date(line)
            priority = self._extract_priority(line)

            # Clean the task description
            task = re.sub(r"\s*\([^)]*\)\s*$", "", line)  # Trailing parentheses
            task = re.sub(r"\s*-\s*\w+\s*$", "", task)  # Trailing "- Name"
            task = task.strip()

            if len(task) < 5 or _is_garbage_line(task):
                continue

            action_items.append(
                {
                    "task": task,
                    "owner": inline_owner or current_owner,
                    "due_date": due_date,
                    "priority": priority,
                }
            )

        return action_items

    @staticmethod
    def _looks_like_owner_header(line: str) -> bool:
        """True if the line looks like a standalone name acting as a sub-header."""
        stripped = line.strip().rstrip(":")
        if not stripped or len(stripped) > 40:
            return False
        if any(ch.isdigit() for ch in stripped):
            return False
        words = stripped.split()
        if not 1 <= len(words) <= 3:
            return False
        # Every word must start with uppercase (First Last style).
        if not all(word[:1].isupper() and word[1:].islower() for word in words if word):
            return False
        # Reject obvious task verbs masquerading as names.
        verb_starts = {"Review", "Send", "Add", "Complete", "Schedule", "Draft", "Email", "Follow"}
        if words[0] in verb_starts:
            return False
        return True

    def _extract_participants(self, body: str) -> List[str]:
        """Extract meeting participants."""
        participants = []

        # Look for participants section
        pattern = r"participants?[:\s]*(.+?)(?=\n\n[A-Z]|\Z)"
        match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)

        if match:
            content = match.group(1)
            # Split by commas, semicolons, or newlines
            names = re.split(r"[,;\n]", content)
            participants = [
                name.strip() for name in names if name.strip() and len(name.strip()) > 2
            ]

        return participants

    def _extract_key_points(self, body: str) -> List[str]:
        """Extract key discussion points."""
        key_points = []

        section_patterns = [
            r"key points?[:\s]*(.+?)(?=\n\n[A-Z]|\Z)",
            r"highlights?[:\s]*(.+?)(?=\n\n[A-Z]|\Z)",
            r"main topics?[:\s]*(.+?)(?=\n\n[A-Z]|\Z)",
        ]

        content = ""
        for pattern in section_patterns:
            match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1)
                break

        if content:
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:
                    # Remove bullet points
                    line = re.sub(r"^[-•*\d.)\]]\s*", "", line)
                    if _is_garbage_line(line):
                        continue
                    key_points.append(line)

        return key_points

    def _extract_decisions(self, body: str) -> List[str]:
        """Extract decisions made during the meeting."""
        decisions = []

        pattern = r"decisions?[:\s]*(.+?)(?=\n\n[A-Z]|\Z)"
        match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)

        if match:
            content = match.group(1)
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:
                    line = re.sub(r"^[-•*\d.)\]]\s*", "", line)
                    if _is_garbage_line(line):
                        continue
                    decisions.append(line)

        return decisions

    def _extract_questions(self, body: str) -> List[str]:
        """Extract questions or open items."""
        questions = []

        pattern = r"(?:questions?|open items?)[:\s]*(.+?)(?=\n\n[A-Z]|\Z)"
        match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)

        if match:
            content = match.group(1)
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if line and len(line) > 5:
                    line = re.sub(r"^[-•*\d.)\]]\s*", "", line)
                    if _is_garbage_line(line):
                        continue
                    questions.append(line)

        return questions

    def _extract_owner(self, text: str) -> Optional[str]:
        """Extract owner/assignee from action item text."""
        # Look for patterns like (John), - John, @John
        patterns = [
            r"\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\)",
            r"-\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$",
            r"@([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return None

    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from action item text."""
        # Look for date patterns
        date_patterns = [
            r"by\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"due\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"(\d{1,2}/\d{1,2}/\d{2,4})",
            r"by\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"by\s+(next\s+week|this\s+week|tomorrow)",
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_priority(self, text: str) -> str:
        """Determine priority based on keywords."""
        text_lower = text.lower()

        high_keywords = ["urgent", "asap", "critical", "immediately", "high priority"]
        low_keywords = ["when possible", "eventually", "low priority", "nice to have"]

        if any(keyword in text_lower for keyword in high_keywords):
            return "high"
        elif any(keyword in text_lower for keyword in low_keywords):
            return "low"

        return "medium"

    def _extract_date(self, body: str) -> Optional[str]:
        """Extract meeting date from body."""
        # Look for date patterns
        date_patterns = [
            r"Date:\s*(.+?)(?:\n|$)",
            r"(?:Meeting\s+)?(?:on|at)\s+(\w+,\s+\w+\s+\d{1,2},\s+\d{4})",
        ]

        for pattern in date_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None
