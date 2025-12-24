"""
Print Server Configuration
Manages settings for the print server including printer mappings and server configuration.
"""
import os
from pathlib import Path

# Server Configuration
HOST = os.getenv('PRINT_SERVER_HOST', '0.0.0.0')
PORT = int(os.getenv('PRINT_SERVER_PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Mock Mode - Set to True to test without physical printers
MOCK_MODE = os.getenv('MOCK_MODE', 'False').lower() == 'true'

# Printer Mappings
PRINTER_A_NAME = os.getenv('PRINTER_A_NAME', 'PrinterA')  # Dot Matrix
PRINTER_B_NAME = os.getenv('PRINTER_B_NAME', 'PrinterB')  # Thermal

# Printer Configuration
PRINTERS = {
    'PrinterA': {
        'name': PRINTER_A_NAME,
        'type': 'dot_matrix',
        'description': 'Dot Matrix Printer for Invoice/Delivery',
        'paper_size': 'A4'
    },
    'PrinterB': {
        'name': PRINTER_B_NAME,
        'type': 'thermal',
        'description': 'Thermal Printer for Invoice',
        'paper_size': '80mm'
    }
}

# Logging Configuration
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'print_jobs.log'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Mock Printer Output Directory
MOCK_OUTPUT_DIR = Path(__file__).parent / 'mock_output'
MOCK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Print Job Settings
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '2'))  # seconds
