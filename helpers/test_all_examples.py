#!/usr/bin/env python3
"""
Concurrent test runner for all observability examples.
Runs all examples in parallel with timeout and captures output/errors.
"""

import os
import sys
import subprocess
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing


def find_examples():
    """Find all numbered example files."""
    examples_dir = Path("examples/observability")
    examples = []
    
    for file in sorted(examples_dir.glob("*.py")):
        if file.name[0:2].isdigit() and file.name.endswith(".py"):
            examples.append(file)
    
    return examples


def run_example(example_path, timeout=30):
    """Run a single example with timeout."""
    start_time = time.time()
    
    try:
        # Run with timeout
        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd()  # Run from project root
        )
        
        duration = time.time() - start_time
        
        return {
            "example": example_path.name,
            "status": "success" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": duration,
            "error": None
        }
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return {
            "example": example_path.name,
            "status": "timeout",
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timeout after {timeout} seconds",
            "duration": duration,
            "error": "TimeoutExpired"
        }
        
    except Exception as e:
        duration = time.time() - start_time
        return {
            "example": example_path.name,
            "status": "error",
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "duration": duration,
            "error": type(e).__name__
        }


def save_results(result, output_dir):
    """Save test results to files."""
    example_name = result["example"]
    
    # Create output directory
    example_dir = output_dir / example_name.replace(".py", "")
    example_dir.mkdir(parents=True, exist_ok=True)
    
    # Save stdout
    if result["stdout"]:
        (example_dir / "stdout.txt").write_text(result["stdout"])
    
    # Save stderr
    if result["stderr"]:
        (example_dir / "stderr.txt").write_text(result["stderr"])
    
    # Save metadata
    metadata = {
        "example": example_name,
        "status": result["status"],
        "returncode": result["returncode"],
        "duration": result["duration"],
        "error": result["error"],
        "timestamp": datetime.now().isoformat()
    }
    (example_dir / "result.json").write_text(json.dumps(metadata, indent=2))


def main():
    """Run all examples concurrently and report results."""
    print("=== Observability Examples Concurrent Test Runner ===\n")
    
    # Setup
    output_dir = Path(".cache/tmp/example-test-results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find examples
    examples = find_examples()
    print(f"Found {len(examples)} examples to test")
    
    # Determine number of workers (leave some CPUs free)
    num_workers = max(1, multiprocessing.cpu_count() - 2)
    print(f"Running with {num_workers} parallel workers\n")
    
    # Test results
    results = {}
    failed_examples = []
    timeout_examples = []
    
    # Progress tracking
    completed = 0
    start_time = time.time()
    
    # Run examples concurrently
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        future_to_example = {}
        for example in examples:
            # Give async examples more time
            timeout = 20 if 'async' in example.name else 10
            future_to_example[executor.submit(run_example, example, timeout=timeout)] = example
        
        # Process completed tasks
        for future in as_completed(future_to_example):
            example = future_to_example[future]
            completed += 1
            
            try:
                result = future.result()
                results[result["example"]] = result
                
                # Save results immediately
                save_results(result, output_dir)
                
                # Update progress
                status_icon = {
                    "success": "✓",
                    "failed": "✗",
                    "timeout": "⏱",
                    "error": "⚠"
                }[result["status"]]
                
                print(f"[{completed}/{len(examples)}] {result['example']} {status_icon} ({result['duration']:.2f}s)")
                
                # Track failures
                if result["status"] == "failed":
                    failed_examples.append(result["example"])
                elif result["status"] == "timeout":
                    timeout_examples.append(result["example"])
                    
            except Exception as e:
                print(f"[{completed}/{len(examples)}] {example.name} ⚠ (executor error: {e})")
    
    # Total duration
    total_duration = time.time() - start_time
    
    # Summary report
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    total = len(examples)
    successful = sum(1 for r in results.values() if r["status"] == "success")
    failed = len(failed_examples)
    timed_out = len(timeout_examples)
    
    print(f"Total examples: {total}")
    print(f"Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"Failed: {failed}")
    print(f"Timed out: {timed_out}")
    print(f"Total time: {total_duration:.2f}s (vs ~{sum(r['duration'] for r in results.values()):.2f}s sequential)")
    print(f"Speedup: {sum(r['duration'] for r in results.values()) / total_duration:.1f}x")
    
    # Report failures
    if failed_examples:
        print("\nFAILED EXAMPLES:")
        for example in sorted(failed_examples):
            print(f"  - {example}")
            if example in results:
                stderr = results[example]["stderr"]
                if stderr:
                    # Show first line of error
                    first_line = stderr.strip().split('\n')[-1]
                    print(f"    Error: {first_line}")
    
    # Report timeouts
    if timeout_examples:
        print("\nTIMEOUT EXAMPLES:")
        for example in sorted(timeout_examples):
            print(f"  - {example}")
    
    # Save summary
    summary = {
        "total": total,
        "successful": successful,
        "failed": failed,
        "timed_out": timed_out,
        "failed_examples": sorted(failed_examples),
        "timeout_examples": sorted(timeout_examples),
        "total_duration": total_duration,
        "timestamp": datetime.now().isoformat()
    }
    
    summary_file = output_dir / "summary.json"
    summary_file.write_text(json.dumps(summary, indent=2))
    
    print(f"\nDetailed results saved to: {output_dir}")
    
    # Exit with error if any failures
    sys.exit(1 if (failed_examples or timeout_examples) else 0)


if __name__ == "__main__":
    main()