#!/bin/bash

mkdir -p txt

dump_folder() {
  local folder="$1"
  local output="txt/_$2.md"
  : > "$output"

  for file in "$folder"/*; do
    [ -f "$file" ] || continue

    local nome_file="${file##*/}"

    [[ "$nome_file" == *.zip ]] && continue
    [[ "$nome_file" == "ETF.ino" ]] && continue
    [[ "$nome_file" == "frame.stl" ]] && continue
    [[ "$nome_file" == "README_FIRST.txt" ]] && continue
    [[ "$nome_file" == "README.md" ]] && continue
    [[ "$nome_file" == "TODO.md" ]] && continue

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
  foldername="${dir%/}"
  
  case "$foldername" in
    txt|.git|node_modules|data|public|old|gallery|img|backup_SQL|.venv|__pycache__) continue ;;
    *) dump_folder "$dir" "$foldername" ;;
  esac
done

tree -a -F -I '*.zip|node_modules|.git|txt' --dirsfirst > project-tree.txt

echo "" >> project-tree.txt
echo "*** NOTE: some local files listed in this tree have been intentionally omitted from the repository ***" >> project-tree.txt

echo "Progetto mappato in project-tree.txt"
echo "Snapshot .md generati in txt"
