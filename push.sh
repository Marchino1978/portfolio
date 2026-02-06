#!/bin/bash

cd "$(dirname "$0")" || exit 1

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "➡️  Pull dal remoto (merge, no rebase)..."
git pull origin "$CURRENT_BRANCH" --no-rebase

git add --all -- :!backup_SQL/*

git commit -m "fix" 2>/dev/null || echo "ℹ️  Nessuna modifica da commitare"

echo "➡️  Push su branch: $CURRENT_BRANCH"
git push origin "$CURRENT_BRANCH"

echo "🚀 Avvio deploy su Fly.io..."
fly deploy
