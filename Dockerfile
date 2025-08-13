FROM ubuntu:24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install core utilities and compression tools
# zstd: zstandard supports parallel
# gzip: Gzip single thread
# pigz: Parallel implementation of gzip
# pbzip2: Parallel implementation of bzip2
# xz-utils: XZ single thread
# brotli: Brotli single thread
# lz4: LZ4 single thread
# coreutils: Includes sha256sum
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    time \
    sudo \
    coreutils \
    zstd \
    gzip \
    pigz \
    pbzip2 \
    xz-utils \
    brotli \
    lz4 \
    vim \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Use vmtouch to flush file system cache
RUN git clone https://github.com/hoytech/vmtouch.git && \
    cd vmtouch && make && make install && cd .. && rm -rf vmtouch

# Copy and run check-tools.sh
COPY check-tools.sh /usr/local/bin/check-tools.sh
COPY run_benchmark.py /usr/local/bin/run_benchmark.py
COPY teuthology.log /usr/local/bin/teuthology.log
RUN chmod +x /usr/local/bin/check-tools.sh
RUN /usr/local/bin/check-tools.sh
