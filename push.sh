#!/bin/bash
# Script per riallineare e pushare su GitHub in modo sicuro

# Vai nella cartella del progetto (relativa allo script stesso)
cd "$(dirname "$0")" || exit 1

# Determina il branch corrente
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "➡️  Pull dal remoto (merge, no rebase)..."
git pull origin "$CURRENT_BRANCH" --no-rebase

# Aggiunge tutte le modifiche (nuovi, modificati, eliminati)
git add --all -- :!backup_SQL/*

# Commit fisso "fix"
git commit -m "fix" 2>/dev/null || echo "ℹ️  Nessuna modifica da commitare"

# Push sul branch corrente
echo "➡️  Push su branch: $CURRENT_BRANCH"
git push origin "$CURRENT_BRANCH"

# Deploy automatico su Fly.io
echo "🚀 Avvio deploy su Fly.io..."
fly deploy
