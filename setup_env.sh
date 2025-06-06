#!/bin/bash

# Setup Flutter SDK and gomobile. Run on a machine with Internet access.
set -e

# Install Flutter SDK if missing
if ! command -v flutter >/dev/null 2>&1; then
  echo "Downloading Flutter SDK..."
  git clone https://github.com/flutter/flutter.git -b stable flutter_sdk
  export PATH="$(pwd)/flutter_sdk/bin:$PATH"
fi

# Install gomobile if missing
if ! command -v gomobile >/dev/null 2>&1; then
  echo "Installing gomobile..."
  go install golang.org/x/mobile/cmd/gomobile@latest
  gomobile init
fi

cat <<INSTRUCTIONS
Add flutter_sdk/bin and \$(go env GOPATH)/bin to your PATH after running this script.
INSTRUCTIONS

