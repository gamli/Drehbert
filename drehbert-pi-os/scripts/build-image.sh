#!/usr/bin/env bash
set -Eeuo pipefail

profile="${1:-}"
case "${profile}" in
  dev|prod) ;;
  *)
    echo "Usage: ${0##*/} dev|prod" >&2
    exit 2
    ;;
esac

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

sources_env="${project_dir}/settings/00.sources.env"
common_env="${project_dir}/settings/01.common.env"
profile_env="${project_dir}/settings/02.${profile}.env"

command -v docker >/dev/null 2>&1 || {
  echo "Docker was not found. On Windows, run this command in WSL2 with Docker Desktop integration enabled." >&2
  exit 1
}

[[ -f "${sources_env}" ]] || {
  echo "Missing ${sources_env}" >&2
  exit 1
}

[[ -f "${common_env}" ]] || {
  echo "Missing ${common_env}" >&2
  exit 1
}

[[ -f "${profile_env}" ]] || {
  echo "Missing ${profile_env}" >&2
  exit 1
}

builder_image="$(sed -n 's/^CUSTOMPIOS_IMAGE=//p' "${sources_env}")"
[[ -n "${builder_image}" ]] || {
  echo "CUSTOMPIOS_IMAGE is missing in ${sources_env}" >&2
  exit 1
}

mkdir -p "${project_dir}/image" "${project_dir}/output"

exec docker run --rm --pull=missing --privileged \
  --env-file "${sources_env}" \
  --env-file "${common_env}" \
  --env-file "${profile_env}" \
  --volume "${project_dir}:/distro" \
  --volume drehbert-pi-os-image:/distro/image \
  --volume "drehbert-pi-os-workspace-${profile}:/distro/workspace-${profile}" \
  "${builder_image}" \
  bash /distro/scripts/in-container-build.sh "${profile}"
