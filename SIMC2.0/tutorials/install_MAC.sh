#!/bin/bash

set -e

echo "==> Starting installation of Homebrew and Python 3.13..."

# Install Homebrew if not already installed
if command -v brew &>/dev/null; then
    echo "==> Homebrew is already installed. Skipping."
else
    echo "==> Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Python 3.13 if not already installed
if brew list python@3.13 &>/dev/null; then
    echo "==> Python 3.13 is already installed. Skipping."
else
    echo "==> Installing Python 3.13..."
    brew install python@3.13
fi

echo ""
echo "Done! Homebrew and Python 3.13 have been installed."
echo ""
echo "Python version:"
brew list --versions python@3.13