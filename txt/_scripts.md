# scripts//push.sh
----------------------------------------
#!/bin/bash

cd "$(dirname "$0")" || exit 1

cd ..

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "➡️  Pull dal remoto (merge, no rebase)..."
git pull origin "$CURRENT_BRANCH" --no-rebase

git add --all -- :!backup_SQL/*

git commit -m "fix" 2>/dev/null || echo "ℹ️  Nessuna modifica da commitare"

echo "➡️  Push su branch: $CURRENT_BRANCH"
git push origin "$CURRENT_BRANCH"

echo "🚀 Avvio deploy su Fly.io..."
fly deploy


# scripts//snapshot_all.sh
----------------------------------------
#!/bin/bash

mkdir -p txt

dump_folder() {
  local folder="$1"
  local output="txt/_$2.md"
  : > "$output"

  for file in "$folder"/*; do
    [ -f "$file" ] || continue

    [[ "$(basename "$file")" == "ETF.ino" ]] && continue
    [[ "$(basename "$file")" == "ETF.example.ino" ]] && continue
    [[ "$(basename "$file")" == "config.h" ]] && continue
    [[ "$(basename "$file")" == "case.stl" ]] && continue
    [[ "$(basename "$file")" == "case.gif" ]] && continue
    [[ "$(basename "$file")" == "case.png" ]] && continue

    echo "# $file" >> "$output"
    echo "----------------------------------------" >> "$output"

    cat "$file" >> "$output"

    echo "" >> "$output"
    echo "" >> "$output"
  done
}

dump_folder "." "root"

for dir in */; do
  [ -d "$dir" ] || continue
  foldername=$(basename "$dir")
  case "$foldername" in
    txt|.git|node_modules|data|public|old|gallery|img|backup_SQL|.venv|__pycache__) continue ;;
    *) dump_folder "$dir" "$foldername" ;;
  esac
done

tree -a -F -I 'node_modules|.git|txt' --dirsfirst > project-tree.txt

echo "" >> project-tree.txt
echo "*** NOTE: some local files listed in this tree have been intentionally omitted from the repository ***" >> project-tree.txt

echo "Progetto mappato in project-tree.txt"
echo "Snapshot .md generati in txt"

