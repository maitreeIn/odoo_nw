"""
Base Printer Abstract Class
Defines the interface that all printer implementations must follow.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BasePrinter(ABC):
    """Abstract base class for printer implementations"""
    
    @abstractmethod
    def get_printers(self) -> List[Dict[str, Any]]:
        """
        Get list of available printers.
        
        Returns:
            List of dictionaries containing printer information:
            [
                {
                    'name': str,
                    'status': str,  # 'ready', 'offline', 'error'
                    'type': str,    # 'dot_matrix', 'thermal', etc.
                }
            ]
        """
        pass
    
    @abstractmethod
    def print_pdf(self, printer_name: str, pdf_data: bytes) -> str:
        """
        Send PDF to printer.
        
        Args:
            printer_name: Name of the printer to use
            pdf_data: PDF file content as bytes
            
        Returns:
            Job ID as string
            
        Raises:
            Exception: If printing fails
        """
        pass
    
    @abstractmethod
    def get_printer_status(self, printer_name: str) -> str:
        """
        Get printer status.
        
        Args:
            printer_name: Name of the printer
            
        Returns:
            Status string: 'ready', 'offline', 'error', 'not_found'
        """
        pass
    
    def validate_printer(self, printer_name: str) -> bool:
        """
        Validate if printer exists and is available.
        
        Args:
            printer_name: Name of the printer to validate
            
        Returns:
            True if printer is available, False otherwise
        """
        printers = self.get_printers()
        return any(p['name'] == printer_name for p in printers)
