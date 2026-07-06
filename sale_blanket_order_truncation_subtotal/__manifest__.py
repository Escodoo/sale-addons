# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Blanket Order Truncation Subtotal",
    "summary": """
        Truncate (instead of round) the blanket order line subtotal for
        partners whose sale condition requires it""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA), Escodoo",
    "website": "https://github.com/Escodoo/sale-addons",
    "depends": [
        "sale_blanket_order",
        "truncation_base",
    ],
    "data": [
        "data/decimal_precision_data.xml",
        "views/res_company_views.xml",
        "views/sale_blanket_order_views.xml",
    ],
    "maintainers": ["CristianoMafraJunior"],
    "application": False,
    "installable": True,
}
