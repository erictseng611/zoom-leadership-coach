"""One-off cleanup: remove TODO events this app created in the last N hours.

Matches any event with 'TODO:' in the summary that was CREATED in the lookback
window. Prints candidates and asks for confirmation before deleting.
"""

import argparse
from datetime import datetime, timedelta, timezone

from googleapiclient.errors import HttpError

from .calendar_client import CalendarClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hours",
        type=float,
        default=2.0,
        help="Only delete TODOs created within the last N hours (default: 2)",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Skip the confirmation prompt"
    )
    args = parser.parse_args()

    client = CalendarClient()
    service = client.service

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=args.hours)
    time_min = (now - timedelta(days=1)).isoformat()
    time_max = (now + timedelta(days=60)).isoformat()

    junk = []
    page_token = None
    while True:
        resp = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            maxResults=2500,
            pageToken=page_token,
        ).execute()

        for event in resp.get("items", []):
            summary = event.get("summary", "") or ""
            if "TODO:" not in summary:
                continue
            created_str = event.get("created", "")
            if not created_str:
                continue
            created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            if created >= cutoff:
                junk.append((event["id"], summary, created_str, event.get("start")))

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    if not junk:
        print(f"No TODO events found created in the last {args.hours}h.")
        return

    print(f"Found {len(junk)} TODO event(s) created in the last {args.hours}h.")
    print("Sample (first 10):")
    for event_id, summary, created_str, start in junk[:10]:
        start_time = (start or {}).get("dateTime", "?")
        print(f"  created={created_str} | start={start_time} | {summary[:80]}")
    if len(junk) > 10:
        print(f"  ... and {len(junk) - 10} more")

    if not args.yes:
        confirm = input(f"\nDelete all {len(junk)} events? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    deleted = 0
    failed = 0
    for event_id, summary, _created_str, _start in junk:
        try:
            service.events().delete(calendarId="primary", eventId=event_id).execute()
            deleted += 1
            if deleted % 10 == 0:
                print(f"  deleted {deleted}/{len(junk)}")
        except HttpError as error:
            failed += 1
            print(f"  failed to delete {event_id} ({summary[:40]}): {error}")

    print(f"\nDone. Deleted {deleted}, failed {failed}.")


if __name__ == "__main__":
    main()
