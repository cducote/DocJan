#!/usr/bin/env python3
"""
Simple log viewer and monitor for Concatly services.
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import argparse


class LogViewer:
    """Interactive log viewer for Concatly services."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        if not self.log_dir.exists():
            print(f"❌ Log directory {self.log_dir} does not exist")
            sys.exit(1)
    
    def list_log_files(self):
        """List all available log files."""
        log_files = list(self.log_dir.glob("*.log"))
        if not log_files:
            print("📝 No log files found")
            return []
        
        print("\n📋 Available log files:")
        for i, log_file in enumerate(log_files, 1):
            size = log_file.stat().st_size
            modified = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"  {i}. {log_file.name} ({self._format_size(size)}, modified: {modified.strftime('%Y-%m-%d %H:%M:%S')})")
        
        return log_files
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def tail_log(self, log_file: Path, lines: int = 50):
        """Show last N lines of a log file."""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()
                
            if not file_lines:
                print("📄 Log file is empty")
                return
            
            print(f"\n📄 Last {min(lines, len(file_lines))} lines from {log_file.name}:")
            print("=" * 100)
            
            for line in file_lines[-lines:]:
                # Color code different log levels
                line = line.strip()
                if ' ERROR ' in line:
                    print(f"\033[91m{line}\033[0m")  # Red
                elif ' WARNING ' in line:
                    print(f"\033[93m{line}\033[0m")  # Yellow
                elif ' INFO ' in line:
                    print(f"\033[92m{line}\033[0m")  # Green
                elif ' DEBUG ' in line:
                    print(f"\033[96m{line}\033[0m")  # Cyan
                else:
                    print(line)
            
            print("=" * 100)
            
        except Exception as e:
            print(f"❌ Error reading {log_file}: {e}")
    
    def follow_log(self, log_file: Path):
        """Follow log file in real-time (like tail -f)."""
        print(f"\n👁️  Following {log_file.name} (Ctrl+C to stop)...")
        print("=" * 100)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                # Go to end of file
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    if line:
                        line = line.strip()
                        # Color code different log levels
                        if ' ERROR ' in line:
                            print(f"\033[91m{line}\033[0m")  # Red
                        elif ' WARNING ' in line:
                            print(f"\033[93m{line}\033[0m")  # Yellow
                        elif ' INFO ' in line:
                            print(f"\033[92m{line}\033[0m")  # Green
                        elif ' DEBUG ' in line:
                            print(f"\033[96m{line}\033[0m")  # Cyan
                        else:
                            print(line)
                    else:
                        time.sleep(0.1)
                        
        except KeyboardInterrupt:
            print("\n\n👋 Stopped following log file")
        except Exception as e:
            print(f"❌ Error following {log_file}: {e}")
    
    def search_logs(self, pattern: str, log_file: Path = None):
        """Search for pattern in log files."""
        files_to_search = [log_file] if log_file else list(self.log_dir.glob("*.log"))
        
        print(f"\n🔍 Searching for '{pattern}' in log files...")
        
        total_matches = 0
        for file_path in files_to_search:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                matches = []
                for i, line in enumerate(lines, 1):
                    if pattern.lower() in line.lower():
                        matches.append((i, line.strip()))
                
                if matches:
                    print(f"\n📄 {file_path.name} ({len(matches)} matches):")
                    for line_num, line in matches:
                        # Highlight the pattern
                        highlighted = line.replace(pattern, f"\033[93m{pattern}\033[0m")
                        print(f"  {line_num:4d}: {highlighted}")
                    total_matches += len(matches)
                    
            except Exception as e:
                print(f"❌ Error searching {file_path}: {e}")
        
        print(f"\n📊 Total matches: {total_matches}")
    
    def show_errors_only(self, log_file: Path = None):
        """Show only ERROR and CRITICAL log entries."""
        files_to_check = [log_file] if log_file else list(self.log_dir.glob("*.log"))
        
        print("\n🚨 Recent errors and critical issues:")
        print("=" * 100)
        
        total_errors = 0
        for file_path in files_to_check:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                errors = []
                for line in lines:
                    line = line.strip()
                    if ' ERROR ' in line or ' CRITICAL ' in line:
                        errors.append(line)
                
                if errors:
                    print(f"\n📄 {file_path.name} ({len(errors)} errors):")
                    for error in errors[-10:]:  # Show last 10 errors
                        print(f"\033[91m{error}\033[0m")  # Red
                    total_errors += len(errors)
                    
            except Exception as e:
                print(f"❌ Error reading {file_path}: {e}")
        
        if total_errors == 0:
            print("✅ No errors found in log files!")
        else:
            print(f"\n📊 Total errors: {total_errors}")
        
        print("=" * 100)


def main():
    parser = argparse.ArgumentParser(description="Concatly Log Viewer")
    parser.add_argument("--log-dir", default="logs", help="Log directory path")
    parser.add_argument("--tail", type=int, metavar="N", help="Show last N lines")
    parser.add_argument("--follow", action="store_true", help="Follow log file in real-time")
    parser.add_argument("--search", metavar="PATTERN", help="Search for pattern in logs")
    parser.add_argument("--errors", action="store_true", help="Show only errors")
    parser.add_argument("--file", metavar="FILENAME", help="Specify log file")
    
    args = parser.parse_args()
    
    viewer = LogViewer(args.log_dir)
    
    # Get target log file
    target_file = None
    if args.file:
        target_file = viewer.log_dir / args.file
        if not target_file.exists():
            print(f"❌ Log file {target_file} does not exist")
            sys.exit(1)
    
    # Execute requested action
    if args.errors:
        viewer.show_errors_only(target_file)
    elif args.search:
        viewer.search_logs(args.search, target_file)
    elif args.follow:
        if not target_file:
            log_files = viewer.list_log_files()
            if not log_files:
                sys.exit(1)
            # Default to main.log for following
            main_log = viewer.log_dir / "main.log"
            target_file = main_log if main_log.exists() else log_files[0]
        viewer.follow_log(target_file)
    elif args.tail:
        if not target_file:
            log_files = viewer.list_log_files()
            if not log_files:
                sys.exit(1)
            # Default to main.log for tailing
            main_log = viewer.log_dir / "main.log"
            target_file = main_log if main_log.exists() else log_files[0]
        viewer.tail_log(target_file, args.tail)
    else:
        # Interactive mode
        log_files = viewer.list_log_files()
        if not log_files:
            sys.exit(1)
        
        while True:
            print("\n🎛️  Concatly Log Viewer")
            print("1. View recent logs (tail)")
            print("2. Follow logs in real-time")
            print("3. Search logs")
            print("4. Show errors only")
            print("5. Refresh file list")
            print("6. Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                lines = input("Number of lines to show (default 50): ").strip()
                lines = int(lines) if lines.isdigit() else 50
                viewer.tail_log(log_files[0], lines)
            elif choice == "2":
                viewer.follow_log(log_files[0])
            elif choice == "3":
                pattern = input("Search pattern: ").strip()
                if pattern:
                    viewer.search_logs(pattern)
            elif choice == "4":
                viewer.show_errors_only()
            elif choice == "5":
                log_files = viewer.list_log_files()
            elif choice == "6":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")


if __name__ == "__main__":
    main()
