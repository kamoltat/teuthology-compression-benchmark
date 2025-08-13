#!/bin/bash
set -e

# Check for --dev flag
DEV_MODE=false
if [[ "$1" == "--dev" ]]; then
    DEV_MODE=true
fi

echo "Building compression benchmark container..."
docker build -t compbench .

if [[ "$DEV_MODE" == "true" ]]; then
    echo "Starting container in development mode..."
    echo "Your local directory is mounted at /data - changes will be reflected immediately!"
    docker run --rm -it \
      --cpuset-cpus="0-5" \
      --memory="8g" \
      --memory-swap="8g" \
      --privileged \
      -v $PWD:/data \
      -w /data \
      compbench /bin/bash
else
    echo "Starting container in normal mode..."
    echo "Run './start.sh --dev' for development mode with live file mounting."
    docker run --rm -it \
      --cpuset-cpus="0-5" \
      --memory="8g" \
      --memory-swap="8g" \
      --privileged \
      compbench /bin/bash
fi