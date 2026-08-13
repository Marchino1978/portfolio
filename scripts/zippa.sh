#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

REPO_NAME=$(basename "$ROOT_DIR")
DATA_OGGI=$(date +%Y-%m-%d)
ZIP_NAME="${REPO_NAME}_backup_${DATA_OGGI}.zip"

echo "Avvio backup totale della repo: $REPO_NAME"
echo "Root del progetto individuata: $ROOT_DIR"

if ! command -v zip &> /dev/null; then
    echo "Errore: il comando 'zip' non è installato."
    echo "Installa con: sudo apt install zip"
    exit 1
fi

echo "Creazione dello zip (inclusi file nascosti, .env e .git)..."

zip -ry "$ZIP_NAME" . -x "*.zip"

echo "Backup completato con successo!"
echo "File creato nella root: $ROOT_DIR/$ZIP_NAME"
