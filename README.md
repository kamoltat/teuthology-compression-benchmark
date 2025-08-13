# Teuthology Compression Benchmark

A comprehensive benchmarking tool for evaluating compression algorithms on a teuthology log file. This tool tests 8 different compression algorithms across multiple compression levels with both single-threaded and multi-threaded variants. The setup is in a container environment to ensure consistency and fairness.

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
- **zstd** (levels 1, 10, 19)

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

## 🏆 Key Findings & Production Recommendations

Based on 300MB teuthology log benchmarks and 10 iterations for each Algorithm and each level:

## 📈 Algorithm Performance Results 

### **gzip** (Single-threaded)
- **Low (1)**
  - Compression Ratio: 0.075
  - Compression Speed: 2.72s
  - Decompression Speed: 4.48s
  - Trade-off Score: 31.9/100
- **Mid (5) (Currently used in Teuthology production)**
  - Compression Ratio: 0.061
  - Compression Speed: 2.96s
  - Decompression Speed: 3.59s
  - Trade-off Score: 37.6/100
- **High (9)**
  - Compression Ratio: 0.045
  - Compression Speed: 19.54s
  - Decompression Speed: 3.41s
  - Trade-off Score: 35.6/100

### **zstd_single_threaded** (Single-threaded)
- **Low (1)**
  - Compression Ratio: 0.067
  - Compression Speed: 0.74s
  - Decompression Speed: 1.39s
  - Trade-off Score: 65.8/100
- **Mid (10)**
  - Compression Ratio: 0.047
  - Compression Speed: 7.60s
  - Decompression Speed: 1.27s
  - Trade-off Score: 40.3/100
- **High (19)**
  - Compression Ratio: 2.000 (timeout)
  - Compression Speed: 9999.00s (timeout)
  - Decompression Speed: 9999.00s (timeout)
  - Trade-off Score: (DNF)

### **brotli** (Single-threaded)
- **Low (1)**
  - Compression Ratio: 0.071
  - Compression Speed: 1.07s
  - Decompression Speed: 1.35s
  - Trade-off Score: 59.3/100
- **Mid (6)**
  - Compression Ratio: 0.049
  - Compression Speed: 6.44s
  - Decompression Speed: 1.17s
  - Trade-off Score: 41.2/100
- **High (11)**
  - Compression Ratio: 2.000 (timeout)
  - Compression Speed: 9999.00s (timeout)
  - Decompression Speed: 9999.00s (timeout)
  - Trade-off Score: (DNF)

### **xz** (Single-threaded)
- **Low (1)**
  - Compression Ratio: 0.051
  - Compression Speed: 8.86s
  - Decompression Speed: 8.53s
  - Trade-off Score: 32.9/100
- **Mid (6)**
  - Compression Ratio: 0.045
  - Compression Speed: 83.51s
  - Decompression Speed: 8.31s
  - Trade-off Score: 32.3/100
- **High (9)**
  - Compression Ratio: 0.043
  - Compression Speed: 84.42s
  - Decompression Speed: 8.28s
  - Trade-off Score: 33.4/100

### **lz4** (Single-threaded)
- **Low (1)**
  - Compression Ratio: 0.126
  - Compression Speed: 0.91s
  - Decompression Speed: 2.41s
  - Trade-off Score: 39.9/100
- **Mid (6)**
  - Compression Ratio: 0.068
  - Compression Speed: 6.67s
  - Decompression Speed: 2.32s
  - Trade-off Score: 31.4/100
- **High (9)**
  - Compression Ratio: 0.063
  - Compression Speed: 18.30s
  - Decompression Speed: 2.33s
  - Trade-off Score: 27.0/100

### **zstd_multithreaded** (Multi-threaded)
- **Low (1)**
  - Compression Ratio: 0.067
  - Compression Speed: 0.45s
  - Decompression Speed: 1.47s
  - Trade-off Score: 70.8/100
- **Mid (10)**
  - Compression Ratio: 0.047
  - Compression Speed: 1.89s
  - Decompression Speed: 1.27s
  - Trade-off Score: 59.8/100
- **High (19)**
  - Compression Ratio: 0.039
  - Compression Speed: 81.50s
  - Decompression Speed: 1.42s
  - Trade-off Score: 37.0/100

### **pigz** (Multi-threaded)
- **Low (1)**
  - Compression Ratio: 0.075
  - Compression Speed: 1.65s
  - Decompression Speed: 3.76s
  - Trade-off Score: 36.3/100
- **Mid (6)**
  - Compression Ratio: 0.052
  - Compression Speed: 1.81s
  - Decompression Speed: 3.88s
  - Trade-off Score: 44.0/100
- **High (9)**
  - Compression Ratio: 0.045
  - Compression Speed: 3.36s
  - Decompression Speed: 3.68s
  - Trade-off Score: 45.0/100

### **pbzip2** (Multi-threaded)
- **Low (1)**
  - Compression Ratio: 0.033
  - Compression Speed: 10.05s
  - Decompression Speed: 1.46s
  - Trade-off Score: 50.3/100
