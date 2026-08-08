#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/publish_to_github.sh <github-owner> <repo-name> [public|private]
# Example:
#   ./scripts/publish_to_github.sh domi fuehrer-der-unschluessigen public

OWNER="${1:?GitHub owner/user fehlt}"
REPO="${2:?Repo-Name fehlt}"
VISIBILITY="${3:-public}"

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git fehlt" >&2
  exit 1
fi

if ! git config --global user.name >/dev/null || ! git config --global user.email >/dev/null; then
  echo "ERROR: git user.name/user.email sind nicht gesetzt." >&2
  echo "Setze z.B.:" >&2
  echo "  git config --global user.name 'Dein Name'" >&2
  echo "  git config --global user.email 'deine-mail@example.com'" >&2
  exit 1
fi

if [ ! -d .git ]; then
  git init
  git branch -M main
fi

git add .
if git diff --cached --quiet; then
  echo "Keine Änderungen zu committen."
else
  git commit -m "Initial publishable knowledge base"
fi

REMOTE="https://github.com/${OWNER}/${REPO}.git"

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  if ! gh repo view "${OWNER}/${REPO}" >/dev/null 2>&1; then
    gh repo create "${OWNER}/${REPO}" "--${VISIBILITY}" --description "Deutsches Quellen- und Wissensnetz zu Maimonides' Führer der Unschlüssigen" --source . --remote origin --push
  else
    git remote get-url origin >/dev/null 2>&1 || git remote add origin "$REMOTE"
    git push -u origin main
  fi
  gh api -X POST "/repos/${OWNER}/${REPO}/pages" -f source='{"branch":"main","path":"/"}' >/dev/null 2>&1 || true
  echo "Fertig. Repo: https://github.com/${OWNER}/${REPO}"
  echo "Pages nach dem ersten Workflow-Lauf: https://${OWNER}.github.io/${REPO}/"
else
  echo "gh ist nicht authentifiziert. Erstelle das Repo zuerst auf GitHub oder authentifiziere gh." >&2
  echo "Dann ausführen:" >&2
  echo "  git remote add origin ${REMOTE}" >&2
  echo "  git push -u origin main" >&2
  exit 2
fi
