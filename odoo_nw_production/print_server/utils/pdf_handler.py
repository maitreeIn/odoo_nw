"""
PDF Handler Utilities
Utilities for processing PDF files.
"""
import base64
from typing import Optional


def decode_base64_pdf(pdf_base64: str) -> bytes:
    """
    Decode base64-encoded PDF data.
    
    Args:
        pdf_base64: Base64-encoded PDF string
        
    Returns:
        PDF data as bytes
        
    Raises:
        ValueError: If decoding fails
    """
    try:
        return base64.b64decode(pdf_base64)
    except Exception as e:
        raise ValueError(f"Failed to decode base64 PDF: {e}")


def encode_pdf_to_base64(pdf_data: bytes) -> str:
    """
    Encode PDF data to base64 string.
    
    Args:
        pdf_data: PDF data as bytes
        
    Returns:
        Base64-encoded string
    """
    return base64.b64encode(pdf_data).decode('utf-8')


def validate_pdf(pdf_data: bytes) -> bool:
    """
    Validate if data is a valid PDF file.
    
    Args:
        pdf_data: PDF data to validate
        
    Returns:
        True if valid PDF, False otherwise
    """
    # Check PDF header
    if not pdf_data:
        return False
    
    # PDF files start with %PDF-
    return pdf_data.startswith(b'%PDF-')


def get_pdf_info(pdf_data: bytes) -> Optional[dict]:
    """
    Extract basic information from PDF.
    
    Args:
        pdf_data: PDF data as bytes
        
    Returns:
        Dictionary with PDF info or None if invalid
    """
    if not validate_pdf(pdf_data):
        return None
    
    try:
        # Extract PDF version from header
        header = pdf_data[:20].decode('latin-1')
        version = header.split('-')[1].split('\n')[0] if '-' in header else 'unknown'
        
        return {
            'valid': True,
            'version': version,
            'size': len(pdf_data),
            'size_kb': round(len(pdf_data) / 1024, 2)
        }
    except Exception:
        return {
            'valid': True,
            'version': 'unknown',
            'size': len(pdf_data),
            'size_kb': round(len(pdf_data) / 1024, 2)
        }
