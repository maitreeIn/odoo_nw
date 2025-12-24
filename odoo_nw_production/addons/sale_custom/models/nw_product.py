from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
from io import BytesIO
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics import renderPM


class NwProduct(models.Model):
    _name = "nw.product"
    _description = "NW Product"

    name = fields.Char(string="Name", required=True)
    sale_price = fields.Float(string="ราคาขาย")
    add_price = fields.Float(string="ราคาสำหรับบวกเพิ่ม")
    barcode = fields.Char(string="Barcode" , copy=False)
    barcode_image = fields.Binary(string="Barcode Image", compute="_compute_barcode_image")
    
    @api.depends('barcode')
    def _compute_barcode_image(self):
        for record in self:
            if record.barcode:
                try:
                    # Create barcode drawing (Code128 is standard)
                    drawing = createBarcodeDrawing('Code128', value=record.barcode, barHeight=50, humanReadable=True)
                    
                    # Render to PNG
                    buffer = BytesIO()
                    renderPM.drawToFile(drawing, buffer, 'PNG')
                    
                    # Save as base64
                    record.barcode_image = base64.b64encode(buffer.getvalue())
                except Exception:
                    # Fallback if generation fails (e.g. invalid chars)
                    record.barcode_image = False
            else:
                record.barcode_image = False
    default_code = fields.Char(string="Internal Reference")
    note = fields.Text(string="Note")
    image = fields.Binary(string="Image")
    category_id = fields.Many2one(
        "product.category", string="Product Category", ondelete="set null"
    )

    @api.model
    def create(self, vals):
        if vals.get('barcode'):
            self._check_barcode_unique_explicit(vals['barcode'])
        return super(NwProduct, self).create(vals)

    def write(self, vals):
        if 'barcode' in vals:
            for record in self:
                barcode = vals.get('barcode')
                if barcode:
                    self._check_barcode_unique_explicit(barcode, exclude_id=record.id)
        return super(NwProduct, self).write(vals)

    def _check_barcode_unique_explicit(self, barcode, exclude_id=None):
        domain = [('barcode', '=', barcode)]
        if exclude_id:
            domain.append(('id', '!=', exclude_id))
        
        # Use active_test=False to find archived records too
        existing = self.with_context(active_test=False).search(domain, limit=1)
        if existing:
            raise UserError(f"บาร์โค้ด '{barcode}' มีอยู่ในระบบแล้ว (ซ้ำกับสินค้า: {existing.name})")

    _sql_constraints = [
        (
            "nw_product_barcode_uniq_v2",  # Renamed again to be sure
            "unique(barcode)",
            "บาร์โค้ดนี้มีอยู่ในระบบแล้ว กรุณาตรวจสอบ!",
        ),
    ]
