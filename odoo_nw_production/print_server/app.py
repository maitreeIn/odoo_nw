# -*- coding: utf-8 -*-
"""
Print Server - Flask Application
Main application for handling print requests from Odoo.
"""
import sys
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from flask import Flask, request, jsonify
from datetime import datetime
import traceback

import config
from printers import get_printer_handler
from utils import decode_base64_pdf, validate_pdf, get_pdf_info, log_print_job, log_error, logger

# Initialize Flask app
app = Flask(__name__)

# Initialize printer handler (auto-detects OS)
init_error = None
try:
    printer_handler = get_printer_handler()
    logger.info("Print Server initialized successfully")
except Exception as e:
    init_error = str(e)
    logger.error("Failed to initialize printer handler: {}".format(e))
    printer_handler = None


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'mock_mode': config.MOCK_MODE,
        'printer_handler': printer_handler.__class__.__name__ if printer_handler else None,
        'init_error': init_error
    })


@app.route('/api/printers', methods=['GET'])
def get_printers():
    """
    Get list of available printers.
    
    Returns:
        JSON list of printers with their status
    """
    if not printer_handler:
        return jsonify({
            'success': False,
            'error': f'Printer handler not initialized: {init_error}'
        }), 200
    
    try:
        printers = printer_handler.get_printers()
        return jsonify({
            'success': True,
            'printers': printers,
            'count': len(printers)
        })
    except Exception as e:
        logger.error("Error getting printers: {}".format(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 200


@app.route('/api/print', methods=['POST'])
def print_document():
    """
    Print a PDF document.
    
    Expected JSON payload:
    {
        "printer": "PrinterA" | "PrinterB",
        "pdf_data": "base64_encoded_pdf",
        "report_type": "invoice_delivery" | "invoice",
        "order_id": "SO001" (optional)
    }
    
    Returns:
        JSON response with job_id and status
    """
    if not printer_handler:
        return jsonify({'error': 'Printer handler not initialized'}), 500
    
    try:
        # Parse request data
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        printer_name = data.get('printer')
        pdf_base64 = data.get('pdf_data')
        report_type = data.get('report_type', 'unknown')
        order_id = data.get('order_id', 'unknown')
        
        # Validate required fields
        if not printer_name:
            return jsonify({'error': 'Missing required field: printer'}), 400
        if not pdf_base64:
            return jsonify({'error': 'Missing required field: pdf_data'}), 400
        
        # Map printer name to actual printer
        printer_mapping = {
            'PrinterA': config.PRINTER_A_NAME,
            'PrinterB': config.PRINTER_B_NAME
        }
        actual_printer_name = printer_mapping.get(printer_name, printer_name)
        
        # Decode PDF
        try:
            pdf_data = decode_base64_pdf(pdf_base64)
        except Exception as e:
            return jsonify({'error': 'Invalid PDF data: {}'.format(e)}), 400
        
        # Validate PDF
        if not validate_pdf(pdf_data):
            return jsonify({'error': 'Invalid PDF file'}), 400
        
        # Get PDF info
        pdf_info = get_pdf_info(pdf_data)
        
        # Validate printer exists
        if not printer_handler.validate_printer(actual_printer_name):
            return jsonify({
                'error': 'Printer not found: {}'.format(actual_printer_name),
                'available_printers': [p['name'] for p in printer_handler.get_printers()]
            }), 404
        
        # Check printer status
        status = printer_handler.get_printer_status(actual_printer_name)
        if status not in ['ready']:
            logger.warning("Printer {} status: {}".format(actual_printer_name, status))
        
        # Send to printer
        job_id = printer_handler.print_pdf(actual_printer_name, pdf_data)
        
        # Log successful print job
        job_info = {
            'job_id': job_id,
            'printer': actual_printer_name,
            'report_type': report_type,
            'order_id': order_id,
            'size_kb': pdf_info['size_kb']
        }
        log_print_job(logger, job_info)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'printer': actual_printer_name,
            'printer_alias': printer_name,
            'report_type': report_type,
            'order_id': order_id,
            'pdf_info': pdf_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        # Log error
        error_info = {
            'printer': data.get('printer', 'unknown'),
            'error': str(e),
            'order_id': data.get('order_id', 'unknown')
        }
        log_error(logger, error_info)
        
        logger.error("Print error: {}".format(traceback.format_exc()))
        
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/status/<job_id>', methods=['GET'])
def get_print_status(job_id):
    """
    Get status of a print job.
    
    Args:
        job_id: Print job ID
        
    Returns:
        JSON response with job status
    """
    # For mock and Windows printers, we don't track job status
    # For Linux/CUPS, we could query the job status
    
    return jsonify({
        'job_id': job_id,
        'status': 'completed',
        'message': 'Job status tracking not implemented for this printer type'
    })


@app.route('/api/mock/jobs', methods=['GET'])
def list_mock_jobs():
    """
    List all mock print jobs (only available in mock mode).
    
    Returns:
        JSON list of saved PDF files
    """
    if not config.MOCK_MODE:
        return jsonify({'error': 'Only available in mock mode'}), 403
    
    try:
        from printers.mock_printer import MockPrinter
        if isinstance(printer_handler, MockPrinter):
            jobs = printer_handler.list_print_jobs()
            return jsonify({
                'success': True,
                'jobs': jobs,
                'count': len(jobs)
            })
        else:
            return jsonify({'error': 'Not using mock printer'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/mock/clear', methods=['POST'])
def clear_mock_jobs():
    """
    Clear all mock print jobs (only available in mock mode).
    
    Returns:
        JSON response with number of jobs cleared
    """
    if not config.MOCK_MODE:
        return jsonify({'error': 'Only available in mock mode'}), 403
    
    try:
        from printers.mock_printer import MockPrinter
        if isinstance(printer_handler, MockPrinter):
            count = printer_handler.clear_print_jobs()
            return jsonify({
                'success': True,
                'cleared': count
            })
        else:
            return jsonify({'error': 'Not using mock printer'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error("Internal server error: {}".format(error))
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🖨️  Print Server Starting")
    print("=" * 60)
    print("Host: {}:{}".format(config.HOST, config.PORT))
    print("Mock Mode: {}".format(config.MOCK_MODE))
    print("Printer A: {} (Dot Matrix)".format(config.PRINTER_A_NAME))
    print("Printer B: {} (Thermal)".format(config.PRINTER_B_NAME))
    print("Log File: {}".format(config.LOG_FILE))
    if config.MOCK_MODE:
        print("Mock Output: {}".format(config.MOCK_OUTPUT_DIR))
    print("=" * 60)
    print("\nAPI Endpoints:")
    print("  GET  /api/health         - Health check")
    print("  GET  /api/printers       - List printers")
    print("  POST /api/print          - Print document")
    print("  GET  /api/status/<id>    - Get job status")
    if config.MOCK_MODE:
        print("  GET  /api/mock/jobs      - List mock jobs")
        print("  POST /api/mock/clear     - Clear mock jobs")
    print("=" * 60)
    print()
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
