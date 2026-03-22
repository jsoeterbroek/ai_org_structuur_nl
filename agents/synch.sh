#!/usr/bin/bash

ROOT=/home/jsoeterbroek/.openclaw
SHARED=/home/jsoeterbroek/.openclaw/workspace-shared

Backup_of_internal_field_separator=$IFS
IFS=,

DEPTS="corporate,business,finance,it,legal,marketing,security"
for DEPT in ${DEPTS}; do
  DEPTDIR="${SHARED}/${DEPT}"
  FROM_DIR="${DEPT}"
  TO_DIR="${DEPTDIR}"
  WORKFLOW_FROM="${FROM_DIR}/WORKFLOW.md"
  WORKFLOW_TO="${TO_DIR}/WORKFLOW.md"
  echo "INFO: ---------"
  mkdir -p "${TO_DIR}"
  echo "INFO: sync workflow ${WORKFLOW_FROM} to ${WORKFLOW_TO} (skip files newer on receiver)"
  rsync -au ${WORKFLOW_FROM} ${WORKFLOW_TO}
done

IFS=$Backup_of_internal_field_separator

# Call the CLI once and cache the result; output tab-separated "name\tworkspace" pairs
AGENTS_JSON=$(openclaw agents list --json)

while IFS=$'\t' read -r EMPLOYEE WORKSPACE; do
  # derive department from agent name prefix (e.g. "finance-bookkeeper" -> "finance")
  DEPARTMENT="${EMPLOYEE%%-*}"
  WORKFLOW_FROM="${DEPARTMENT}/${EMPLOYEE}/*.md"
  WORKFLOW_TO="${WORKSPACE}"

  if [ "${EMPLOYEE}" != "main" ]; then
    echo "INFO: ---------"
    echo "INFO: sync workflow ${WORKFLOW_FROM} to ${WORKFLOW_TO} (skip files newer on receiver)"
    rsync -au ${WORKFLOW_FROM} ${WORKFLOW_TO}
  fi

done < <(echo "${AGENTS_JSON}" | python3 -c "
import sys, json
for emp in json.load(sys.stdin):
    print(emp.get('name', emp['id']) + '\t' + emp['workspace'])
")
