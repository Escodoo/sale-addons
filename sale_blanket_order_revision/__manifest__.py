# Copyright 2025 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Blanket Order Revision",
    "category": "Sale",
    "version": "16.0.1.0.2",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/sale-addons",
    "depends": ["purchase_request_custom"],
    "data": [
        "wizard/sale_blanket_order_revision.xml",
        "views/sale_blanket_order.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [],
    "installable": True,
    "post_init_hook": "post_init_hook",
}
