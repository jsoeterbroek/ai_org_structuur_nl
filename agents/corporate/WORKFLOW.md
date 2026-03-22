# WORKFLOW.md — Corporate

**Version:** 1.1
**Date:** 2026-03-20
**Supersedes:** workflow-corporate-policy-v1.0.md

## Current Policy

This file is superseded by the comprehensive policy document:

**`workflow-corporate-policy-v1.1.md`** — contains all policy directives, templates, scripts, and implementation details.

## Quick Reference

| Item | Location |
|------|----------|
| Full policy | `workflow-corporate-policy-v1.1.md` |
| Day Summary | `workspace-shared/<DEPT>/activity_reports/YY-MM-DD-<AGENT>.md` |
| Department workflows | `workspace-shared/<DEPT>/WORKFLOW.md` |

## Key Directives (v1.1)

- **Session Start Protocol** — Run mc inbox + mc list + mc checkin before any work
- **Heartbeat** — mc checkin + inbox every 30 min during business hours
- **Day Summary** — Mandatory at 18:00 in your department's activity_reports folder
- **Task Flow** — mc add → mc claim → mc start → mc done
- **Approval Flow** — Cross-agent tasks require approval before execution

## mc Quick Reference

```bash
export PATH="$PATH:/home/jsoeterbroek/.openclaw/mission-control"
export MC_AGENT=<your-name>

# Start of day
MC_AGENT=<your-name> mc inbox --unread
MC_AGENT=<your-name> mc list --status pending

# Tasks
mc add "Task" --for <agent>
mc claim <id>
mc start <id>
mc done <id> -m "result"

# Communication
mc msg <agent> "message"
mc checkin
mc fleet
mc feed --last 10
```

---

*See: workflow-corporate-policy-v1.1.md for full policy document.*
