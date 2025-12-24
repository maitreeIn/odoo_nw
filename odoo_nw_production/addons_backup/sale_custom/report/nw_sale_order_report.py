from odoo import models, api, fields


class ReportNwSaleOrder(models.AbstractModel):
    _name = "report.sale_custom.report_nw_sale_order"
    _description = "NW Sale Order Report Parsing"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["nw.sale.order"].browse(docids)

        order_pages = {}
        max_lines = 15

        for order in docs:
            lines = order.order_line_ids
            chunks = [lines[i : i + max_lines] for i in range(0, len(lines), max_lines)]
            if not chunks:
                chunks = [[]]

            pages_data = []

            # 1. กำหนดชุดที่จะพิมพ์ (ปกติมีแค่ ต้นฉบับ)
            print_sets = ["ต้นฉบับ"]

            # 2. ถ้า is_copy เป็น True ให้เพิ่ม "สำเนา" ต่อท้าย
            if order.is_copy:
                print_sets.append("สำเนา")

            # 3. วนลูปสร้างหน้ากระดาษตามชุดที่กำหนด (ต้นฉบับ -> สำเนา)
            for label in print_sets:
                for page_index, chunk in enumerate(chunks):
                    page_lines = []
                    for i, line in enumerate(chunk):
                        page_lines.append(
                            {
                                "seq": (page_index * max_lines) + i + 1,
                                "name": line.product_id.name,
                                "qty": line.quantity,
                                "unit": "หน่วย",
                                "price": "{:,.2f}".format(line.price),
                                "sub_total": "{:,.2f}".format(line.sub_total),
                            }
                        )

                    while len(page_lines) < max_lines:
                        page_lines.append(None)

                    pages_data.append(
                        {
                            "lines": page_lines,
                            "is_last": (page_index == len(chunks) - 1),
                            "page_no": page_index + 1,
                            "total_pages": len(chunks),
                            "copy_label": label,  # <--- ส่งค่าป้ายชื่อ (ต้นฉบับML/สำเนา) ไปที่ X
                        }
                    )

            order_pages[order.id] = pages_data

        current_dt = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        print_time = current_dt.strftime("%H:%M")

        return {
            "doc_ids": docids,
            "doc_model": "nw.sale.order",
            "docs": docs,
            "order_pages": order_pages,
            "print_time": print_time,
        }
