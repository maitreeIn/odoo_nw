"""
Printer Factory
Auto-detects OS and returns the appropriate printer handler.
"""
import platform
from .base import BasePrinter
import config


def get_printer_handler() -> BasePrinter:
    """
    Factory function to get the appropriate printer handler based on OS.
    
    Returns:
        BasePrinter: Printer handler instance (Mock, Windows, or Linux)
        
    Raises:
        NotImplementedError: If OS is not supported
    """
    # Check if mock mode is enabled
    if config.MOCK_MODE:
        from .mock_printer import MockPrinter
        print("🧪 Using Mock Printer (MOCK_MODE=True)")
        return MockPrinter()
    
    # Detect OS and return appropriate handler
    os_type = platform.system()
    
    if os_type == 'Windows':
        from .windows_printer import WindowsPrinter
        print("🪟 Detected Windows - Using Windows Printer Handler")
        return WindowsPrinter()
    
    elif os_type == 'Linux':
        from .linux_printer import LinuxPrinter
        print("🐧 Detected Linux - Using CUPS Printer Handler")
        return LinuxPrinter()
    
    elif os_type == 'Darwin':  # macOS
        # macOS also uses CUPS
        from .linux_printer import LinuxPrinter
        print("🍎 Detected macOS - Using CUPS Printer Handler")
        return LinuxPrinter()
    
    else:
        raise NotImplementedError(
            f"Operating system '{os_type}' is not supported. "
            f"Supported: Windows, Linux, macOS. "
            f"You can enable MOCK_MODE=True for testing."
        )


# Export all printer classes
from .base import BasePrinter
from .mock_printer import MockPrinter

__all__ = [
    'get_printer_handler',
    'BasePrinter',
    'MockPrinter'
]
