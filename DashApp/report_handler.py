"""
Report Handler Module
Handles file operations for reading and processing report files
"""
import os
import glob
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

from config import Config

class ReportHandler:
    """Handle report file operations and metadata extraction"""
    
    def __init__(self):
        self.reports_dir = Path(Config.get_reports_path())
        self.supported_formats = Config.SUPPORTED_REPORT_FORMATS
        self.default_type = Config.DEFAULT_REPORT_TYPE
        self.last_data_files = {}  # Store data files from the latest report generation
    
    def get_data_files(self, structured_output=None) -> Dict[str, str]:
        """
        Get the data files from structured output or latest report generation
        
        Args:
            structured_output: AnalysisOutput object from report_agent
        
        Returns:
            Dictionary containing data file paths for interactive plotting
        """
        print(f"[ReportHandler] Getting data files...")
        
        if structured_output and hasattr(structured_output, 'data_files'):
            print(f"[ReportHandler] Using structured output data files")
            data_files = structured_output.data_files or {}
            print(f"[ReportHandler] Found {len(data_files)} data files: {list(data_files.keys())}")
            return data_files
        else:
            print(f"[ReportHandler] No structured output provided, using cached data files")
            print(f"[ReportHandler] Cached data files: {len(self.last_data_files)} files: {list(self.last_data_files.keys())}")
            return self.last_data_files.copy()
    
    def read_md_report(self, file_handle: str) -> Optional[str]:
        """
        Read markdown report from file handle/path
        
        Args:
            file_handle: File path or handle to the report
            
        Returns:
            Content of the markdown file or None if error
        """
        try:
            # Handle both absolute paths and relative filenames
            if os.path.isabs(file_handle):
                file_path = Path(file_handle)
            else:
                file_path = self.reports_dir / file_handle
            
            if not file_path.exists():
                print(f" Report file not found: {file_path}")
                return None
            
            if not file_path.suffix == '.md':
                print(f" File is not a markdown file: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                print(f" Successfully read report: {file_path.name}")
                return content
                
        except Exception as e:
            print(f" Error reading report file {file_handle}: {str(e)}")
            return None
    
    def validate_report_exists(self, file_path: str) -> bool:
        """
        Check if report file exists
        
        Args:
            file_path: Path to the report file
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            if os.path.isabs(file_path):
                path = Path(file_path)
            else:
                path = self.reports_dir / file_path
            
            return path.exists() and path.is_file()
            
        except Exception as e:
            print(f" Error validating report path {file_path}: {str(e)}")
            return False
    
    def extract_report_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from report filename and content
        
        Args:
            file_path: Path to the report file
            
        Returns:
            Dictionary containing report metadata
        """
        try:
            if os.path.isabs(file_path):
                path = Path(file_path)
            else:
                path = self.reports_dir / file_path
            
            if not path.exists():
                return {}
            
            # Extract information from filename
            filename = path.stem
            
            # Parse filename pattern: City_territory_report_type_date_time
            metadata = {
                'filename': path.name,
                'file_path': str(path),
                'file_size': path.stat().st_size,
                'created_time': datetime.fromtimestamp(path.stat().st_ctime),
                'modified_time': datetime.fromtimestamp(path.stat().st_mtime),
                'format': path.suffix[1:]  # Remove the dot
            }
            
            # Try to parse structured filename
            # Expected format: City_territory_report_type_YYYYMMDD_HHMMSS
            parts = filename.split('_')
            if len(parts) >= 4:
                metadata.update({
                    'city': parts[0],
                    'report_type': '_'.join(parts[1:-2]) if len(parts) > 4 else parts[1],
                    'date_part': parts[-2] if len(parts) >= 2 else None,
                    'time_part': parts[-1] if len(parts) >= 1 else None
                })
            
            # Try to parse date and time from filename
            if 'date_part' in metadata and 'time_part' in metadata:
                try:
                    date_str = metadata['date_part']
                    time_str = metadata['time_part']
                    if len(date_str) == 8 and len(time_str) == 6:  # YYYYMMDD_HHMMSS
                        datetime_str = f"{date_str}_{time_str}"
                        parsed_datetime = datetime.strptime(datetime_str, "%Y%m%d_%H%M%S")
                        metadata['parsed_datetime'] = parsed_datetime
                except ValueError:
                    pass  # Ignore parsing errors
            
            return metadata
            
        except Exception as e:
            print(f" Error extracting metadata from {file_path}: {str(e)}")
            return {}
    
    def list_available_reports(self, report_type: str = None) -> List[Dict[str, Any]]:
        """
        List all available reports with metadata
        
        Args:
            report_type: Filter by report type ('md' or 'html'), None for all
            
        Returns:
            List of dictionaries containing report information
        """
        reports = []
        
        try:
            if report_type and report_type in Config.REPORT_FILE_PATTERNS:
                pattern = Config.REPORT_FILE_PATTERNS[report_type]
            else:
                pattern = "*.*"
            
            # Get all files matching pattern
            file_pattern = str(self.reports_dir / pattern)
            files = glob.glob(file_pattern)
            
            for file_path in files:
                path = Path(file_path)
                if Config.is_valid_report_file(path.name):
                    metadata = self.extract_report_metadata(file_path)
                    if metadata:
                        reports.append(metadata)
            
            # Sort by creation time (newest first)
            reports.sort(key=lambda x: x.get('created_time', datetime.min), reverse=True)
            
            return reports
            
        except Exception as e:
            print(f" Error listing reports: {str(e)}")
            return []
    
    def get_latest_report(self, report_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Get the latest report file
        
        Args:
            report_type: Filter by report type ('md' or 'html'), None for default
            
        Returns:
            Dictionary containing latest report metadata or None
        """
        if report_type is None:
            report_type = self.default_type
        
        reports = self.list_available_reports(report_type)
        return reports[0] if reports else None
    
    def parse_file_handle_from_response(self, structured_output) -> Optional[str]:
        """
        Extract file handle from structured output
        
        Args:
            structured_output: AnalysisOutput object from report_agent
            
        Returns:
            File handle/path if found, None otherwise
        """
        print(f" [ReportHandler] Parsing file handle from structured output...")
        
        if structured_output is None:
            print(f" [ReportHandler] No structured output provided - report not found")
            return None
        
        if not hasattr(structured_output, 'report_file'):
            print(f" [ReportHandler] Structured output missing 'report_file' attribute - report not found")
            return None
        
        report_file = structured_output.report_file
        
        if not report_file:
            print(f" [ReportHandler] Empty report_file in structured output - report not found")
            return None
        
        print(f" [ReportHandler] Found report file: {report_file}")
        
        # Store data files for backward compatibility
        if hasattr(structured_output, 'data_files') and structured_output.data_files:
            self.last_data_files = structured_output.data_files
            print(f" [ReportHandler] Cached {len(self.last_data_files)} data files: {list(self.last_data_files.keys())}")
        else:
            self.last_data_files = {}
            print(f" [ReportHandler] No data files found in structured output")
        
        return report_file

# Global instance for easy import
report_handler = ReportHandler()