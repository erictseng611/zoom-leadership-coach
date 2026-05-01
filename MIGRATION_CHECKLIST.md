# Migration Checklist: Manual Todo Approval

## For Existing Users

If you're already using zoom-leadership-coach and upgrading to the manual approval version, follow this checklist:

### ✅ Pre-Migration Steps

- [ ] **Backup current data**
  ```bash
  cp -r data/ data_backup_$(date +%Y%m%d)/
  ```

- [ ] **Note current configuration**
  - Review your `config/config.yaml` settings
  - Document any customizations you've made

- [ ] **Check scheduled tasks**
  - macOS: `launchctl list | grep zoom-leadership-coach`
  - Linux: `crontab -l | grep zoom-leadership-coach`
  - Windows: Check Task Scheduler for "ZoomLeadershipCoach"

### ✅ Migration Steps

- [ ] **Pull latest code**
  ```bash
  cd /path/to/zoom-leadership-coach
  git pull  # if using git
  # or download latest version
  ```

- [ ] **Install dependencies** (if needed)
  ```bash
  source venv/bin/activate
  pip install -r requirements.txt --upgrade
  ```

- [ ] **Test interactive mode**
  ```bash
  # Try with a single test meeting
  python -m src.main --limit 1
  ```

- [ ] **Update scheduled tasks** (if using automation)
  
  **For automated runs**, add `--auto-approve` flag:
  
  **macOS (launchd)**:
  ```bash
  # Edit plist file
  nano ~/Library/LaunchAgents/com.user.zoom-leadership-coach.plist
  
  # Add --auto-approve to ProgramArguments:
  <array>
      <string>/path/to/python</string>
      <string>-m</string>
      <string>src.main</string>
      <string>--auto-approve</string>  <!-- ADD THIS LINE -->
  </array>
  
  # Reload
  launchctl unload ~/Library/LaunchAgents/com.user.zoom-leadership-coach.plist
  launchctl load ~/Library/LaunchAgents/com.user.zoom-leadership-coach.plist
  ```
  
  **Linux (cron)**:
  ```bash
  crontab -e
  
  # Change from:
  0 20 * * * cd /path && python -m src.main
  
  # To:
  0 20 * * * cd /path && python -m src.main --auto-approve
  ```
  
  **Windows (Task Scheduler)**:
  1. Open Task Scheduler
  2. Find "ZoomLeadershipCoach" task
  3. Edit Action
  4. Add `--auto-approve` to arguments

### ✅ Post-Migration Testing

- [ ] **Test interactive workflow**
  - Run without flags: `python -m src.main`
  - Verify review screen appears
  - Test editing a todo
  - Test changing time
  - Test skipping an item
  - Test accepting an item

- [ ] **Test auto-approve mode**
  - Run with flag: `python -m src.main --auto-approve`
  - Verify todos are created automatically
  - Check calendar for new events

- [ ] **Verify calendar creation**
  - Open Google Calendar
  - Check that approved todos appear correctly
  - Verify time slots, descriptions, priorities

- [ ] **Test with different scenarios**
  - Multiple action items (3+)
  - High/medium/low priority items
  - Custom time entry
  - Editing all fields

### ✅ Configuration Review

- [ ] **Review work hours** (`config/config.yaml`)
  ```yaml
  scheduling:
    work_hours_start: "09:00"
    work_hours_end: "17:00"
  ```

- [ ] **Review preferred focus times**
  ```yaml
  scheduling:
    preferred_focus_times:
      - "09:00-11:00"
      - "14:00-16:00"
  ```

- [ ] **Review todo filters** (if using personal keyword filtering)
  ```yaml
  todos:
    skip_personal: true
    personal_keywords:
      - "personal"
      - "family"
  ```

### ✅ Documentation Review

- [ ] **Read new documentation**
  - [ ] `MANUAL_TODO_APPROVAL.md` - Detailed feature guide
  - [ ] `QUICK_START_APPROVAL.md` - Quick reference
  - [ ] `WORKFLOW_DIAGRAM.md` - Visual workflow
  - [ ] Updated `README.md` - Main documentation

### ✅ Optional: Update Usage Patterns

Decide which mode works best for your workflow:

**Option 1: Interactive by default**
- Use for manual runs when you have time to review
- Command: `python -m src.main`
- Best for: Ad-hoc processing, careful review needed

**Option 2: Auto-approve for scheduled runs**
- Use for automated daily processing
- Command: `python -m src.main --auto-approve`
- Best for: End-of-day automation, high volume

**Option 3: Hybrid approach**
- Scheduled runs: Auto-approve during off-hours
- Manual runs: Interactive during work hours
- Example schedule:
  ```bash
  # Auto-approve at night
  0 22 * * * cd /path && python -m src.main --auto-approve
  
  # Remind to review manually during day
  0 16 * * * echo "Review today's meetings: python -m src.main"
  ```

## Rollback Plan

If you need to revert to automatic behavior:

### Temporary Rollback
Always use `--auto-approve` flag:
```bash
python -m src.main --auto-approve
```

### Permanent Rollback
1. Checkout previous version
2. Or modify `src/main.py` to default `auto_approve=True`

## Common Issues

### Issue: "No module named 'rich'"
**Solution**: Update dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Issue: Approval prompts not showing
**Solution**: Check that you're NOT using `--auto-approve` flag
```bash
# Should show prompts
python -m src.main

# Should NOT show prompts
python -m src.main --auto-approve
```

### Issue: Scheduled task still auto-creating todos
**Solution**: Add `--auto-approve` flag to scheduled command

### Issue: Can't enter custom time
**Solution**: Use exact format `YYYY-MM-DD HH:MM`
```
Example: 2026-05-01 14:30
```

## Getting Help

- **Documentation**: See `MANUAL_TODO_APPROVAL.md`
- **Quick Reference**: See `QUICK_START_APPROVAL.md`
- **Workflow Diagrams**: See `WORKFLOW_DIAGRAM.md`
- **Issues**: Check GitHub issues or create new one

## Success Criteria

✅ You've successfully migrated when:

- [ ] Interactive mode works for manual runs
- [ ] Auto-approve mode works for scheduled runs
- [ ] All approved todos appear in Google Calendar
- [ ] You can edit todo details before approval
- [ ] You can change scheduled times
- [ ] You can skip unwanted items
- [ ] Coaching reports still generate correctly
- [ ] No errors in logs

## Timeline Recommendation

- **Day 1**: Pull updates, test with `--limit 1`
- **Day 2-3**: Use interactively for a few meetings
- **Day 4-5**: Update scheduled tasks if satisfied
- **Week 2**: Monitor and adjust workflow as needed

## Questions to Consider

Before finalizing your migration:

1. **How often will I review todos manually?**
   - Daily → Interactive mode
   - Weekly/never → Auto-approve mode

2. **Do I trust the AI's action item extraction?**
   - Yes → Auto-approve
   - No → Interactive review

3. **How many action items per day?**
   - 1-5 → Interactive is fine
   - 10+ → Consider auto-approve

4. **Do I have calendar conflicts often?**
   - Yes → Interactive to adjust times
   - No → Auto-approve with smart scheduling

5. **Do I want to see coaching insights live?**
   - Yes → Interactive mode
   - No → Auto-approve, read reports later
