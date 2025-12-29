#!/bin/bash
# Script per riallineare e pushare su GitHub

# Vai nella cartella del progetto (relativa allo script stesso)
cd "$(dirname "$0")" || exit 1

# Determina il branch corrente
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Riallinea con il remoto
git pull origin "$CURRENT_BRANCH" --rebase

# Aggiunge tutte le modifiche (nuovi, modificati, eliminati)
git add --all

# Commit fisso "fix"
git commit -m "fix" || echo "Nessuna modifica da commitare"

# Push sul branch corrente
echo "Push su branch: $CURRENT_BRANCH"
git push origin "$CURRENT_BRANCH"

# Deploy automatico su Fly.io
echo "Avvio deploy su Fly.io..."
fly deploy