# Teuthology Compression Benchmark

A comprehensive benchmarking tool for evaluating compression algorithms on teuthology log files. This tool tests 8 different compression algorithms across multiple compression levels with both single-threaded and multi-threaded variants.

## Overview

This benchmark evaluates compression performance across three key metrics:
- **Compression Ratio**: How much the file size is reduced
- **Speed**: Combined compression + decompression time
- **Trade-off Score**: Balanced score considering both compression and speed

## Algorithms Tested

### Single-Threaded
- **gzip** (levels 1, 5, 9) - Current teuthology production standard
- **brotli** (levels 1, 6, 11) - Web-optimized compression
- **xz** (levels 1, 6, 9) - High compression ratio
- **lz4** (levels 1, 6, 9) - Speed-focused compression
- **zstd** (levels 1, 10, 19) - Modern balanced algorithm

### Multi-Threaded
- **zstd_multithreaded** (levels 1, 10, 19) - Multi-core zstd
- **pigz** (levels 1, 6, 9) - Parallel gzip
- **pbzip2** (levels 1, 6, 9) - Parallel bzip2

## Quick Start

### 1. Start the Container

```bash
# Normal mode - run benchmark in isolated container
./start.sh

# Development mode - mount local directory for live editing
./start.sh --dev
```

The container provides:
- All compression tools pre-installed
- 6 CPU cores allocated (`--cpuset-cpus="0-5"`)
- 8GB memory limit
- Privileged access for cache management

### 2. Run the Benchmark

```bash
# Inside the container
python run_benchmark.py
```

This will:
- Create a 300MB test file (`teuthology.log`) if it doesn't exist
- Test all algorithms with cold cache (using `vmtouch`)
- Run 10 iterations per algorithm/level combination
- Generate timestamped results files

**Output files:**
- `results_[timestamp].json` - Detailed JSON results
- `results_[timestamp].csv` - CSV format for spreadsheet analysis

### 3. Analyze Results

```bash
# Analyze the generated results
python analyze_result.py results_[timestamp].json
```

**Example output:**
```
=== Overall Best Results ===
 Top 3 Best Compression Ratios:
    1. 0.028 (pbzip2 - high)
    2. 0.029 (pbzip2 - mid)
    3. 0.033 (pbzip2 - low)

 Top 3 Fastest Compression Speeds:
    1. 1.923s total (zstd_multithreaded - low)
    2. 2.134s total (zstd_single_threaded - low)
    3. 2.433s total (brotli - low)

 Top 3 Best Trade-off Scores:
    1. 70.8/100 (zstd_multithreaded - low)
    2. 65.8/100 (zstd_single_threaded - low)
    3. 59.8/100 (zstd_multithreaded - mid)
```

### 4. Clean Up

```bash
# Remove all generated results files
python clean_up.py
```

## Script Details

### `start.sh`
Container management script with two modes:

**Normal Mode:**
```bash
./start.sh
```
- Builds the Docker container
- Runs benchmark in isolated environment
- Files created inside container are not persistent

**Development Mode:**
```bash
./start.sh --dev
```
- Mounts local directory to `/data` in container
- Changes made inside container persist locally
- Useful for modifying scripts and keeping results

### `run_benchmark.py`
Main benchmarking engine that:

**Test Configuration:**
- Tests each algorithm at 3 compression levels (low/mid/high)
- Runs 10 iterations per configuration for statistical reliability
- Uses cold cache testing with `vmtouch` for consistent results
- Implements timeouts with penalty scoring for slow algorithms

**Metrics Collected:**
- Compression time and decompression time
- Compressed file size and compression ratio
- SHA256 verification for data integrity
- Normalized scores for fair comparison

**Key Features:**
- Automatic test file generation (300MB simulated teuthology log)
- Resource-safe cleanup with `finally` blocks
- Timeout handling (90s compression, 30s decompression)
- Both single-threaded and multi-threaded algorithm testing

### `analyze_result.py`
Results analysis tool that processes benchmark output:

**Usage:**
```bash
python analyze_result.py results_1754595284.json
```

**Analysis Categories:**
- **Overall Best**: Top performers across all algorithms
- **Single-Threaded Category**: Best within single-threaded algorithms only
- **Multi-Threaded Category**: Best within multi-threaded algorithms only

**Metrics Displayed:**
- Top 3 compression ratios (best space savings)
- Top 3 fastest speeds (total compression + decompression time)
- Top 3 trade-off scores (balanced compression and speed)

### `clean_up.py`
Utility script for removing generated files:

```bash
python clean_up.py
```

**What it removes:**
- All `results_*.json` files
- All `results_*.csv` files
- Displays count of files cleaned

## Key Findings

Based on 300MB teuthology log benchmarks:

### Production Recommendations

**For FAST Real-time Logging:**
- `zstd_multithreaded level 1` - 1.92s total, 6.7% compression ratio

**For Daily Archival (MOST suited for Teuthology):**
- `zstd_multithreaded level 10` - 3.16s total, 4.7% compression ratio
- **Replaces gzip level 5**: 52% faster, 23% better compression

**For Long-term Storage (BEST Compression):**
- `pbzip2 level 6` - 20.3s total, 2.9% compression ratio

### Threading Considerations

**Multi-threaded Benefits:**
- zstd: 39% faster with threading (2.13s → 1.92s)

**Production Safety:**
- Use `zstd_single_threaded level 10` for resource-constrained environments
- Still 23% better compression than gzip with 65% faster decompression

## Container Specifications

- **Base**: Ubuntu with compression tools
- **CPU**: Limited to 6 cores for controlled testing
- **Memory**: 8GB limit with swap disabled
- **Privileges**: Required for cache management operations
- **Tools**: gzip, brotli, xz, lz4, zstd, pigz, pbzip2, vmtouch

## System Requirements

- Docker installed and running
- At least 8GB available RAM
- 6+ CPU cores recommended
- ~2GB disk space for container and test files

## Customization

Edit `run_benchmark.py` to modify:
- `ITERATIONS`: Number of test runs per algorithm (default: 10)
- `TEST_FILE_SIZE` Test file size (default: 300MB)
- ` COMPRESSION_TIMEOUT `/ `DECOMPRESSION_TIMEOUT` Compression/decompression timeouts
- Algorithm configurations and levels

## Troubleshooting

**Permission Issues:**
```bash
chmod +x start.sh
```

**Container Build Failures:**
```bash
docker system prune  # Clean up old containers
./start.sh
```

**Memory Issues:**
Reduce iterations in `run_benchmark.py` or increase container memory limits in `start.sh`.