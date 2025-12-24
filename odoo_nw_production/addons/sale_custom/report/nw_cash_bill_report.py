from odoo import models, api, fields


class ReportNwCashBill(models.AbstractModel):
    _name = "report.sale_custom.report_nw_cash_bill"
    _description = "NW Cash Bill Report Parsing"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["nw.sale.order"].browse(docids)

        order_pages = {}
        max_lines = 1000  # Thermal printer: allow many lines per page (effectively one long page)

        for order in docs:
            lines = order.order_line_ids
            # แบ่ง lines เป็นชุดๆ (กรณีเยอะมากๆ)
            chunks = [lines[i : i + max_lines] for i in range(0, len(lines), max_lines)]
            if not chunks:
                chunks = [[]]

            pages_data = []

            # 1. กำหนดชุดที่จะพิมพ์ (ต้นฉบับ / สำเนา)
            print_sets = ["ต้นฉบับ"]
            if order.is_copy:
                print_sets.append("สำเนา")

            # 2. วนลูปสร้างหน้ากระดาษตามชุดที่กำหนด
            for label in print_sets:
                for page_index, chunk in enumerate(chunks):
                    page_lines = []
                    for i, line in enumerate(chunk):
                        page_lines.append(
                            {
                                "seq": (page_index * max_lines) + i + 1,
                                "name": line.product_id.name,
                                "qty": line.quantity,
                                # รายงานบิลเงินสดเอาแค่ 3 คอลัมน์หลัก
                                "sub_total": "{:,.2f}".format(line.sub_total),
                            }
                        )

                    # ไม่ต้องเติมบรรทัดว่างสำหรับ Thermal Printer

                    pages_data.append(
                        {
                            "lines": page_lines,
                            "is_last": (page_index == len(chunks) - 1),
                            "page_no": page_index + 1,
                            "total_pages": len(chunks),
                            "copy_label": label,
                        }
                    )

            order_pages[order.id] = pages_data

        current_dt = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        print_time = current_dt.strftime("%H:%M")

        return {
            "doc_ids": docids,
            "doc_model": "nw.sale.order",
            "docs": docs,
            "order_pages": order_pages,  # ส่งข้อมูลที่จัดหน้าแล้วไปที่ XML
            "print_time": print_time,
        }
