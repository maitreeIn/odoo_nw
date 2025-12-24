from odoo import models, fields, api

class ProductBarcodeWizard(models.TransientModel):
    _name = 'nw.product.barcode.wizard'
    _description = 'Product Barcode Wizard'

    product_id = fields.Many2one('nw.product', string='Product', required=True)
    quantity = fields.Integer(string='Quantity', default=1, required=True)

    def action_print_barcode(self):
        return self.env.ref('sale_custom.action_report_product_barcode').report_action(self)
