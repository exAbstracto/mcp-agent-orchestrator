#!/usr/bin/env python3
"""
Platform Performance Benchmarking Script

This script measures key performance metrics to validate our platform
capability analysis for Cursor vs Claude Code.
"""

import time
import psutil
import json
import subprocess
import sys
import os
from typing import Dict, List, Any
from pathlib import Path


class PlatformBenchmark:
    """Benchmark class for measuring platform performance metrics."""
    
    def __init__(self):
        self.results: Dict[str, Any] = {
            "timestamp": time.time(),
            "system_info": self._get_system_info(),
            "benchmarks": {}
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmark context."""
        return {
            "platform": sys.platform,
            "python_version": sys.version,
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "disk_usage": psutil.disk_usage('/').total
        }
    
    def benchmark_file_operations(self, num_files: int = 100) -> Dict[str, float]:
        """Benchmark file operation performance."""
        test_dir = Path("/tmp/mcp_benchmark")
        test_dir.mkdir(exist_ok=True)
        
        # File creation benchmark
        start_time = time.time()
        for i in range(num_files):
            test_file = test_dir / f"test_file_{i}.txt"
            test_file.write_text(f"Test content for file {i}")
        create_time = time.time() - start_time
        
        # File reading benchmark
        start_time = time.time()
        for i in range(num_files):
            test_file = test_dir / f"test_file_{i}.txt"
            content = test_file.read_text()
        read_time = time.time() - start_time
        
        # File deletion benchmark
        start_time = time.time()
        for i in range(num_files):
            test_file = test_dir / f"test_file_{i}.txt"
            test_file.unlink()
        delete_time = time.time() - start_time
        
        # Cleanup
        test_dir.rmdir()
        
        return {
            "file_creation_time": create_time,
            "file_reading_time": read_time,
            "file_deletion_time": delete_time,
            "total_time": create_time + read_time + delete_time,
            "files_per_second": num_files / (create_time + read_time + delete_time)
        }
    
    def benchmark_memory_usage(self) -> Dict[str, float]:
        """Benchmark current memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": process.memory_percent()
        }
    
    def benchmark_cpu_usage(self, duration: int = 5) -> Dict[str, float]:
        """Benchmark CPU usage over time."""
        process = psutil.Process()
        
        # Initial measurement
        cpu_before = process.cpu_percent()
        system_cpu_before = psutil.cpu_percent()
        
        # Wait and measure
        time.sleep(duration)
        
        cpu_after = process.cpu_percent() or 0.0
        system_cpu_after = psutil.cpu_percent() or 0.0
        
        return {
            "process_cpu_percent": float(cpu_after),
            "system_cpu_percent": float(system_cpu_after),
            "cpu_count": float(psutil.cpu_count() or 1)
        }
    
    def benchmark_subprocess_creation(self, num_processes: int = 10) -> Dict[str, float]:
        """Benchmark subprocess creation and management."""
        start_time = time.time()
        
        processes = []
        for i in range(num_processes):
            proc = subprocess.Popen(['echo', f'test_{i}'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
            processes.append(proc)
        
        # Wait for all processes to complete
        for proc in processes:
            proc.wait()
        
        total_time = time.time() - start_time
        
        return {
            "subprocess_creation_time": total_time,
            "processes_per_second": num_processes / total_time,
            "average_time_per_process": total_time / num_processes
        }
    
    def benchmark_json_processing(self, data_size: int = 1000) -> Dict[str, float]:
        """Benchmark JSON serialization/deserialization."""
        # Create test data
        test_data = {
            "items": [
                {
                    "id": i,
                    "name": f"item_{i}",
                    "properties": {
                        "value": i * 2,
                        "enabled": i % 2 == 0,
                        "tags": [f"tag_{j}" for j in range(5)]
                    }
                }
                for i in range(data_size)
            ]
        }
        
        # Serialization benchmark
        start_time = time.time()
        json_str = json.dumps(test_data)
        serialize_time = time.time() - start_time
        
        # Deserialization benchmark
        start_time = time.time()
        parsed_data = json.loads(json_str)
        deserialize_time = time.time() - start_time
        
        return {
            "json_serialize_time": serialize_time,
            "json_deserialize_time": deserialize_time,
            "total_time": serialize_time + deserialize_time,
            "data_size_mb": len(json_str) / 1024 / 1024,
            "items_per_second": data_size / (serialize_time + deserialize_time)
        }
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmark tests."""
        print("🚀 Starting Platform Performance Benchmarks...")
        
        print("📁 Running file operations benchmark...")
        self.results["benchmarks"]["file_operations"] = self.benchmark_file_operations()
        
        print("💾 Running memory usage benchmark...")
        self.results["benchmarks"]["memory_usage"] = self.benchmark_memory_usage()
        
        print("⚡ Running CPU usage benchmark...")
        self.results["benchmarks"]["cpu_usage"] = self.benchmark_cpu_usage()
        
        print("🔄 Running subprocess creation benchmark...")
        self.results["benchmarks"]["subprocess"] = self.benchmark_subprocess_creation()
        
        print("📋 Running JSON processing benchmark...")
        self.results["benchmarks"]["json_processing"] = self.benchmark_json_processing()
        
        print("✅ All benchmarks completed!")
        return self.results
    
    def save_results(self, filename: str = "benchmark_results.json"):
        """Save benchmark results to file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"📊 Results saved to {filename}")
    
    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "="*60)
        print("  PLATFORM PERFORMANCE BENCHMARK SUMMARY")
        print("="*60)
        
        benchmarks = self.results["benchmarks"]
        
        print(f"\n💾 Memory Usage:")
        memory = benchmarks["memory_usage"]
        print(f"   RSS: {memory['rss_mb']:.2f} MB")
        print(f"   VMS: {memory['vms_mb']:.2f} MB") 
        print(f"   Percent: {memory['percent']:.2f}%")
        
        print(f"\n📁 File Operations (100 files):")
        files = benchmarks["file_operations"]
        print(f"   Total time: {files['total_time']:.3f}s")
        print(f"   Files/sec: {files['files_per_second']:.1f}")
        
        print(f"\n⚡ CPU Usage:")
        cpu = benchmarks["cpu_usage"]
        print(f"   Process: {cpu['process_cpu_percent']:.2f}%")
        print(f"   System: {cpu['system_cpu_percent']:.2f}%")
        
        print(f"\n🔄 Subprocess Performance (10 processes):")
        subprocess_bench = benchmarks["subprocess"]
        print(f"   Total time: {subprocess_bench['subprocess_creation_time']:.3f}s")
        print(f"   Processes/sec: {subprocess_bench['processes_per_second']:.1f}")
        
        print(f"\n📋 JSON Processing (1000 items):")
        json_bench = benchmarks["json_processing"]
        print(f"   Total time: {json_bench['total_time']:.3f}s")
        print(f"   Data size: {json_bench['data_size_mb']:.2f} MB")
        print(f"   Items/sec: {json_bench['items_per_second']:.1f}")


def main():
    """Main benchmark execution."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Platform Performance Benchmark Script")
        print("Usage: python3 platform-benchmarks.py [output_file.json]")
        print("Default output: benchmark_results.json")
        return
    
    benchmark = PlatformBenchmark()
    results = benchmark.run_all_benchmarks()
    
    # Determine output filename
    output_file = sys.argv[1] if len(sys.argv) > 1 else "benchmark_results.json"
    benchmark.save_results(output_file)
    
    # Print summary
    benchmark.print_summary()
    
    print(f"\n🎯 Benchmark Context:")
    print(f"   Platform: {results['system_info']['platform']}")
    print(f"   CPU Count: {results['system_info']['cpu_count']}")
    print(f"   Memory: {results['system_info']['memory_total'] / 1024 / 1024 / 1024:.1f} GB")


if __name__ == "__main__":
    main() 