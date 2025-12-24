"""
Linux Printer Implementation
Uses CUPS (Common Unix Printing System) to interact with printers.
"""
from typing import List, Dict, Any
from datetime import datetime
from .base import BasePrinter

try:
    import cups
    CUPS_AVAILABLE = True
except ImportError:
    CUPS_AVAILABLE = False


class LinuxPrinter(BasePrinter):
    """Linux printer implementation using CUPS"""
    
    def __init__(self):
        if not CUPS_AVAILABLE:
            raise ImportError(
                "pycups not available. Install with: pip install pycups"
            )
        try:
            self.conn = cups.Connection()
            print("🖨️  Linux CUPS Printer Handler initialized")
        except Exception as e:
            raise Exception(f"Failed to connect to CUPS: {e}")
    
    def get_printers(self) -> List[Dict[str, Any]]:
        """Get list of CUPS printers"""
        printers = []
        
        try:
            cups_printers = self.conn.getPrinters()
            
            for name, printer_info in cups_printers.items():
                status = self._get_cups_status(printer_info)
                
                printers.append({
                    'name': name,
                    'status': status,
                    'type': printer_info.get('printer-type', 'unknown'),
                    'description': printer_info.get('printer-info', name),
                    'location': printer_info.get('printer-location', ''),
                    'make_model': printer_info.get('printer-make-and-model', '')
                })
        except Exception as e:
            print(f"❌ Error enumerating CUPS printers: {e}")
        
        return printers
    
    def print_pdf(self, printer_name: str, pdf_data: bytes) -> str:
        """
        Print PDF using CUPS.
        
        Args:
            printer_name: Name of the CUPS printer
            pdf_data: PDF file content
            
        Returns:
            CUPS job ID as string
        """
        import tempfile
        import os
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.pdf',
            prefix='odoo_print_'
        ) as tmp_file:
            tmp_file.write(pdf_data)
            tmp_path = tmp_file.name
        
        try:
            # Send print job to CUPS
            job_id = self.conn.printFile(
                printer_name,
                tmp_path,
                "Odoo Print Job",
                {}  # Options (can add paper size, orientation, etc.)
            )
            
            print(f"✓ CUPS Print Job: {job_id}")
            print(f"  Printer: {printer_name}")
            print(f"  File: {tmp_path}")
            print(f"  Size: {len(pdf_data):,} bytes")
            
            return str(job_id)
            
        except Exception as e:
            raise Exception(f"Failed to print via CUPS: {e}")
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def get_printer_status(self, printer_name: str) -> str:
        """Get CUPS printer status"""
        try:
            printers = self.conn.getPrinters()
            
            if printer_name not in printers:
                return 'not_found'
            
            printer_info = printers[printer_name]
            return self._get_cups_status(printer_info)
            
        except Exception as e:
            print(f"❌ Error getting printer status for {printer_name}: {e}")
            return 'error'
    
    def _get_cups_status(self, printer_info: dict) -> str:
        """
        Convert CUPS printer state to our status format.
        
        CUPS states:
        3 = idle (ready)
        4 = printing
        5 = stopped
        """
        state = printer_info.get('printer-state', 0)
        
        if state == 3:  # IPP_PRINTER_IDLE
            return 'ready'
        elif state == 4:  # IPP_PRINTER_PROCESSING
            return 'ready'  # Still accepting jobs
        elif state == 5:  # IPP_PRINTER_STOPPED
            return 'offline'
        else:
            return 'error'
    
    def get_job_status(self, job_id: int) -> dict:
        """
        Get status of a specific print job.
        
        Args:
            job_id: CUPS job ID
            
        Returns:
            Job information dictionary
        """
        try:
            jobs = self.conn.getJobs()
            if job_id in jobs:
                return jobs[job_id]
            return None
        except Exception as e:
            print(f"❌ Error getting job status: {e}")
            return None
    
    def cancel_job(self, job_id: int) -> bool:
        """
        Cancel a print job.
        
        Args:
            job_id: CUPS job ID
            
        Returns:
            True if cancelled successfully
        """
        try:
            self.conn.cancelJob(job_id)
            print(f"🗑️  Cancelled print job: {job_id}")
            return True
        except Exception as e:
            print(f"❌ Error cancelling job {job_id}: {e}")
            return False
