
from odoo import models, fields

class SaleCustom(models.Model):
    _name = 'sale.custom'
    _description = 'Sale'

    name = fields.Char(string='Order Name', required=True)
    customer = fields.Char(string='Customer')
    amount_total = fields.Float(string='Total Amount')
    date_order = fields.Date(string='Order Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft')

