# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)

class PrintServerPrinter(models.Model):
    _name = 'print.server.printer'
    _description = 'Print Server Printer'
    _order = 'name'

    name = fields.Char(string='Printer Name', required=True, readonly=True)
    description = fields.Char(string='Description', readonly=True)
    status = fields.Selection([
        ('ready', 'Ready'),
        ('offline', 'Offline'),
        ('unknown', 'Unknown')
    ], string='Status', default='unknown', readonly=True)
    is_active = fields.Boolean(string='Active', default=True)
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Printer name must be unique!')
    ]

    @api.model
    def action_sync_printers(self):
        """Fetch printers from Print Server and update the list"""
        # Get Print Server URL from System Parameters
        config_param = self.env['ir.config_parameter'].sudo()
        base_url = config_param.get_param('sale_custom.print_server_url', 'http://print_server:5000')
        
        def try_sync(url):
            _logger.info("Syncing printers from %s", url)
            response = requests.get(f"{url}/api/printers", timeout=5)
            response.raise_for_status()
            return response.json()

        try:
            try:
                result = try_sync(base_url)
            except requests.exceptions.ConnectionError:
                # If failed and URL is localhost, try docker hostname
                if 'localhost' in base_url:
                    fallback_url = 'http://print_server:5000'
                    _logger.warning("Connection to %s failed. Retrying with fallback: %s", base_url, fallback_url)
                    result = try_sync(fallback_url)
                    # If successful, update config
                    config_param.set_param('sale_custom.print_server_url', fallback_url)
                    base_url = fallback_url
                else:
                    raise

            if result.get('success'):
                printers = result.get('printers', [])
                current_printer_names = []
                
                for p in printers:
                    name = p.get('name')
                    current_printer_names.append(name)
                    
                    # Check if printer exists
                    existing = self.search([('name', '=', name)], limit=1)
                    vals = {
                        'name': name,
                        'description': p.get('description') or p.get('make_model', 'N/A'),
                        'status': p.get('status', 'unknown'),
                        'is_active': True
                    }
                    
                    if existing:
                        existing.write(vals)
                    else:
                        self.create(vals)
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Sync Successful',
                        'message': f'Synced {len(printers)} printers from {base_url}',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise Exception(result.get('error', 'Unknown error'))
                
        except Exception as e:
            _logger.error("Failed to sync printers: %s", str(e))
            raise UserError(f"Failed to sync printers from {base_url}: {str(e)}\n\nCheck if Print Server is running.")

class PrintReportMapping(models.Model):
    _name = 'print.report.mapping'
    _description = 'Print Report Mapping'
    _rec_name = 'report_id'

    report_id = fields.Many2one('ir.actions.report', string='Report', required=True, domain="[('model', '=', 'nw.sale.order')]")
    printer_id = fields.Many2one('print.server.printer', string='Printer', required=True, domain="[('is_active', '=', True)]")
    description = fields.Char(string='Description')
    
    _sql_constraints = [
        ('report_uniq', 'unique (report_id)', 'This report is already mapped to a printer!')
    ]

    def action_test_print(self):
        """Send a test print job to the mapped printer"""
        self.ensure_one()
        
        try:
            # Get Print Server URL
            base_url = self.env['ir.config_parameter'].sudo().get_param('sale_custom.print_server_url', 'http://print_server:5000')
            
            # Create a simple PDF with text "Test Print: [Printer Name]"
            # For simplicity, we'll send a dummy base64 string or a simple text file if the server supports it
            # But our server expects PDF. Let's create a minimal PDF or just send a text message if we can.
            # Since we can't easily generate PDF here without a report, let's try to use the mapped report with a dummy ID if possible,
            # OR better, just send a "Test Connection" request to the printer if the API supports it.
            # Our current API expects PDF.
            
            # Alternative: Use a simple pre-generated "Test Page" PDF base64
            # Minimal PDF "Hello World" base64
            test_pdf_base64 = "JVBERi0xLjcKCjEgMCBvYmogICUgZW50cnkgcG9pbnQKPDwKICAvVHlwZSAvQ2F0YWxvZwogIC9QYWdlcyAyIDAgUgo+PgplbmRvYmoKCjIgMCBvYmogICUgcGFnZXMKPDwKICAvVHlwZSAvUGFnZXwKICAvTWVkaWFCb3ggWyAwIDAgMjAwIDIwMCBdCiAgL0NvdW50IDEKICAvS2lkcyBbIDMgMCBSIF0KPj4KZW5kb2JqCgozIDAgb2JqICB1cGFnZQo8PAogIC9UeXBlIC9QYWdlCiAgL1BhcmVudCAyIDAgUgogIC9SZXNvdXJjZXMgPDwKICAgIC9Gb250IDw8CiAgICAgIC9GMSA0IDAgUgogICAgPj4KICA+PgogIC9Db250ZW50cyA1IDAgUgo+PgplbmRvYmoKCjQgMCBvYmogICUgb2JqZWN0Cjw8CiAgL1R5cGUgL0ZvbnQKICAvU3VidHlwZSAvVHlwZTEKICAvQmFzZUZvbnQgL1RpbWVzLVJvbWFuCj4+CmVuZG9iagoKNSAwIG9iYiAlIGNvbnRlbnRzCjw8CiAgL0xlbmd0aCA0NAo+PgpzdHJlYW0KQlQKNzAgNTAgVGQKL0YxIDEyIFRmCihIZWxsbywgV29ybGQhKSBUagpFVAplbmRzdHJlYW0KZW5kb2JqCgp4cmVmCjAgNgowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMTAgMDAwMDAgbiAKMDAwMDAwMDA2MCAwMDAwMCBuIAowMDAwMDAwMTU3IDAwMDAwIG4gCjAwMDAwMDAyNTUgMDAwMDAgbiAKMDAwMDAwMDM0NCAwMDAwMCBuIAp0cmFpbGVyCjw8CiAgL1NpemUgNgogIC9Sb290IDEgMCBSCj4+CnN0YXJ0eHJlZgo0MTMKJSVFT0YK"
            
            payload = {
                'printer': self.printer_id.name,
                'pdf_data': test_pdf_base64,
                'job_name': 'Test_Print_Page'
            }
            
            response = requests.post(
                f"{base_url}/api/print",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Test Print Sent',
                            'message': f"Sent test page to {self.printer_id.name}",
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    raise UserError(f"Print Server Error: {result.get('error')}")
            else:
                raise UserError(f"Connection Error: {response.status_code}")
                
        except Exception as e:
            raise UserError(f"Test Print Failed: {str(e)}")
