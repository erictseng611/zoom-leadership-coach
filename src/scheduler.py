"""Scheduling logic for daily automated runs."""

import logging
import platform
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("zoom_coach")


class SchedulerSetup:
    """Setup automated scheduling for the application."""

    def __init__(self, run_time: str = "20:00"):
        """
        Initialize scheduler.

        Args:
            run_time: Time to run daily (HH:MM format)
        """
        self.run_time = run_time
        self.platform = platform.system()
        self.script_path = Path(__file__).parent.parent / "src" / "main.py"

    def setup_daily_schedule(self) -> bool:
        """Setup daily scheduled runs based on platform."""
        try:
            if self.platform == "Darwin":  # macOS
                return self._setup_launchd()
            elif self.platform == "Linux":
                return self._setup_cron()
            elif self.platform == "Windows":
                return self._setup_windows_task()
            else:
                logger.error(f"Unsupported platform: {self.platform}")
                return False
        except Exception as e:
            logger.error(f"Error setting up schedule: {e}")
            return False

    def _setup_launchd(self) -> bool:
        """Setup macOS launchd for daily runs."""
        logger.info("Setting up macOS launchd...")

        hour, minute = self.run_time.split(":")

        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.zoom-leadership-coach</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>src.main</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{self.script_path.parent.parent}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{self.script_path.parent.parent}/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>{self.script_path.parent.parent}/logs/launchd.error.log</string>
</dict>
</plist>
"""

        plist_path = Path.home() / "Library" / "LaunchAgents" / "com.user.zoom-leadership-coach.plist"
        plist_path.parent.mkdir(parents=True, exist_ok=True)

        with open(plist_path, "w") as f:
            f.write(plist_content)

        # Load the launch agent
        subprocess.run(["launchctl", "load", str(plist_path)], check=True)

        logger.info(f"✓ Scheduled daily runs at {self.run_time} via launchd")
        logger.info(f"  Plist file: {plist_path}")
        logger.info(f"  To disable: launchctl unload {plist_path}")

        return True

    def _setup_cron(self) -> bool:
        """Setup Linux cron for daily runs."""
        logger.info("Setting up cron job...")

        hour, minute = self.run_time.split(":")

        # Get existing crontab
        try:
            result = subprocess.run(
                ["crontab", "-l"], capture_output=True, text=True, check=False
            )
            existing_crontab = result.stdout if result.returncode == 0 else ""
        except FileNotFoundError:
            existing_crontab = ""

        # Check if job already exists
        job_marker = "# zoom-leadership-coach"
        if job_marker in existing_crontab:
            logger.info("Cron job already exists")
            return True

        # Add new cron job
        new_job = f"{minute} {hour} * * * cd {self.script_path.parent.parent} && {sys.executable} -m src.main {job_marker}\n"

        new_crontab = existing_crontab + new_job

        # Install new crontab
        process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)

        logger.info(f"✓ Scheduled daily runs at {self.run_time} via cron")
        logger.info("  To view: crontab -l")
        logger.info("  To edit: crontab -e")

        return True

    def _setup_windows_task(self) -> bool:
        """Setup Windows Task Scheduler for daily runs."""
        logger.info("Setting up Windows Task Scheduler...")

        hour, minute = self.run_time.split(":")

        task_name = "ZoomLeadershipCoach"

        # Create task using schtasks
        command = [
            "schtasks",
            "/Create",
            "/SC", "DAILY",
            "/TN", task_name,
            "/TR", f'"{sys.executable}" -m src.main',
            "/ST", self.run_time,
            "/F",  # Force create (overwrite if exists)
        ]

        subprocess.run(command, check=True, cwd=str(self.script_path.parent.parent))

        logger.info(f"✓ Scheduled daily runs at {self.run_time} via Task Scheduler")
        logger.info(f"  Task name: {task_name}")
        logger.info(f"  To view: schtasks /Query /TN {task_name}")
        logger.info(f"  To delete: schtasks /Delete /TN {task_name}")

        return True

    def remove_schedule(self) -> bool:
        """Remove scheduled daily runs."""
        try:
            if self.platform == "Darwin":
                plist_path = (
                    Path.home()
                    / "Library"
                    / "LaunchAgents"
                    / "com.user.zoom-leadership-coach.plist"
                )
                if plist_path.exists():
                    subprocess.run(["launchctl", "unload", str(plist_path)], check=True)
                    plist_path.unlink()
                    logger.info("✓ Removed launchd schedule")
                    return True

            elif self.platform == "Linux":
                # Remove cron job
                result = subprocess.run(
                    ["crontab", "-l"], capture_output=True, text=True, check=False
                )
                if result.returncode == 0:
                    lines = result.stdout.split("\n")
                    new_lines = [
                        line for line in lines if "zoom-leadership-coach" not in line
                    ]
                    new_crontab = "\n".join(new_lines)

                    process = subprocess.Popen(
                        ["crontab", "-"], stdin=subprocess.PIPE, text=True
                    )
                    process.communicate(input=new_crontab)
                    logger.info("✓ Removed cron job")
                    return True

            elif self.platform == "Windows":
                subprocess.run(
                    ["schtasks", "/Delete", "/TN", "ZoomLeadershipCoach", "/F"],
                    check=True,
                )
                logger.info("✓ Removed Windows task")
                return True

        except Exception as e:
            logger.error(f"Error removing schedule: {e}")
            return False

        return False
