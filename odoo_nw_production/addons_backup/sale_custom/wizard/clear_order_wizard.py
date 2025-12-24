from odoo import models, fields, api


class NwClearOrderWizard(models.TransientModel):
    _name = "nw.clear.order.wizard"
    _description = "Clear Order Wizard"

    days = fields.Integer(
        string="จำนวนวัน (ย้อนหลัง)", default=7, help="ลบ Order ที่เก่ากว่าจำนวนวันที่ระบุ"
    )
    clear_all = fields.Boolean(string="Clear ทั้งหมด")

    def action_clear_orders(self):
        """ส่งค่าไปยังฟังก์ชันใน Model หลักเพื่อทำการลบ"""

        days_to_process = self.days
        if self.clear_all:
            days_to_process = 0

        self.env["nw.sale.order"]._cron_clear_weekly_orders(days=days_to_process)

        return {
            "type": "ir.actions.client",
            "tag": "reload",  # รีโหลดหน้าจอหลังจากลบเสร็จ
        }
