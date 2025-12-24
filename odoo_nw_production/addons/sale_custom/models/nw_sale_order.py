from odoo import models, fields, api
from odoo.exceptions import UserError
import xlsxwriter
import io
import base64
import requests
import logging

_logger = logging.getLogger(__name__)


class NwSaleOrder(models.Model):
    _name = "nw.sale.order"
    _inherit = ["barcodes.barcode_events_mixin"]
    _description = "NW Sale Order"

    name = fields.Char(
        string="Order No.", required=True, copy=False, readonly=True, default="New"
    )
    customer_id = fields.Many2one(
        "nw.customer",
        string="Customer",
        ondelete="set null",
        default=lambda self: self.env.ref(
            "sale_custom.nw_customer_default", raise_if_not_found=False
        ),
    )
    order_date = fields.Date(string="Order Date", default=fields.Date.today)
    order_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("cancel", "Cancel"),
        ],
        string="Order Status",
        default="draft",
    )
    order_line_ids = fields.One2many(
        "nw.sale.order.line", "order_id", string="Order Lines"
    )
    is_add_sale_price = fields.Boolean("บวกราคาเพิ่ม")
    total = fields.Float(string="Total Amount", compute="_compute_total", store=True)
    payment_type = fields.Selection(
        [("cash", "จ่ายสด"), ("credit", "สินเชื่อ")], string="ประเภทการชำระ", default="cash"
    )

    is_copy = fields.Boolean(string="สำเนา", default=False)

    def on_barcode_scanned(self, barcode):
        _logger.info(f"Barcode Scanned: {barcode}")
        
        product = self.env['nw.product'].search([('barcode', '=', barcode)], limit=1)
        _logger.info(f"Product Found: {product}")
        
        if product:
            # Check if product already exists in lines
            existing_line = self.order_line_ids.filtered(lambda l: l.product_id == product)
            if existing_line:
                existing_line.quantity += 1
            else:
                # Use One2many command to add line dynamically (Command: 0 = CREATE)
                self.order_line_ids = [(0, 0, {
                    'product_id': product.id,
                    'quantity': 1,
                    'price': product.sale_price + product.add_price if self.is_add_sale_price else product.sale_price,
                })]
        else:
            return {
                'warning': {
                    'title': "ไม่พบสินค้า",
                    'message': f"ไม่พบสินค้าที่มีบาร์โค้ด: {barcode}",
                }
            }

    def action_confirm(self):
        for rec in self:
            rec.order_status = "confirm"
            # ถ้าเป็น "สินเชื่อ" (credit) ให้สร้างรายการตั้งหนี้ใน Customer
            if rec.payment_type == "credit" and rec.customer_id:
                self.env["nw.account.line"].create(
                    {
                        "customer_id": rec.customer_id.id,
                        "name": rec.name,  # ใช้ชื่อ SO เป็น Description
                        "amount": rec.total,  # ยอดเงินรวม
                        "transaction_type": "debit",  # ประเภท Debit (เป็นหนี้)
                    }
                )

    def action_cancel(self):
        for rec in self:
            # เช็คก่อนว่า "ถ้าเดิมสถานะเป็น Confirm" และ "เป็นสินเชื่อ" -> แสดงว่าเคยตั้งหนี้ไว้แล้ว
            # เราจึงต้องสร้างรายการ "Credit (ล้างหนี้)" ให้
            if (
                rec.order_status == "confirm"
                and rec.payment_type == "credit"
                and rec.customer_id
            ):
                self.env["nw.account.line"].create(
                    {
                        "customer_id": rec.customer_id.id,
                        "name": f"{rec.name} (Cancel)",  # ชื่อรายการต่อท้ายด้วย (Cancel)
                        "amount": rec.total,  # ยอดเงินเท่าเดิม
                        "transaction_type": "credit",  # ประเภท Credit (เพื่อไปหักลบกับ Debit เดิม)
                    }
                )

            # เปลี่ยนสถานะเป็น Cancel
            rec.order_status = "cancel"

    def action_draft(self):
        for rec in self:
            rec.order_status = "draft"

    @api.depends("order_line_ids.sub_total")
    def _compute_total(self):
        for order in self:
            order.total = sum(line.sub_total for line in order.order_line_ids)

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("nw.sale.order") or "/"
        return super(NwSaleOrder, self).create(vals)

    @api.onchange("is_add_sale_price")
    def _onchange_product_id(self):
        for obj in self:
            if obj.is_add_sale_price:
                for line in obj.order_line_ids:
                    line.price = line.product_id.sale_price + line.product_id.add_price
            else:
                for line in obj.order_line_ids:
                    line.price = line.product_id.sale_price

    @api.model
    def _cron_clear_weekly_orders(self, days=0):
        """
        ฟังก์ชันลบ Order
        - days: จำนวนวันที่ต้องการย้อนหลัง (ค่า Default 7 สำหรับ Cron Job เดิม)
        - clear_all: ถ้าเป็น True จะล้างตามเงื่อนไขพิเศษ
        """
        from datetime import timedelta

        # เรียกใช้ฟังก์ชัน action_clear_lines ของ customer (ตาม Code เดิมของคุณ)
        all_customers = self.env["nw.customer"].search([])
        if all_customers:
            all_customers.action_clear_lines()

        # กำหนด date_threshold
        # ถ้า clear_all=True หรือ days=0 ตามโจทย์ -> date_threshold จะเป็น "วันนี้"
        # คำสั่ง < date_threshold จะลบรายการที่เกิด "ก่อนวันนี้" (ไม่รวมวันนี้)
        target_days = days - 1
        date_threshold = fields.Date.today() - timedelta(days=target_days)

        # เงื่อนไขการค้นหา Order
        domain = [("order_status", "!=", "draft")]

        # เพิ่มเงื่อนไขวันที่
        domain.append(("order_date", "<", date_threshold))

        # ค้นหา Order ตามเงื่อนไข
        orders_to_clear = self.search(domain)

        for order in orders_to_clear:
            order.unlink()

    def action_download_excel_report(self):
        """ฟังก์ชันสร้างไฟล์ Excel รายการ Order ทั้งหมด"""

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("All Sales Report")

        # --- กำหนด Format ---
        # Format หัวตาราง
        header_format = workbook.add_format(
            {"bold": True, "align": "center", "bg_color": "#D3D3D3", "border": 1}
        )
        # Format หัวข้อใหญ่ (Title)
        title_format = workbook.add_format(
            {"bold": True, "font_size": 16, "align": "left"}
        )
        # Format ข้อมูล
        date_format = workbook.add_format({"num_format": "dd/mm/yyyy", "align": "left"})
        text_format = workbook.add_format({"align": "left"})
        number_format = workbook.add_format({"num_format": "#,##0.00"})
        # Format ผลรวมท้ายตาราง
        total_label_format = workbook.add_format({"bold": True, "align": "right"})
        total_value_format = workbook.add_format(
            {"bold": True, "num_format": "#,##0.00", "top": 1}
        )  # มีเส้นขีดบน

        # 1. เขียนหัวข้อใหญ่ "Sales report" (ที่บรรทัดแรก)
        sheet.merge_range("A1:D1", "Sales report", title_format)

        # 2. เขียนหัวตาราง (เลื่อนลงมาที่บรรทัดที่ 2 -> index 1)
        headers = [
            "Date",
            "Bill no.",
            "Item no.",
            "Item name",
            "Qty.",
            "Amount",
            "Customer name",
            "Type",
        ]
        for col, header in enumerate(headers):
            sheet.write(1, col, header, header_format)
            sheet.set_column(col, col, 15)  # ปรับความกว้าง

        # 3. ดึงข้อมูลและคำนวณผลรวม
        orders = self.search([], order="order_date desc")

        row = 2
        sum_qty = 0.0  # ตัวแปรเก็บผลรวม Qty
        sum_amount = 0.0  # ตัวแปรเก็บผลรวม Amount

        for order in orders:
            for line in order.order_line_ids:
                sheet.write(row, 0, order.order_date, date_format)
                sheet.write(row, 1, order.name or "", text_format)
                item_no = line.product_id.barcode or line.product_id.default_code or ""
                sheet.write(row, 2, item_no, text_format)
                sheet.write(row, 3, line.product_id.name or "", text_format)

                # เขียนค่า Qty และบวกเพิ่มในตัวแปรผลรวม
                sheet.write(row, 4, line.quantity, number_format)
                sum_qty += line.quantity

                # เขียนค่า Amount และบวกเพิ่มในตัวแปรผลรวม
                sheet.write(row, 5, line.sub_total, number_format)
                sum_amount += line.sub_total

                sheet.write(row, 6, order.customer_id.name or "", text_format)
                sheet.write(row, 7, order.payment_type or "", text_format)

                row += 1

        # 4. เขียนบรรทัดสรุปผลรวม (Total) ที่บรรทัดสุดท้าย
        sheet.write(row, 3, "Total", total_label_format)  # คำว่า Total อยู่ช่อง Item name
        sheet.write(row, 4, sum_qty, total_value_format)  # ผลรวม Qty
        sheet.write(row, 5, sum_amount, total_value_format)  # ผลรวม Amount

        workbook.close()
        output.seek(0)

        file_content = base64.b64encode(output.read())
        output.close()

        attachment = self.env["ir.attachment"].create(
            {
                "name": "Sales_Report.xlsx",
                "type": "binary",
                "datas": file_content,
                "res_model": "nw.sale.order",
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % attachment.id,
            "target": "self",
        }

    def action_print_to_printer_a(self):
        """Print invoice/delivery using mapped printer"""
        return self._send_to_print_server(
            report_name='sale_custom.report_nw_sale_order'
        )

    def action_print_to_printer_b(self):
        """Print invoice using mapped printer"""
        return self._send_to_print_server(
            report_name='sale_custom.report_nw_cash_bill'
        )

    def _send_to_print_server(self, report_name):
        """
        Generate PDF and send to Print Server using dynamic mapping
        
        Args:
            report_name: Odoo report name (e.g., 'sale_custom.report_nw_sale_order')
            
        Returns:
            Notification action
        """
        self.ensure_one()
        
        try:
            # 1. Find Printer Mapping
            report_action = self.env['ir.actions.report']._get_report_from_name(report_name)
            if not report_action:
                raise UserError(f"Report {report_name} not found")
                
            mapping = self.env['print.report.mapping'].search([
                ('report_id', '=', report_action.id)
            ], limit=1)
            
            if not mapping:
                raise UserError(
                    f"No printer mapped for report '{report_action.name}'.\n"
                    "Please configure in Print Configuration > Report Mappings."
                )
                
            printer_name = mapping.printer_id.name
            
            # 2. Get Print Server URL from config
            print_server_url = self.env['ir.config_parameter'].sudo().get_param(
                'sale_custom.print_server_url',
                default='http://print_server:5000'
            )
            
            # 3. Generate PDF
            pdf_content, _ = report_action._render_qweb_pdf([self.id])
            
            # 4. Encode PDF to base64
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # 5. Send to Print Server
            payload = {
                'printer': printer_name,
                'pdf_data': pdf_base64,
                'job_name': f"{self.name}_{report_action.name}"
            }
            
            response = requests.post(
                f"{print_server_url}/api/print",
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
                            'title': 'Print Job Sent',
                            'message': f"Sent to {printer_name} (Job ID: {result.get('job_id')})",
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    raise UserError(f"Print Server Error: {result.get('error')}")
            else:
                raise UserError(f"Connection Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            raise UserError(
                "ไม่สามารถเชื่อมต่อ Print Server ได้\n\n"
                "กรุณาตรวจสอบว่า Print Server ทำงานอยู่ที่: {}\n\n"
                "หากต้องการดาวน์โหลด PDF ให้ใช้เมนู Print ปกติ".format(print_server_url)
            )
        except requests.exceptions.Timeout:
            raise UserError("Print Server ไม่ตอบสนอง (Timeout)")
        except requests.exceptions.RequestException as e:
            _logger.error("Print Server request error: %s", str(e))
            raise UserError("เกิดข้อผิดพลาดในการส่งงานพิมพ์: {}".format(str(e)))
        except Exception as e:
            _logger.exception("Unexpected error in print server communication")
            raise UserError("เกิดข้อผิดพลาด: {}".format(str(e)))


class NwSaleOrderLine(models.Model):
    _name = "nw.sale.order.line"
    _description = "NW Sale Order Line"

    order_id = fields.Many2one("nw.sale.order", string="Sale Order", ondelete="cascade")
    product_id = fields.Many2one("nw.product", string="Product", ondelete="set null")
    barcode = fields.Char(string="Barcode", related="product_id.barcode", readonly=True)
    quantity = fields.Float(string="Quantity", default=1)
    price = fields.Float(string="Unit Price")
    sub_total = fields.Float(
        string="Sub Total", compute="_compute_sub_total", store=True
    )

    @api.depends("quantity", "price")
    def _compute_sub_total(self):
        for line in self:
            line.sub_total = line.quantity * line.price

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                if line.order_id.is_add_sale_price:
                    line.price = (
                        line.product_id.sale_price + line.product_id.add_price
                    ) or 0.0
                else:
                    line.price = line.product_id.sale_price or 0.0