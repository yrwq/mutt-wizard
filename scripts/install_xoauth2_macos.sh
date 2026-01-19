#!/bin/sh

set -eu

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install from https://brew.sh/."
  exit 1
fi

brew install libtool automake autoconf cyrus-sasl

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

git clone https://github.com/moriyoshi/cyrus-sasl-xoauth2.git "$workdir/cyrus-sasl-xoauth2"
cd "$workdir/cyrus-sasl-xoauth2"

if ! command -v glibtoolize >/dev/null 2>&1; then
  echo "glibtoolize not found. Try: brew reinstall libtool"
  exit 1
fi

sed -i '' 's/libtoolize/glibtoolize/' autogen.sh

./autogen.sh
./configure --with-cyrus-sasl=/opt/homebrew
make
sudo make install

echo "Installed XOAUTH2 SASL plugin."
echo "If needed, export SASL_PATH=/opt/homebrew/lib/sasl2"
