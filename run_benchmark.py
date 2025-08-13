"""
Compression Benchmark Tool
"""

import os
import sys
import time
import subprocess
import csv
import json
from pathlib import Path
import random

ITERATIONS = 1  # Number of iterations for each algorithm/level
ALGORITHMS_SINGLE_THREADS = {
    'gzip': {
        'compress_cmd': 'gzip -c -{level}',
        'decompress_cmd': 'gzip -dc',
        'levels': {'low': 1, 'mid': 5, 'high': 9},  # gzip -c -5 is used by production teuthology
        'extension': '.gz'
    },
    'brotli': {
        'compress_cmd': 'brotli -c -q {level}',  # brotli uses -q for quality
        'decompress_cmd': 'brotli -dc',
        'levels': {'low': 1, 'mid': 6, 'high': 11},
        'extension': '.br'
    },
    'xz': {
        'compress_cmd': 'xz -c -{level}',
        'decompress_cmd': 'xz -dc',
        'levels': {'low': 1, 'mid': 6, 'high': 9},
        'extension': '.xz'
    },
    'lz4': {
        'compress_cmd': 'lz4 -c -{level}',
        'decompress_cmd': 'lz4 -dc',
        'levels': {'low': 1, 'mid': 6, 'high': 9},
        'extension': '.lz4'
    },
    'zstd_single_threaded': {
        'compress_cmd': 'zstd -c -{level}',  # single-threaded (no -T flag)
        'decompress_cmd': 'zstd -dc',
        'levels': {'low': 1, 'mid': 10, 'high': 19},
        'extension': '.zst'
    }
}

ALGORITHMS_MULTI_THREADS = {
    # All available CPU cores will be used
    'zstd_multithreaded': {
        'compress_cmd': 'zstd -c -{level} -T0',
        'decompress_cmd': 'zstd -dc -T0',
        'levels': {'low': 1, 'mid': 10, 'high': 19},
        'extension': '.zst'
    },
    'pigz': {
        'compress_cmd': 'pigz -c -{level}',
        'decompress_cmd': 'pigz -dc',
        'levels': {'low': 1, 'mid': 6, 'high': 9},
        'extension': '.gz'
    },
    'pbzip2': {
        'compress_cmd': 'pbzip2 -c -{level}',
        'decompress_cmd': 'pbzip2 -dc',
        'levels': {'low': 1, 'mid': 6, 'high': 9},
        'extension': '.bz2'
    }
}

# Add penalty constants at the top
COMPRESSION_TIMEOUT = 90  # 90 seconds timeout
DECOMPRESSION_TIMEOUT = 30  # 30 seconds timeout
TEST_FILE_SIZE = 300 * 1024 * 1024  # 300MB test file size


def check_sha256sum(file1: str, file2: str) -> bool:
    """
    Compare SHA256 checksums of two files using system sha256sum command
    """
    try:
        # Get checksum of first file
        # capture_output=True allows us to capture stdout/stderr
        # text=True returns output as string instead of bytes
        result1 = subprocess.run(['sha256sum', file1],
                                 capture_output=True, text=True)
        if result1.returncode != 0:
            return False
        checksum1 = result1.stdout.split()[0]

        # Get checksum of second file
        # capture_output=True allows us to capture stdout/stderr
        # text=True returns output as string instead of bytes
        result2 = subprocess.run(['sha256sum', file2],
                                 capture_output=True, text=True)
        if result2.returncode != 0:
            return False
        checksum2 = result2.stdout.split()[0]

        return checksum1 == checksum2

    except Exception as e:
        print(f"Error checking SHA256: {e}")
        return False


def flush_cache(file_path: str) -> bool:
    """
    Flush file from cache using vmtouch

    """
    try:
        # capture_output=True allows us to capture stdout/stderr
        # text=True returns output as string instead of bytes
        # Evict the file from cache!
        subprocess.run(
            ['vmtouch', '-e', file_path],
            capture_output=True, check=True
        )
        # Check if the file is flushed
        result = subprocess.run(
            ['vmtouch', file_path],
            capture_output=True, text=True
        )
        # Parse vmtouch output to verify cache is flushed
        if "Resident Pages: 0/" in result.stdout:
            print(f"Cache flushed for {file_path}")
            return True
        else:
            print(f"Cache not flushed for {file_path}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Warning: Cache flush failed: {e}")
        return False


def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    return os.path.getsize(file_path)


