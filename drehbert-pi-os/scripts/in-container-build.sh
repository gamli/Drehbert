#!/usr/bin/env bash
set -Eeuo pipefail

profile="${1:-}"
case "${profile}" in
  dev|prod) ;;
  *)
    echo "Internal error: expected profile dev or prod." >&2
    exit 2
    ;;
esac

required=(BASE_IMAGE_URL BASE_IMAGE_FILENAME BASE_IMAGE_SHA256 DREHBERT_HOSTNAME)
for name in "${required[@]}"; do
  [[ -n "${!name:-}" ]] || {
    echo "Missing ${name} in the image configuration." >&2
    exit 1
  }
done

[[ "${BASE_IMAGE_FILENAME}" != */* ]] || {
  echo "BASE_IMAGE_FILENAME must be a file name, not a path." >&2
  exit 1
}

[[ "${BASE_IMAGE_SHA256}" =~ ^[0-9a-fA-F]{64}$ ]] || {
  echo "BASE_IMAGE_SHA256 must contain exactly 64 hexadecimal characters." >&2
  exit 1
}

if [[ "${profile}" == dev ]]; then
  dev_required=(
    DREHBERT_DEV_WIFI_SSID
    DREHBERT_DEV_WIFI_PASSWORD
    DREHBERT_DEV_WIFI_COUNTRY
    UV_VERSION
    UV_DOWNLOAD_URL
    UV_SHA256
  )
  for name in "${dev_required[@]}"; do
    [[ -n "${!name:-}" ]] || {
      echo "Missing ${name} in settings/02.dev.env." >&2
      exit 1
    }
  done

  [[ "${DREHBERT_DEV_WIFI_COUNTRY}" =~ ^[A-Z]{2}$ ]] || {
    echo "DREHBERT_DEV_WIFI_COUNTRY must be a two-letter uppercase country code." >&2
    exit 1
  }

  case "${DREHBERT_DEV_WIFI_HIDDEN:-no}" in
    yes|no) ;;
    *)
      echo "DREHBERT_DEV_WIFI_HIDDEN must be yes or no." >&2
      exit 1
      ;;
  esac

  [[ "${UV_SHA256}" =~ ^[0-9a-fA-F]{64}$ ]] || {
    echo "UV_SHA256 must contain exactly 64 hexadecimal characters." >&2
    exit 1
  }
fi

image_dir=/distro/image
image_path="${image_dir}/${BASE_IMAGE_FILENAME}"
partial_path="${image_path}.part"
mkdir -p "${image_dir}"

if [[ -f "${image_path}" ]] &&
   printf '%s  %s\n' "${BASE_IMAGE_SHA256}" "${image_path}" | sha256sum --check --status; then
  echo "Using verified cached base image: ${BASE_IMAGE_FILENAME}"
else
  rm -f "${partial_path}"
  trap 'rm -f "${partial_path}"' EXIT
  echo "Downloading pinned Raspberry Pi OS base image..."
  curl --fail --location --show-error --silent --retry 3 \
    --output "${partial_path}" "${BASE_IMAGE_URL}"
  printf '%s  %s\n' "${BASE_IMAGE_SHA256}" "${partial_path}" |
    sha256sum --check --status || {
      echo "Base image checksum mismatch." >&2
      exit 1
    }
  mv -f "${partial_path}" "${image_path}"
  trap - EXIT
fi

/usr/bin/build "${profile}"

case "${profile}" in
  dev)
    image_name=drehbert-pi-dev-os.img
    archive_name=drehbert-pi-dev-os.img.zip
    ;;
  prod)
    image_name=drehbert-pi-prod-os.img
    archive_name=drehbert-pi-prod-os.img.zip
    ;;
esac

workspace="/distro/workspace-${profile}"
archive_path="${workspace}/${archive_name}"
[[ -f "${archive_path}" ]] || {
  echo "CustomPiOS finished without producing ${archive_path}." >&2
  exit 1
}

mkdir -p /distro/output
mv -f "${archive_path}" "/distro/output/${archive_name}"
(
  cd /distro/output
  sha256sum "${archive_name}" > "${archive_name}.sha256"
)
rm -f "${workspace}/${image_name}"
chmod 0666 "/distro/output/${archive_name}" "/distro/output/${archive_name}.sha256"

echo "Created /distro/output/${archive_name}"
