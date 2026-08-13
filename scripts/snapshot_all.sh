#!/bin/bash

mkdir -p txt

dump_folder() {
  local folder="$1"
  local output="txt/_$2.md"
  : > "$output"

  for file in "$folder"/*; do
    [ -f "$file" ] || continue

    [[ "$(basename "$file")" == "ETF.ino" ]] && continue
    [[ "$(basename "$file")" == "frame.stl" ]] && continue
    [[ "$(basename "$file")" == "frame.gif" ]] && continue
    [[ "$(basename "$file")" == "frame.png" ]] && continue
    [[ "$(basename "$file")" == "README_FIRST.txt" ]] && continue
    [[ "$(basename "$file")" == "README.md" ]] && continue
    [[ "$(basename "$file")" == "TODO.md" ]] && continue

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