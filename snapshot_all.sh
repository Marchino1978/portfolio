#!/bin/bash
# snapshot_all.sh - genera un file .md per ogni cartella (txt/_<cartella>.md)
# Esclude: txt/, .git/, node_modules, data, public, .venv

mkdir -p txt

dump_folder() {
  local folder="$1"
  local output="txt/_$2.md"
  : > "$output"

  for file in "$folder"/*; do
    [ -f "$file" ] || continue

    echo "# $file" >> "$output"
    echo "----------------------------------------" >> "$output"

    cat "$file" >> "$output"

    echo "" >> "$output"
    echo "" >> "$output"
  done
}

# Dump della root
dump_folder "." "root"

# Dump di ogni sottocartella, esclusioni aggiornate per Python
for dir in */; do
  [ -d "$dir" ] || continue
  foldername=$(basename "$dir")
  case "$foldername" in
    txt|.git|node_modules|data|public|.venv|__pycache__) continue ;;
    *) dump_folder "$dir" "$foldername" ;;
  esac
done

echo "Snapshot .md generati in txt"