def generate_log_line():
    log_lines = [
        f"2025-08-15 10:30:45 INFO: Starting teuthology job {random.randint(10000, 99999)}\n",
        f"2025-08-15 10:30:46 DEBUG: Connecting to cluster nodes {random.randint(10000, 99999)}\n",
        f"2025-08-15 10:30:47 ERROR: Connection timeout on node-{random.randint(1, 10)}\n",
        f"2025-08-15 10:30:48 WARN: Retrying connection to node-{random.randint(1, 10)}\n",
        "2025-08-15 10:30:49 INFO: Successfully connected to all nodes\n"
    ]
    return random.choice(log_lines)


def create_test_file():
    """
    Create a test file of size
    TEST_FILE_SIZE if teuthology.log doesn't exist
    """

    if os.path.exists("teuthology.log"):
        return  # File already exists, don't overwrite

    print(f"Creating test file of size {TEST_FILE_SIZE / 1024 / 1024:.1f} MB...")
    target_size = TEST_FILE_SIZE

    with open("teuthology.log", "w") as f:
        written = 0
        while written < target_size:
            for line in generate_log_line():
                f.write(line)
                written += len(line)
                if written >= target_size:
                    break

    size_mb = os.path.getsize("teuthology.log") / 1024 / 1024
    print(f"Created teuthology.log: {size_mb:.1f} MB")


