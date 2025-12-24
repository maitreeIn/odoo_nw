"""
Mock Printer Implementation
Used for testing without physical printers. Saves PDFs to disk instead of printing.
"""
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from .base import BasePrinter
import config


class MockPrinter(BasePrinter):
    """Mock printer that saves PDFs to disk for testing"""
    
    def __init__(self):
        self.output_dir = config.MOCK_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"🧪 Mock Printer initialized. Output directory: {self.output_dir}")
    
    def get_printers(self) -> List[Dict[str, Any]]:
        """Return mock printer list"""
        return [
            {
                'name': config.PRINTER_A_NAME,
                'status': 'ready',
                'type': 'dot_matrix',
                'description': 'Mock Dot Matrix Printer'
            },
            {
                'name': config.PRINTER_B_NAME,
                'status': 'ready',
                'type': 'thermal',
                'description': 'Mock Thermal Printer'
            }
        ]
    
    def print_pdf(self, printer_name: str, pdf_data: bytes) -> str:
        """
        Save PDF to disk instead of printing.
        
        Args:
            printer_name: Name of the printer (used in filename)
            pdf_data: PDF file content
            
        Returns:
            Job ID (timestamp-based)
        """
        # Generate job ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        job_id = f"mock_{timestamp}"
        
        # Create filename
        filename = f"{printer_name}_{timestamp}.pdf"
        filepath = self.output_dir / filename
        
        # Save PDF
        with open(filepath, 'wb') as f:
            f.write(pdf_data)
        
        # Log
        file_size = len(pdf_data)
        print(f"✓ Mock Print Job: {job_id}")
        print(f"  Printer: {printer_name}")
        print(f"  File: {filepath}")
        print(f"  Size: {file_size:,} bytes")
        
        return job_id
    
    def get_printer_status(self, printer_name: str) -> str:
        """Always return 'ready' for mock printers"""
        valid_printers = [config.PRINTER_A_NAME, config.PRINTER_B_NAME]
        if printer_name in valid_printers:
            return 'ready'
        return 'not_found'
    
    def list_print_jobs(self) -> List[Dict[str, Any]]:
        """
        List all saved print jobs (PDF files).
        
        Returns:
            List of print job information
        """
        jobs = []
        for pdf_file in sorted(self.output_dir.glob('*.pdf')):
            stat = pdf_file.stat()
            jobs.append({
                'filename': pdf_file.name,
                'path': str(pdf_file),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        return jobs
    
    def clear_print_jobs(self) -> int:
        """
        Clear all saved print jobs.
        
        Returns:
            Number of files deleted
        """
        count = 0
        for pdf_file in self.output_dir.glob('*.pdf'):
            pdf_file.unlink()
            count += 1
        print(f"🗑️  Cleared {count} mock print jobs")
        return count
