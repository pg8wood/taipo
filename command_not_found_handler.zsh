TAIPO_DIR="$(dirname "$0")"

command_not_found_handler() {
  "$TAIPO_DIR/.venv/bin/python" "$TAIPO_DIR/taipo.py" "$@"
  return $?
}