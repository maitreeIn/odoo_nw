from odoo import models, fields, api
from odoo.exceptions import ValidationError


class NwAccountPaymentWizard(models.TransientModel):
    _name = "nw.account.payment.wizard"
    _description = "Payment Wizard"

    # สร้าง Field ตามที่ต้องการ
    amount = fields.Float(string="จำนวนเงินที่ใช้หนี้", required=True)

    def action_confirm_payment(self):
        """ฟังก์ชันสำหรับปุ่มยืนยัน: สร้างรายการ Payment Line"""

        # 1. ดึง ID ของ Customer ที่เปิด Wizard นี้ขึ้นมา
        customer_id = self.env.context.get("active_id")

        if customer_id:
            # ดึง Object ลูกค้าออกมาเพื่อดูยอดหนี้
            customer = self.env["nw.customer"].browse(customer_id)
            if self.amount <= 0:
                raise ValidationError("ยอดเงินที่ชำระต้องมากกว่า 0")

            # คำนวณยอดหนี้ปัจจุบัน (เนื่องจากในโมเดล nw.customer ยอดหนี้ติดลบ เราจึงใช้ abs() แปลงเป็นบวก)
            current_debt = abs(customer.total_balance)

            # 2. ตรวจสอบเงื่อนไข: ถ้ายอดจ่าย มากกว่า ยอดหนี้ ให้ Error
            if self.amount > current_debt:
                raise ValidationError(
                    f"ไม่สามารถชำระเงินเกินยอดหนี้ได้\n"
                    f"ยอดหนี้คงเหลือ: {current_debt:,.2f}\n"
                    f"ยอดที่ระบุ: {self.amount:,.2f}"
                )

            # 3. สั่งสร้างข้อมูลลงในโมเดล nw.account.line (โค้ดเดิม)
            self.env["nw.account.line"].create(
                {
                    "customer_id": customer_id,
                    "name": "ชำระเงิน",
                    "amount": self.amount,
                    "transaction_type": "credit",
                }
            )

        return {"type": "ir.actions.act_window_close"}

    # def action_confirm_payment(self):
    #     """ ฟังก์ชันสำหรับปุ่มยืนยัน: สร้างรายการ Payment Line """

    #     # 1. ดึง ID ของ Customer ที่เปิด Wizard นี้ขึ้นมา (active_id)
    #     customer_id = self.env.context.get('active_id')

    #     if customer_id:
    #         # 2. สั่งสร้างข้อมูลลงในโมเดล nw.account.line
    #         self.env['nw.account.line'].create({
    #             'customer_id': customer_id,    # ผูกกับลูกค้าคนปัจจุบัน
    #             'name': 'ชำระเงิน',   # ใส่คำอธิบาย
    #             'amount': self.amount,         # ยอดเงินจากช่องที่กรอก
    #             'transaction_type': 'credit',  # type = credit (Payment +) ตามโจทย์
    #         })

    #     # 3. ปิดหน้าต่าง Wizard (เมื่อปิดแล้ว หน้าจอหลักมักจะ Refresh อัตโนมัติให้เห็นยอดใหม่)
    #     return {'type': 'ir.actions.act_window_close'}