def main():
    # Create test file if it doesn't exist
    create_test_file()

    # Use teuthology.log as the input file (should be present in container)
    input_file = Path("teuthology.log")
    if not input_file.exists():
        print("Error: teuthology.log not found in current directory!")
        sys.exit(1)

    print(f"Starting benchmark with input file: {input_file}")
    original_size = get_file_size(str(input_file))

    TIMEOUT_PENALTY_TIME = 9999.0  # Large penalty time for timeouts
    TIMEOUT_PENALTY_SIZE = original_size * 2  # Worse than no compression

    print(f"Original file size: {original_size}")

    # Initialize results collection - now collect raw data per iteration
    raw_results = []

    # ALGORITHMS_SINGLE_THREADS
    print("Testing Single-Threaded Algorithms")
    for algorithm, config in ALGORITHMS_SINGLE_THREADS.items():
        print(f"Testing {algorithm}...")
        for level_name, level_value in config['levels'].items():
            print(f"Level {level_name} ({level_value}):")
            iteration_data = []

            for i in range(ITERATIONS):
                print(f"Iteration {i+1}/{ITERATIONS}...")
                compression_time = None
                decompression_time = None
                compressed_size = None
                sha256_valid = False
                compressed_file = None
                decompressed_file = None
                try:
                    # Compression
                    try:
                        flush_cache(str(input_file))
                        cmd = config['compress_cmd'].format(level=level_value)
                        compressed_file = f"{algorithm}_{level_name}_iter{i}_compressed{config['extension']}"

                        start_time = time.perf_counter()
                        with open(input_file, 'rb') as infile:
                            with open(compressed_file, 'wb') as outfile:
                                process = subprocess.Popen(
                                    cmd.split(), stdin=infile,
                                    stdout=outfile,
                                    stderr=subprocess.PIPE
                                )
                                try:
                                    _, stderr = process.communicate(timeout=COMPRESSION_TIMEOUT)
                                    compression_time = time.perf_counter() - start_time

                                    if process.returncode != 0:
                                        print(f"Compression failed: {stderr.decode()}")
                                        continue

                                    compressed_size = get_file_size(compressed_file)
                                    print(f"Compression Time: {compression_time:.3f}s, Size: {compressed_size}")

                                except subprocess.TimeoutExpired:
                                    process.kill()
                                    process.wait()
                                    print(f"Compression timeout ({COMPRESSION_TIMEOUT}s) - assigning penalty")
                                    compression_time = TIMEOUT_PENALTY_TIME
                                    decompression_time = TIMEOUT_PENALTY_TIME
                                    compressed_size = TIMEOUT_PENALTY_SIZE
                                    sha256_valid = False
                                    # Skip decompression section entirely
                                    continue

                    except Exception as e:
                        print(f"Compression exception: {e}")
                        continue

                    # Decompression
                    # (only runs if compression succeeded)
                    try:
                        flush_cache(compressed_file)
                        decompressed_file = f"{algorithm}_{level_name}_iter{i}_decompressed.log"
                        decompress_cmd = config['decompress_cmd'].format(level=level_value)

                        start_time = time.perf_counter()
                        with open(compressed_file, 'rb') as infile:
                            with open(decompressed_file, 'wb') as outfile:
                                process = subprocess.Popen(
                                    decompress_cmd.split(), stdin=infile,
                                    stdout=outfile,
                                    stderr=subprocess.PIPE
                                )
                                try:
                                    _, stderr = process.communicate(timeout=DECOMPRESSION_TIMEOUT)
                                    decompression_time = time.perf_counter() - start_time

                                    if process.returncode != 0:
                                        print(f"Decompression failed: {stderr.decode()}")
                                        continue

                                    # Check sha256sum
                                    if check_sha256sum(str(input_file), decompressed_file):
                                        sha256_valid = True
                                        print("Verification passed")
                                    else:
                                        print("Verification failed")

                                except subprocess.TimeoutExpired:
                                    process.kill()
                                    process.wait()
                                    print(f"Decompression timeout ({DECOMPRESSION_TIMEOUT}s) - assigning penalty")
                                    decompression_time = TIMEOUT_PENALTY_TIME
                                    sha256_valid = False

                        print(f"Decompression Time: {decompression_time:.3f}s")

                    except Exception as e:
                        print(f"Decompression exception: {e}")

                finally:
                    # Clean up files safely regardless of success or failure
                    if compressed_file and os.path.exists(compressed_file):
                        os.unlink(compressed_file)
                    if decompressed_file and os.path.exists(decompressed_file):
                        os.unlink(decompressed_file)
                    # Store this iteration's data (including penalties)
                    if compression_time and decompression_time and compressed_size:
                        iteration_data.append({
                            'compression_time': compression_time,
                            'decompression_time': decompression_time,
                            'compressed_size': compressed_size,
                            'sha256_valid': sha256_valid
                        })

            # Exit the third for-loop; Calculate averages for this algorithm/level combination
            if iteration_data:
                avg_compression_time = sum(d['compression_time'] for d in iteration_data) / len(iteration_data)
                avg_decompression_time = sum(d['decompression_time'] for d in iteration_data) / len(iteration_data)
                avg_compressed_size = sum(d['compressed_size'] for d in iteration_data) / len(iteration_data)
                avg_compression_ratio = avg_compressed_size / original_size
                successful_iterations = len(iteration_data)

                result = {
                    'algorithm': algorithm,
                    'is_threaded': False,
                    'level_name': level_name,
                    'level_value': level_value,
                    'iterations': successful_iterations,
                    'original_size': original_size,
                    'avg_compressed_size': avg_compressed_size,
                    'avg_compression_ratio': avg_compression_ratio,
                    'avg_compression_time': avg_compression_time,
                    'avg_decompression_time': avg_decompression_time,
                    'all_sha256_valid': all(d['sha256_valid'] for d in iteration_data),
                }
                raw_results.append(result)

    # ALGORITHMS_MULTI_THREADS (same pattern)
    print("Testing Multi-Threaded Algorithms")
    for algorithm, config in ALGORITHMS_MULTI_THREADS.items():
        print(f"Testing {algorithm}...")
        for level_name, level_value in config['levels'].items():
            print(f"Level {level_name} ({level_value}):")
            iteration_data = []

            for i in range(ITERATIONS):
                print(f"Iteration {i+1}/{ITERATIONS}...")
                compression_time = None
                decompression_time = None
                compressed_size = None
                sha256_valid = False
                compressed_file = None
                decompressed_file = None
                try:
                    # Compression
                    try:
                        flush_cache(str(input_file))
                        cmd = config['compress_cmd'].format(level=level_value)
                        compressed_file = f"{algorithm}_{level_name}_iter{i}_compressed{config['extension']}"

                        start_time = time.perf_counter()
                        with open(input_file, 'rb') as infile:
                            with open(compressed_file, 'wb') as outfile:
                                process = subprocess.Popen(
                                    cmd.split(), stdin=infile,
                                    stdout=outfile,
                                    stderr=subprocess.PIPE
                                )
                                try:
                                    _, stderr = process.communicate(timeout=COMPRESSION_TIMEOUT)
                                    compression_time = time.perf_counter() - start_time

                                    if process.returncode != 0:
                                        print(f"Compression failed: {stderr.decode()}")
                                        continue

                                    compressed_size = get_file_size(compressed_file)
                                    print(f"Compression Time: {compression_time:.3f}s, Size: {compressed_size}")

                                except subprocess.TimeoutExpired:
                                    process.kill()
                                    process.wait()
                                    print(f"Compression timeout ({COMPRESSION_TIMEOUT}s) - assigning penalty")
                                    compression_time = TIMEOUT_PENALTY_TIME
                                    decompression_time = TIMEOUT_PENALTY_TIME
                                    compressed_size = TIMEOUT_PENALTY_SIZE
                                    sha256_valid = False
                                    # Skip decompression section entirely
                                    continue

                    except Exception as e:
                        print(f"Compression exception: {e}")
                        continue

                    # Decompression (only runs if compression succeeded)
                    try:
                        flush_cache(compressed_file)
                        decompressed_file = f"{algorithm}_{level_name}_iter{i}_decompressed.log"
                        decompress_cmd = config['decompress_cmd'].format(level=level_value)

                        start_time = time.perf_counter()
                        with open(compressed_file, 'rb') as infile:
                            with open(decompressed_file, 'wb') as outfile:
                                process = subprocess.Popen(
                                    decompress_cmd.split(), stdin=infile,
                                    stdout=outfile,
                                    stderr=subprocess.PIPE
                                )
                                try:
                                    _, stderr = process.communicate(timeout=DECOMPRESSION_TIMEOUT)
                                    decompression_time = time.perf_counter() - start_time

                                    if process.returncode != 0:
                                        print(f"Decompression failed: {stderr.decode()}")
                                        continue

                                    # Check sha256sum
                                    if check_sha256sum(str(input_file), decompressed_file):
                                        sha256_valid = True
                                        print("Verification passed")
                                    else:
                                        print("Verification failed")

                                except subprocess.TimeoutExpired:
                                    process.kill()
                                    process.wait()
                                    print(f"Decompression timeout ({DECOMPRESSION_TIMEOUT}s) - assigning penalty")
                                    decompression_time = TIMEOUT_PENALTY_TIME
                                    sha256_valid = False
                        print(f"Decompression Time: {decompression_time:.3f}s")

                    except Exception as e:
                        print(f"Decompression exception: {e}")
                finally:
                    # Clean up files safely
                    if compressed_file and os.path.exists(compressed_file):
                        os.unlink(compressed_file)
                    if decompressed_file and os.path.exists(decompressed_file):
                        os.unlink(decompressed_file)
                    # Store this iteration's data (including penalties)
                    if compression_time and decompression_time and compressed_size:
                        iteration_data.append({
                            'compression_time': compression_time,
                            'decompression_time': decompression_time,
                            'compressed_size': compressed_size,
                            'sha256_valid': sha256_valid
                        })

            # Calculate averages
            if iteration_data:
                avg_compression_time = sum(d['compression_time'] for d in iteration_data) / len(iteration_data)
                avg_decompression_time = sum(d['decompression_time'] for d in iteration_data) / len(iteration_data)
                avg_compressed_size = sum(d['compressed_size'] for d in iteration_data) / len(iteration_data)
                avg_compression_ratio = avg_compressed_size / original_size
                successful_iterations = len(iteration_data)
                result = {
                    'algorithm': algorithm,
                    'is_threaded': True,
                    'level_name': level_name,
                    'level_value': level_value,
                    'iterations': successful_iterations,
                    'original_size': original_size,
                    'avg_compressed_size': avg_compressed_size,
                    'avg_compression_ratio': avg_compression_ratio,
                    'avg_compression_time': avg_compression_time,
                    'avg_decompression_time': avg_decompression_time,
                    'all_sha256_valid': all(d['sha256_valid'] for d in iteration_data),
                }
                raw_results.append(result)

    # After collecting all results, calculate + normalized scores
    if raw_results:
        # Inverse the compression ratio for normalization and scoring aesthetics
        # (smaller = better compression), but for scoring we want original/compressed (bigger = better compression).
        max_ratio_seen = max(1 / result['avg_compression_ratio'] for result in raw_results)
        min_time_seen = min(result['avg_compression_time'] + result['avg_decompression_time'] for result in raw_results)

        # Add normalized scores to each result
        for result in raw_results:
            # Compression score: normalize compression ratio to 0-1 (e.g., 1 = best, 0 = worst)
            compression_score = (1 / result['avg_compression_ratio']) / max_ratio_seen

            # Speed score: normalize time to 0-1 (e.g., 0.9, 1 being fastest) (faster = higher score)
            # e.g., speed_score = 0.5 means it's twice as slow as the fastest
            total_time = result['avg_compression_time'] + result['avg_decompression_time']
            speed_score = min_time_seen / total_time

            # Combined trade-off score (0-100)
            trade_off_score = (compression_score + speed_score) / 2 * 100

            # Add to result
            result['compression_score'] = compression_score
            result['speed_score'] = speed_score
            result['trade_off_score'] = trade_off_score

    # Save results to files
    timestamp = int(time.time())

    # Save as JSON
    json_file = f"results_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(raw_results, f, indent=2)

    # Save as CSV
    csv_file = f"results_{timestamp}.csv"
    if raw_results:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=raw_results[0].keys())
            writer.writeheader()
            writer.writerows(raw_results)

    print("Results saved:")
    print(f"JSON: {json_file}")
    print(f"CSV: {csv_file}")
    print(f"Total tests: {len(raw_results)}")

    print("\nTest Finish!")


if __name__ == "__main__":
    main()
