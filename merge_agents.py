# ABOUTME: Reads agents from agents.json and registers new agents via the openclaw CLI.
# ABOUTME: Also creates workspace/agentDir folders and copies SOUL.md for each new agent.

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

OPENCLAW_BASE = Path("/Users/openclaw")
OPENCLAW_CLI = "/opt/homebrew/bin/openclaw"
OPENCLAW_CONFIG_DEFAULT = "/Users/openclaw/.openclaw/openclaw.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def provision_agent_fs(agent: dict, agents_source_dir: Path) -> None:
    """Copy SOUL.md into the agent workspace (workspace dir is created by the CLI)."""
    category = agent.get("category", "")
    name = agent.get("name", agent.get("id", ""))
    workspace = agent.get("workspace")

    if not workspace:
        print(
            f"  Warning: agent '{name}' missing workspace — skipping SOUL.md copy.",
            file=sys.stderr,
        )
        return

    # SOUL.md lives at agents/{category}/{name_without_category_prefix}/SOUL.md
    category_prefix = f"{category}-"
    name_suffix = name.removeprefix(category_prefix) if category else name
    soul_src = agents_source_dir / category / name_suffix / "SOUL.md"

    if not soul_src.exists():
        print(f"  Warning: SOUL.md not found at {soul_src} — skipping copy.", file=sys.stderr)
        return

    soul_dst = Path(workspace) / "SOUL.md"
    shutil.copy2(soul_src, soul_dst)
    print(f"  Copied SOUL.md:     {soul_src} -> {soul_dst}")


def register_agent(agent_id: str) -> bool:
    """Call the openclaw CLI to register the agent. Returns True on success."""
    cmd = [OPENCLAW_CLI, "agents", "add", agent_id]
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  Error: openclaw exited with code {result.returncode}", file=sys.stderr)
        return False
    return True


def fetch_live_agents():
    """Call 'openclaw agents list' and return the parsed agent list, or None on failure."""
    cmd = [OPENCLAW_CLI, "agents", "list"]
    print(f"\nRunning: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: openclaw agents list failed (code {result.returncode})", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return None

    raw = result.stdout.strip()
    try:
        parsed = json.loads(raw)
        # Accept either a bare list or {"agents": [...]}
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return parsed.get("agents", list(parsed.values()))
    except json.JSONDecodeError:
        pass

    # Fall back: treat each non-empty line as an agent id
    return [{"id": line.strip()} for line in raw.splitlines() if line.strip()]


def _flatten(value: object, prefix: str = "") -> dict:
    """Recursively flatten a nested dict into dot-notation keys."""
    items = {}
    if isinstance(value, dict):
        for k, v in value.items():
            items.update(_flatten(v, f"{prefix}.{k}" if prefix else k))
    else:
        items[prefix] = value
    return items


def compare_and_report(incoming_agents, live_agents):
    """Compare agents.json entries against the live CLI list and print differences."""
    print("\n--- Agent comparison (agents.json vs openclaw agents list) ---")

    live_by_id = {a["id"]: a for a in live_agents if "id" in a}
    source_by_id = {a["id"]: a for a in incoming_agents if "id" in a}

    # Agents in agents.json but missing from the live list
    missing = [aid for aid in source_by_id if aid not in live_by_id]
    if missing:
        print(f"\n  MISSING from live (in agents.json but not in openclaw list):")
        for aid in missing:
            print(f"    - {aid}")

    # Agents in the live list but not in agents.json
    extra = [aid for aid in live_by_id if aid not in source_by_id]
    if extra:
        print(f"\n  EXTRA in live (in openclaw list but not in agents.json):")
        for aid in extra:
            print(f"    + {aid}")

    # Field-level diff for agents present in both
    common = [aid for aid in source_by_id if aid in live_by_id]
    for aid in common:
        src_flat = _flatten(source_by_id[aid])
        live_flat = _flatten(live_by_id[aid])
        all_keys = src_flat.keys() | live_flat.keys()
        diffs = []
        for key in sorted(all_keys):
            src_val = src_flat.get(key)
            live_val = live_flat.get(key)
            if src_val != live_val:
                diffs.append((key, src_val, live_val))
        if diffs:
            print(f"\n  DIFF for agent '{aid}':")
            for key, src_val, live_val in diffs:
                if key not in src_flat:
                    print(f"    {key}: (not in agents.json) | live: {live_val!r}")
                elif key not in live_flat:
                    print(f"    {key}: agents.json: {src_val!r} | (not in live)")
                else:
                    print(f"    {key}: agents.json: {src_val!r} | live: {live_val!r}")

    if not missing and not extra and not any(True for aid in common):
        print("  All agents match.")
    elif not missing and not extra and all(
        _flatten(source_by_id[aid]) == _flatten(live_by_id[aid]) for aid in common
    ):
        print("\n  All present agents are identical.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register agents from agents.json via the openclaw CLI."
    )
    parser.add_argument(
        "agents_file",
        nargs="?",
        default="agents.json",
        help="Path to agents.json (default: agents.json)",
    )
    parser.add_argument(
        "-i", "--input",
        default=OPENCLAW_CONFIG_DEFAULT,
        help=f"Path to openclaw.json to read existing agents from (default: {OPENCLAW_CONFIG_DEFAULT})",
    )
    args = parser.parse_args()

    if not OPENCLAW_BASE.exists():
        print(f"Error: base path {OPENCLAW_BASE} does not exist.", file=sys.stderr)
        sys.exit(1)

    agents_path = Path(args.agents_file)
    openclaw_path = Path(args.input)

    # agents source dir sits next to the agents.json file
    agents_source_dir = agents_path.parent / "agents"

    if not agents_path.exists():
        print(f"Error: agents file not found: {agents_path}", file=sys.stderr)
        sys.exit(1)

    if not openclaw_path.exists():
        print(f"Error: openclaw config not found: {openclaw_path}", file=sys.stderr)
        sys.exit(1)

    agents_data = load_json(agents_path)
    openclaw_data = load_json(openclaw_path)

    incoming_agents = agents_data.get("agents", [])
    existing_list = openclaw_data.get("agents", {}).get("list", [])
    existing_ids = {entry["id"] for entry in existing_list if "id" in entry}

    added = 0
    skipped = 0
    errors = 0
    for agent in incoming_agents:
        agent_id = agent.get("id")
        if not agent_id:
            print(f"Warning: skipping agent with no id: {agent}", file=sys.stderr)
            skipped += 1
            continue
        if agent_id in existing_ids:
            print(f"Skipping existing agent: {agent_id}")
            skipped += 1
            continue

        print(f"Adding agent: {agent_id}")
        if register_agent(agent_id):
            provision_agent_fs(agent, agents_source_dir)
            added += 1
        else:
            errors += 1

    print(f"Done. Added {added} agent(s), skipped {skipped}, errors {errors}.")

    live_agents = fetch_live_agents()
    if live_agents is not None:
        compare_and_report(incoming_agents, live_agents)

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
