#!/usr/bin/env python3
import os
import sys
import re
import statistics
from collections import defaultdict
from typing import Dict, List, Tuple

class LogAnalyzer:
    def __init__(self, log_file_path: str = "app.log", output_file: str = "log_analysis.txt"):
        self.log_file_path = log_file_path
        self.function_times = defaultdict(list)
        self.analysis_file = output_file
        
    def parse_log_file(self) -> None:
        """Parse the log file and extract function execution times."""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
            print(f"Reading {len(lines)} lines from {self.log_file_path}...")
            
            i = 0
            functions_found = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Look for function execution details pattern
                execution_details_match = re.search(r'(\w+) - INFO - (\w+) execution details:', line)
                if execution_details_match:
                    module_name = execution_details_match.group(1)
                    function_name = execution_details_match.group(2)
                    
                    # Look for the timing information in the next few lines
                    j = i + 1
                    total_time = None
                    core_time = None
                    overhead_time = None
                    
                    while j < len(lines) and j < i + 10:  # Look within next 10 lines
                        timing_line = lines[j].strip()
                        
                        # Extract core function execution time
                        core_match = re.search(r'Core function execution:\s*(\d+\.?\d*)s', timing_line)
                        if core_match:
                            core_time = float(core_match.group(1))
                            
                        # Extract logging/validation overhead
                        overhead_match = re.search(r'Logging/validation overhead:\s*(\d+\.?\d*)s', timing_line)
                        if overhead_match:
                            overhead_time = float(overhead_match.group(1))
                            
                        # Extract total time
                        total_match = re.search(r'Total time:\s*(\d+\.?\d*)s', timing_line)
                        if total_match:
                            total_time = float(total_match.group(1))
                            break
                            
                        j += 1
                    
                    if total_time is not None:
                        self.function_times[f"{module_name}.{function_name}"].append({
                            'total_time': total_time,
                            'core_time': core_time,
                            'overhead_time': overhead_time,
                            'timestamp': line.split(' - ')[0]
                        })
                        functions_found += 1
                
                i += 1
            
            print(f"Found {functions_found} function executions across {len(self.function_times)} unique functions")
                
        except FileNotFoundError:
            print(f"Error: Log file not found: {self.log_file_path}")
            print("Make sure 'app.log' exists in the current directory.")
            sys.exit(1)
        except Exception as e:
            print(f"Error parsing log file: {e}")
            sys.exit(1)
    
    def calculate_statistics(self) -> List[Tuple[str, Dict]]:
        """Calculate statistics for each function and return sorted results."""
        results = []
        
        for function_name, executions in self.function_times.items():
            if not executions:
                continue
                
            total_times = [exec_data['total_time'] for exec_data in executions]
            core_times = [exec_data['core_time'] for exec_data in executions if exec_data['core_time'] is not None]
            overhead_times = [exec_data['overhead_time'] for exec_data in executions if exec_data['overhead_time'] is not None]
            
            stats = {
                'execution_count': len(executions),
                'total_time_sum': sum(total_times),
                'total_time_median': statistics.median(total_times),
                'total_time_min': min(total_times),
                'total_time_max': max(total_times),
                'core_time_median': statistics.median(core_times) if core_times else 0,
                'overhead_time_median': statistics.median(overhead_times) if overhead_times else 0,
                'first_execution': executions[0]['timestamp'],
                'last_execution': executions[-1]['timestamp']
            }
            
            results.append((function_name, stats))
        
        # Sort by median total time (descending - slowest first)
        results.sort(key=lambda x: x[1]['total_time_median'], reverse=True)
        return results
    
    def write_analysis(self, results: List[Tuple[str, Dict]]) -> None:
        """Write the analysis results to analysis file."""
        try:
            with open(self.analysis_file, 'w', encoding='utf-8') as file:
                file.write("=" * 80 + "\n")
                file.write("FUNCTION PERFORMANCE ANALYSIS\n")
                file.write("=" * 80 + "\n\n")
                
                file.write(f"Total unique functions analyzed: {len(results)}\n")
                file.write(f"Analysis generated from: {self.log_file_path}\n")
                file.write(f"Analysis generated at: {__import__('datetime').datetime.now()}\n\n")
                
                if not results:
                    file.write("No function execution data found.\n")
                    return
                
                # Summary section
                file.write("TOP 10 SLOWEST FUNCTIONS (by median execution time):\n")
                file.write("-" * 60 + "\n")
                for i, (func_name, stats) in enumerate(results[:10], 1):
                    file.write(f"{i:2d}. {func_name}: {stats['total_time_median']:.4f}s median ({stats['execution_count']} calls)\n")
                
                file.write("\nTOP 10 FASTEST FUNCTIONS (by median execution time):\n")
                file.write("-" * 60 + "\n")
                for i, (func_name, stats) in enumerate(results[-10:][::-1], 1):
                    file.write(f"{i:2d}. {func_name}: {stats['total_time_median']:.4f}s median ({stats['execution_count']} calls)\n")
                
                file.write("\nFUNCTIONS WITH MOST EXECUTIONS:\n")
                file.write("-" * 60 + "\n")
                execution_sorted = sorted(results, key=lambda x: x[1]['execution_count'], reverse=True)
                for i, (func_name, stats) in enumerate(execution_sorted[:10], 1):
                    file.write(f"{i:2d}. {func_name}: {stats['execution_count']} executions ({stats['total_time_median']:.4f}s median)\n")
                
                file.write("\nFUNCTIONS WITH HIGHEST TOTAL TIME SPENT:\n")
                file.write("-" * 60 + "\n")
                total_time_sorted = sorted(results, key=lambda x: x[1]['total_time_sum'], reverse=True)
                for i, (func_name, stats) in enumerate(total_time_sorted[:10], 1):
                    file.write(f"{i:2d}. {func_name}: {stats['total_time_sum']:.4f}s total ({stats['execution_count']} calls)\n")
                
                # Detailed section
                file.write("\n" + "=" * 80 + "\n")
                file.write("DETAILED FUNCTION ANALYSIS\n")
                file.write("=" * 80 + "\n\n")
                
                for func_name, stats in results:
                    file.write(f"Function: {func_name}\n")
                    file.write(f"  Execution Count: {stats['execution_count']}\n")
                    file.write(f"  Total Time Sum: {stats['total_time_sum']:.4f}s\n")
                    file.write(f"  Median Time: {stats['total_time_median']:.4f}s\n")
                    file.write(f"  Min Time: {stats['total_time_min']:.4f}s\n")
                    file.write(f"  Max Time: {stats['total_time_max']:.4f}s\n")
                    if stats['core_time_median'] > 0:
                        file.write(f"  Median Core Time: {stats['core_time_median']:.4f}s\n")
                        file.write(f"  Median Overhead: {stats['overhead_time_median']:.4f}s\n")
                        overhead_percentage = (stats['overhead_time_median'] / stats['total_time_median']) * 100
                        file.write(f"  Overhead %: {overhead_percentage:.2f}%\n")
                    file.write(f"  First Execution: {stats['first_execution']}\n")
                    file.write(f"  Last Execution: {stats['last_execution']}\n")
                    file.write("-" * 60 + "\n")
                
            print(f"Analysis complete! Results written to: {os.path.abspath(self.analysis_file)}")
            
        except Exception as e:
            print(f"Error writing analysis file: {e}")
            sys.exit(1)
    
    def print_summary(self, results: List[Tuple[str, Dict]]) -> None:
        """Print a summary to console."""
        if not results:
            print("No function execution data found in the log file.")
            return
            
        print(f"\n{'='*60}")
        print("LOG ANALYSIS SUMMARY")
        print(f"{'='*60}")
        print(f"Analyzed {len(self.function_times)} unique functions")
        print(f"Total function executions found: {sum(len(executions) for executions in self.function_times.values())}")
        
        if results:
            slowest_func, slowest_stats = results[0]
            fastest_func, fastest_stats = results[-1]
            most_called = max(results, key=lambda x: x[1]['execution_count'])
            highest_total = max(results, key=lambda x: x[1]['total_time_sum'])
            
            print(f"\nSlowest function: {slowest_func}")
            print(f"  Median time: {slowest_stats['total_time_median']:.4f}s")
            print(f"  Called {slowest_stats['execution_count']} times")
            
            print(f"\nFastest function: {fastest_func}")
            print(f"  Median time: {fastest_stats['total_time_median']:.4f}s")
            print(f"  Called {fastest_stats['execution_count']} times")
            
            print(f"\nMost called function: {most_called[0]}")
            print(f"  Called {most_called[1]['execution_count']} times")
            print(f"  Median time: {most_called[1]['total_time_median']:.4f}s")
            
            print(f"\nHighest total time: {highest_total[0]}")
            print(f"  Total time: {highest_total[1]['total_time_sum']:.4f}s")
            print(f"  Called {highest_total[1]['execution_count']} times")
    
    def analyze_log(self) -> None:
        """Main method to perform complete log analysis."""
        print(f"Starting log analysis...")
        print(f"Reading from: {os.path.abspath(self.log_file_path)}")
        print(f"Output will be saved to: {os.path.abspath(self.analysis_file)}")
        
        self.parse_log_file()
        
        if not self.function_times:
            print("No function execution data found in the log file.")
            print("Make sure the log file contains lines with 'execution details:' and timing information.")
            return
        
        results = self.calculate_statistics()
        self.write_analysis(results)
        self.print_summary(results)

def main():
    """Main function - analyzes app.log and saves to log_analysis.txt"""
    analyzer = LogAnalyzer()
    analyzer.analyze_log()

if __name__ == "__main__":
    main()