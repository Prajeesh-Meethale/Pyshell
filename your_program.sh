#!/bin/sh
#
# Use this script to run PyShell locally.

set -e # Exit early if any commands fail

exec uv run --quiet -m app.main "$@"
