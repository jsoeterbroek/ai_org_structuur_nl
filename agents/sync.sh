#!/usr/bin/env bash
set -euo pipefail

AGENTS_JSON="/Users/jsoeterbroek/Development/ai_org_structuur_nl/agents.json"
AGENTS_DIR="/Users/jsoeterbroek/Development/ai_org_structuur_nl/agents"

# Build list of "agent_id|department|workspace" from agents.json
mapfile -t AGENT_ENTRIES < <(python3 -c "
import json, sys
data = json.load(open('${AGENTS_JSON}'))
for agent in data['agents']:
    agent_id = agent['id']
    dept = agent.get('category', agent_id.split('-')[0])
    workspace = agent['workspace'].replace('~', '${HOME}')
    print(f'{agent_id}|{dept}|{workspace}')
")

echo "Found ${#AGENT_ENTRIES[@]} agents."

for entry in "${AGENT_ENTRIES[@]}"; do
    IFS='|' read -r agent_id dept workspace <<< "${entry}"
    src_dir="${AGENTS_DIR}/${dept}/${agent_id}"

    echo ""
    echo "--- Agent: ${agent_id} (${dept}) -> ${workspace}"

    if [[ ! -d "${src_dir}" ]]; then
        echo "  SKIP: source directory ${src_dir} not found"
        continue
    fi

    mkdir -p "${workspace}"

    for src_file in "${src_dir}"/*.md; do
        [[ -f "${src_file}" ]] || continue
        filename=$(basename "${src_file}")
        dest_file="${workspace}/${filename}"

        if [[ -f "${dest_file}" ]] && [[ "${dest_file}" -nt "${src_file}" ]]; then
            echo "  Skipping, file ${filename} is newer in workdir"
        else
            echo "  Copying ${filename}"
            cp "${src_file}" "${dest_file}"
        fi
    done
done

echo ""
echo "Sync complete."
