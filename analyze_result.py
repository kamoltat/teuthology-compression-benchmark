import argparse
import json
import sys
from pathlib import Path


def analyze_results(results_file):
    """Analyze compression benchmark results"""
    try:
        # Load the JSON results
        with open(results_file, 'r') as f:
            results = json.load(f)

        print(f"Analyzing results from: {results_file}")
        print()
        # Calculate Overall Best - Top 3:
        print("=== Overall Best Results ===")
        # Top 3 compression ratios (best compression)
        top_compression = sorted(results, key=lambda x: x['compression_score'], reverse=True)[:3]
        print(" Top 3 Best Compression Ratios:")
        for i, result in enumerate(top_compression, 1):
            print(f"    {i}. {result['avg_compression_ratio']:.3f} "
                  f"({result['algorithm']} - {result['level_name']})")
        print()

        # Top 3 compression speeds (fastest)
        top_speed = sorted(results, key=lambda x: x['speed_score'], reverse=True)[:3]
        print(" Top 3 Fastest Compression + Decompression Speeds (seconds):")
        for i, result in enumerate(top_speed, 1):
            total_time = result['avg_compression_time'] + result['avg_decompression_time']
            print(f"    {i}. {total_time:.3f}s total "
                  f"({result['algorithm']} - {result['level_name']})")
        print()

        # Top 3 trade-off scores (best balance)
        top_tradeoff = sorted(results, key=lambda x: x['trade_off_score'], reverse=True)[:3]
        print(" Top 3 Best Trade-off Scores:")
        for i, result in enumerate(top_tradeoff, 1):
            print(f"    {i}. {result['trade_off_score']:.1f}/100 "
                  f"({result['algorithm']} - {result['level_name']})")
        print()

        print("=== Best Single Thread Category Results ===")

        # Filter single-threaded results
        single_threaded = [r for r in results if not r['is_threaded']]

        if single_threaded:
            # Top 3 compression for single-threaded
            top_single_compression = sorted(single_threaded, key=lambda x: x['compression_score'], reverse=True)[:3]
            print(" Top 3 Best Compression Ratios:")
            for i, result in enumerate(top_single_compression, 1):
                print(f"    {i}. {result['avg_compression_ratio']:.3f} "
                      f"({result['algorithm']} - {result['level_name']})")
            print()

            # Top 3 fastest single-threaded
            top_single_speed = sorted(single_threaded, key=lambda x: x['speed_score'], reverse=True)[:3]
            print(" Top 3 Fastest Speeds:")
            for i, result in enumerate(top_single_speed, 1):
                total_time = result['avg_compression_time'] + result['avg_decompression_time']
                print(f"    {i}. {total_time:.3f}s "
                      f"({result['algorithm']} - {result['level_name']})")
            print()

            # Top 3 trade-off for single-threaded
            top_single_tradeoff = sorted(single_threaded, key=lambda x: x['trade_off_score'], reverse=True)[:3]
            print(" Top 3 Best Trade-off Scores:")
            for i, result in enumerate(top_single_tradeoff, 1):
                print(f"    {i}. {result['trade_off_score']:.1f}/100 "
                      f"({result['algorithm']} - {result['level_name']})")
        else:
            print("No single-threaded results found")
        print()

        print("=== Best Multi-Thread Category Results ===")

        # Filter multi-threaded results
        multi_threaded = [r for r in results if r['is_threaded']]

        if multi_threaded:
            # Top 3 compression for multi-threaded
            top_multi_compression = sorted(multi_threaded, key=lambda x: x['compression_score'], reverse=True)[:3]
            print(" Top 3 Best Compression Ratios:")
            for i, result in enumerate(top_multi_compression, 1):
                print(f"    {i}. {result['avg_compression_ratio']:.3f} "
                      f"({result['algorithm']} - {result['level_name']})")
            print()

            # Top 3 fastest multi-threaded
            top_multi_speed = sorted(multi_threaded, key=lambda x: x['speed_score'], reverse=True)[:3]
            print(" Top 3 Fastest Speeds:")
            for i, result in enumerate(top_multi_speed, 1):
                total_time = result['avg_compression_time'] + result['avg_decompression_time']
                print(f"    {i}. {total_time:.3f}s "
                      f"({result['algorithm']} - {result['level_name']})")
            print()

            # Top 3 trade-off for multi-threaded
            top_multi_tradeoff = sorted(multi_threaded, key=lambda x: x['trade_off_score'], reverse=True)[:3]
            print(" Top 3 Best Trade-off Scores:")
            for i, result in enumerate(top_multi_tradeoff, 1):
                print(f"    {i}. {result['trade_off_score']:.1f}/100 "
                      f"({result['algorithm']} - {result['level_name']})")
        else:
            print("No multi-threaded results found")
        print()

        return results

    except FileNotFoundError:
        print(f"Error: File {results_file} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {results_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing results: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze compression benchmark results'
    )
    parser.add_argument('results_file',
                        help='Path to the JSON results file (e.g., results_1754595284.json)')

    args = parser.parse_args()

    # Validate file exists
    if not Path(args.results_file).exists():
        print(f"Error: File {args.results_file} does not exist")
        sys.exit(1)

    print("Running benchmark analysis...")
    results = analyze_results(args.results_file)

    # Add more analysis functions here
    print("Analysis complete!")


if __name__ == "__main__":
    main()
