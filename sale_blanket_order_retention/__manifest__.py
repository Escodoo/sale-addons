# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Blanket Order Retention",
    "summary": """
        Payment Escrow/Retention on invoices generated from
        Blanket Orders (Sale Blanket Order)""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/sale-addons",
    "depends": [
        "sale_blanket_order",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/account_move_retention_wizard_views.xml",
        "views/sale_blanket_order_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
    ],
    "maintainers": ["CristianoMafraJunior"],
    "application": False,
    "installable": True,
}
