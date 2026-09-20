#!/usr/bin/env bash
set -Eeuo pipefail

declare -a paths_to_delete=(
  "image"
  "output"
  "workspace-dev"
  "build.log"
)

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

echo "Deleting all paths in ${project_dir} ..."
for path_to_delete in "${paths_to_delete[@]}"
do
   echo "  - ${path_to_delete}"
   rm -rf "${project_dir:?}/${path_to_delete}"
done
echo "... done."
