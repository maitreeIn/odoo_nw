from odoo import models, fields, api


class Customer(models.Model):
    _name = "nw.customer"
    _description = "Customer Information"

    name = fields.Char(string="ชื่อ", required=True)
    last_name = fields.Char(string="นามสกุล", required=False)
    phone = fields.Char(string="เบอร์โทร")
    email = fields.Char(string="อีเมล")
    address = fields.Text(string="ที่อยู่")
    note = fields.Text(string="บันทึก")
    account_line_ids = fields.One2many(
        "nw.account.line", "customer_id", string="Payment Lines"
    )
    total_balance = fields.Float(
        string="ยอดค้างชำระ",
        compute="_compute_total_balance",
        store=True,  # บันทึกลงฐานข้อมูลเพื่อให้ค้นหาหรือ Group by ได้
    )

    @api.depends("account_line_ids.amount", "account_line_ids.transaction_type")
    def _compute_total_balance(self):
        for rec in self:
            balance = 0.0
            for line in rec.account_line_ids:
                if line.transaction_type == "credit":
                    balance += line.amount  # Credit = จ่ายเงินเข้ามา (บวก)
                elif line.transaction_type == "debit":
                    balance -= line.amount  # Debit = เป็นหนี้ (ลบ)
            if balance > 0:
                rec.total_balance = 0.0
            else:
                rec.total_balance = balance

    def action_clear_lines(self):
        """ล้างรายการทั้งหมดแล้วตั้งยอดยกมา"""
        for rec in self:
            # 1. เก็บยอดคงเหลือปัจจุบันไว้ก่อน
            current_balance = rec.total_balance

            # 2. ลบรายการเดิมทั้งหมดทิ้ง
            rec.account_line_ids.unlink()

            # 3. กำหนดประเภทรายการ (ถ้าติดลบ คือ หนี้/Debit, ถ้าบวก คือ จ่ายเกิน/Credit
            if current_balance < 0:
                trans_type = "debit"

                # 4. สร้างรายการใหม่ "ยอดยกมา"
                self.env["nw.account.line"].create(
                    {
                        "customer_id": rec.id,
                        "name": "ยอดยกมา",
                        "amount": abs(current_balance),
                        "transaction_type": trans_type,
                    }
                )


class NwAccountLine(models.Model):
    _name = "nw.account.line"
    _description = "NW Account Line"

    customer_id = fields.Many2one("nw.customer", string="Customer", ondelete="cascade")
    name = fields.Char(string="Description")
    amount = fields.Float(string="Unit Price")
    transaction_type = fields.Selection(
        [
            ("debit", "Debt (-)"),
            ("credit", "Payment (+)"),
        ],
        string="Transaction Type",
        required=True,
        default="credit",
        help="ระบุว่ารายการนี้เป็นหนี้ (-) หรือเงินที่ลูกค้าจ่าย (+)",
    )
