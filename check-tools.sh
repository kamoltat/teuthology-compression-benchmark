#!/bin/bash
set -e

echo "Checking compression tools..."
for tool in zstd brotli gzip pigz xz pbzip2 lz4; do
    if command -v $tool &>/dev/null; then
        echo "$tool is installed!"
    else
        echo "$tool is MISSING!!"
    fi
done

echo "Checking vmtouch..."
if command -v vmtouch &>/dev/null; then
    echo "vmtouch is installed!"
else
    echo "vmtouch is MISSING!!"
fi

echo "Checking sha256sum..."
if command -v sha256sum &>/dev/null; then
    echo "sha256sum is installed!"
else
    echo "sha256sum is MISSING!!"
fi