- **Mid (6)**
  - Compression Ratio: 0.029
  - Compression Speed: 16.63s
  - Decompression Speed: 3.69s
  - Trade-off Score: 53.5/100
- **High (9)**
  - Compression Ratio: 0.028
  - Compression Speed: 20.75s
  - Decompression Speed: 5.57s
  - Trade-off Score: 53.6/100

### 📊 Analyze Result (analyze_result.py output)

```
Analyzing results from: results_1754595284.json

=== Overall Best Results ===
 Top 3 Best Compression Ratios:
    1. 0.028 (pbzip2 - high)
    2. 0.029 (pbzip2 - mid)
    3. 0.033 (pbzip2 - low)

 Top 3 Fastest Compression + Decompression Speeds (seconds):
    1. 1.917s total (zstd_multithreaded - low)
    2. 2.130s total (zstd_single_threaded - low)
    3. 2.427s total (brotli - low)

 Top 3 Best Trade-off Scores:
    1. 70.8/100 (zstd_multithreaded - low)
    2. 65.8/100 (zstd_single_threaded - low)
    3. 59.8/100 (zstd_multithreaded - mid)

=== Best Single Thread Category Results ===
 Top 3 Best Compression Ratios:
    1. 0.043 (xz - high)
    2. 0.045 (gzip - high)
    3. 0.045 (xz - mid)

 Top 3 Fastest Speeds:
    1. 2.130s (zstd_single_threaded - low)
    2. 2.427s (brotli - low)
    3. 3.327s (lz4 - low)

 Top 3 Best Trade-off Scores:
    1. 65.8/100 (zstd_single_threaded - low)
    2. 59.3/100 (brotli - low)
    3. 41.2/100 (brotli - mid)

=== Best Multi-Thread Category Results ===
 Top 3 Best Compression Ratios:
    1. 0.028 (pbzip2 - high)
    2. 0.029 (pbzip2 - mid)
    3. 0.033 (pbzip2 - low)

 Top 3 Fastest Speeds:
    1. 1.917s (zstd_multithreaded - low)
    2. 3.160s (zstd_multithreaded - mid)
    3. 5.411s (pigz - low)

 Top 3 Best Trade-off Scores:
    1. 70.8/100 (zstd_multithreaded - low)
    2. 59.8/100 (zstd_multithreaded - mid)
    3. 53.6/100 (pbzip2 - high)

Analysis complete!
```

### 🚀 Production Recommendation Verdict

Based on the comprehensive analysis from `analyze_result.py`, we recommend **zstd_multithreaded level 10 (mid)** as the optimal choice for compressing teuthology log files at the end of jobs. This algorithm clearly outperforms the current production standard of `gzip level 5 (mid)` by delivering 36% faster compression times while achieving 23% better compression ratios.

The performance advantage is significant: while `gzip level 5 (mid)` takes 2.96 seconds for compression and achieves a 0.061 compression ratio, `zstd_multithreaded level 10 (mid)` completes compression in just 1.89 seconds with a superior 0.047 compression ratio. This translates to both faster job completion times and more storage saved.

However, if there are concerns about thread resource contention or depletion, **zstd_single_threaded level 10 (mid)** remains a good alternative. While it takes 7.60 seconds for compression (4.64 seconds slower than gzip level 5), it still maintains the same 23% improvement in compression ratio. We believe this 4.6-second increase in compression time is negligible compared to the substantial storage savings achieved.

**Notable mention:** For maximum compression when processing time is less critical, `pbzip2 level 6 (mid)` achieves the best compression ratio of 0.029, though it requires 16.63 seconds compression time which compared to 1.89s `zstd_multithreaded level 10 (mid)` it is significantly slower (8.8x), in the scenario where we are testing larger files e.g., osd.logs > 300MB a job with many heavy log files such as 10+ OSD thrashing jobs. 16.63 seconds compression time per file can potentially hold up the machine for a long period of time. Besides, `zstd_multithreaded (mid)` still achieve pretty good compression ratio of 0.047 which when compared to `gzip level 5 (mid)` compression ratio 0.061 still yields a 23% improvement.

The threading analysis reveals that zstd benefits significantly from multi-core utilization, achieving 75% faster compression performance when comparing single-threaded (7.60s) versus multi-threaded (1.89s) implementations at level 10.

### Future Improvements

The current scoring methodology weights compression and decompression speed equally (50%/50%) in the speed score calculation. However, for teuthology's production workflow, compression time is significantly more critical than decompression time since:

- Compression occurs at the end of every job, directly impacting job completion time
- Decompression happens less frequently, primarily during log analysis or debugging
- Users typically tolerate longer decompression times when accessing archived logs

A more accurate scoring model for teuthology would weight compression time more heavily (e.g., 70% compression, 30% decompression). This adjustment would better reflect the operational priorities and provide rankings more aligned with teuthology's actual performance requirements.