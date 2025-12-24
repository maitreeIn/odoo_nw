# -*- coding: utf-8 -*-
{
    "name": "Sale",
    "version": "15.0.1.0.0",
    "summary": "Custom Sale Main Menu",
    "category": "Sales",
    "depends": ["base", "product"],
    "data": [
        "data/nw_customer_data.xml",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "data/print_server_config.xml",  # Print Server configuration
        "security/sale_custom_security.xml",
        "security/ir.model.access.csv",
        "wizard/payment_wizard_views.xml",
        "data/cleanup_view.xml",
        "views/print_server_views.xml",  # New Print Server Views
        "views/sale_custom_menu.xml",  # 1. สร้าง Root Menu
        "views/nw_customer_views.xml",
        "views/nw_product_views.xml",
        "views/nw_sale_order_views.xml",  # 2. สร้าง menu_nw_sale_order_main ที่ไฟล์นี้
        "wizard/clear_order_wizard_views.xml",  # <--- 3. ย้ายมาไว้ตรงนี้ (เพื่อให้มองเห็นเมนูแม่จากข้อ 2)
        "report/nw_sale_order_report.xml",
        "report/nw_product_barcode_report.xml",
    ],
    "installable": True,
    "application": True,
}
