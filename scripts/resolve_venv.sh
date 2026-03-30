# shellcheck shell=bash
# Pick a virtualenv path: respect VENV if set; else .venv under ROOT when writable;
# else a per-user cache dir (read-only project trees, e.g. DMG or network share).
signature_packet_venv_path() {
  local root="$1"
  if [ -n "${VENV:-}" ]; then
    printf '%s\n' "$VENV"
    return
  fi
  if [ -w "$root" ]; then
    printf '%s\n' "$root/.venv"
    return
  fi
  local home="${HOME:-/tmp}"
  local cache_root="${XDG_CACHE_HOME:-$home/.cache}"
  printf '%s\n' "$cache_root/signature-packet/venv"
}
