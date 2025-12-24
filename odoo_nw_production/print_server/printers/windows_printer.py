"""
Windows Printer Implementation
Uses win32print to interact with Windows Print Spooler.
"""
import tempfile
import os
from typing import List, Dict, Any
from datetime import datetime
from .base import BasePrinter

try:
    import win32print
    import win32api
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False


class WindowsPrinter(BasePrinter):
    """Windows printer implementation using win32print"""
    
    def __init__(self):
        if not WINDOWS_AVAILABLE:
            raise ImportError(
                "win32print not available. Install with: pip install pywin32"
            )
        print("🖨️  Windows Printer Handler initialized")
    
    def get_printers(self) -> List[Dict[str, Any]]:
        """Get list of Windows printers"""
        printers = []
        
        try:
            # Enumerate local and network printers
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            printer_list = win32print.EnumPrinters(flags)
            
            for printer_info in printer_list:
                printer_name = printer_info[2]  # Printer name is at index 2
                status = self.get_printer_status(printer_name)
                
                printers.append({
                    'name': printer_name,
                    'status': status,
                    'type': 'unknown',  # Windows doesn't expose printer type easily
                    'description': printer_info[1] or printer_name  # Description at index 1
                })
        except Exception as e:
            print(f"❌ Error enumerating printers: {e}")
        
        return printers
    
    def print_pdf(self, printer_name: str, pdf_data: bytes) -> str:
        """
        Print PDF on Windows using multiple fallback methods.
        
        1. Try using SumatraPDF (best compatibility)
        2. Fall back to ShellExecute (requires default PDF reader)
        3. Fall back to RAW printing (limited printer support)
        """
        # Generate job ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        job_id = f"win_{timestamp}"
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.pdf',
            prefix='odoo_print_'
        ) as tmp_file:
            tmp_file.write(pdf_data)
            tmp_path = tmp_file.name
        
        try:
            # Method 1: Try SumatraPDF (best for silent printing)
            sumatra_paths = [
                r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
                r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\SumatraPDF\SumatraPDF.exe")
            ]
            
            for sumatra_path in sumatra_paths:
                if os.path.exists(sumatra_path):
                    try:
                        import subprocess
                        subprocess.run([
                            sumatra_path,
                            "-print-to", printer_name,
                            "-silent",
                            tmp_path
                        ], check=True, timeout=30)
                        
                        print(f"✓ Windows Print Job (SumatraPDF): {job_id}")
                        print(f"  Printer: {printer_name}")
                        print(f"  File: {tmp_path}")
                        print(f"  Size: {len(pdf_data):,} bytes")
                        
                        # Don't delete temp file immediately
                        return job_id
                    except Exception as e:
                        print(f"  SumatraPDF failed: {e}")
                        break
            
            # Method 2: Try ShellExecute (requires default PDF reader)
            try:
                win32api.ShellExecute(
                    0,
                    "print",
                    tmp_path,
                    f'/d:"{printer_name}"',
                    ".",
                    0  # SW_HIDE
                )
                
                print(f"✓ Windows Print Job (ShellExecute): {job_id}")
                print(f"  Printer: {printer_name}")
                print(f"  File: {tmp_path}")
                print(f"  Size: {len(pdf_data):,} bytes")
                
                return job_id
                
            except Exception as e:
                print(f"  ShellExecute failed: {e}")
                
                # Method 3: Try RAW printing (limited support)
                try:
                    # Delete temp file before trying RAW
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    
                    h_printer = win32print.OpenPrinter(printer_name)
                    
                    try:
                        job_info = ("Odoo Print Job", None, "RAW")
                        job_id_win = win32print.StartDocPrinter(h_printer, 1, job_info)
                        
                        try:
                            win32print.StartPagePrinter(h_printer)
                            win32print.WritePrinter(h_printer, pdf_data)
                            win32print.EndPagePrinter(h_printer)
                            
                            print(f"✓ Windows Print Job (RAW): {job_id}")
                            print(f"  Printer: {printer_name}")
                            print(f"  Job ID: {job_id_win}")
                            print(f"  Size: {len(pdf_data):,} bytes")
                            
                            return job_id
                            
                        finally:
                            win32print.EndDocPrinter(h_printer)
                    finally:
                        win32print.ClosePrinter(h_printer)
                        
                except Exception as raw_error:
                    raise Exception(
                        f"All print methods failed. "
                        f"Please install SumatraPDF from https://www.sumatrapdfreader.org/ "
                        f"or ensure a PDF reader is set as default. "
                        f"Last error: {raw_error}"
                    )
                    
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            raise Exception(f"Failed to print: {e}")
    
    def get_printer_status(self, printer_name: str) -> str:
        """Get Windows printer status"""
        try:
            handle = win32print.OpenPrinter(printer_name)
            printer_info = win32print.GetPrinter(handle, 2)
            win32print.ClosePrinter(handle)
            
            # Check printer status
            status = printer_info['Status']
            attributes = printer_info['Attributes']
            
            # Status codes from Windows
            if status == 0:
                # Check if printer is offline
                if attributes & win32print.PRINTER_ATTRIBUTE_WORK_OFFLINE:
                    return 'offline'
                return 'ready'
            else:
                return 'error'
                
        except Exception as e:
            print(f"❌ Error getting printer status for {printer_name}: {e}")
            return 'not_found'
    
    def get_default_printer(self) -> str:
        """Get the default Windows printer"""
        try:
            return win32print.GetDefaultPrinter()
        except Exception:
            return None
