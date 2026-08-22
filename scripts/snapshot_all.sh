#!/bin/bash

mkdir -p txt

dump_folder() {
  local folder="$1"
  local output="txt/_$2.md"
  : > "$output"

  for file in "$folder"/*; do
    [ -f "$file" ] || continue

    local nome_file="${file##*/}"

# ESCLUDE FILE PER ESTENSIONE DALLO SNAPSHOT .md
    [[ "$nome_file" == *.zip ]] && continue

# ESCLUDE FILE SPECIFICI DALLO SNAPSHOT .md
    [[ "$nome_file" == "ETF.ino" ]] && continue
    [[ "$nome_file" == "frame.stl" ]] && continue
    [[ "$nome_file" == "64179.png" ]] && continue
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

# ESCLUDE INTERAMENTE QUESTE CARTELLE DALLO SNAPSHOT .md
    txt|.git|node_modules|data|public|old|gallery|img|backup_SQL|.venv|__pycache__) continue ;;
    *) dump_folder "$dir" "$foldername" ;;
  esac
done

# ESCLUSIONI FILE PER ESTENSIONE DAL TREE DEL PROGETTO
tree_exclude_files="*.zip"

# ESCLUSIONI CARTELLE DAL TREE DEL PROGETTO
tree_exclude_folders="node_modules|.git|txt"

# GENERA TREE DEL PROGETTO
tree -a -F -I "$tree_exclude_files|$tree_exclude_folders" --dirsfirst > project-tree.txt

echo "" >> project-tree.txt
echo "*** NOTE: some local files shown in this tree have been intentionally omitted from the repository ***" >> project-tree.txt

echo "Progetto mappato in project-tree.txt"
echo "Snapshot .md generati in txt"
