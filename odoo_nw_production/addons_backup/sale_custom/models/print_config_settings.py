# -*- coding: utf-8 -*-
from odoo import models, fields

class PrintConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    print_server_url = fields.Char(config_parameter='sale_custom.print_server_url')
    printer_a_name = fields.Char(config_parameter='sale_custom.printer_a_name')
    printer_b_name = fields.Char(config_parameter='sale_custom.printer_b_name')
    print_server_enabled = fields.Boolean(config_parameter='sale_custom.print_server_enabled')
    x_print_server_status_display = fields.Text() # Dummy field for safety
