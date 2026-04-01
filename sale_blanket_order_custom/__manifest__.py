# Copyright 2023 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Blanket Order Custom",
    "summary": """
        Sale Blanket Order Custom""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/sale-addons",
    "depends": [
        "sale_blanket_order",
        "mis_builder_cash_flow_forecast_integration",
    ],
    "data": [
        "security/sale_blanket_order_product.xml",
        "security/sale_blanket_order_service.xml",
        "security/sale_blanket_order_sale_order_plan.xml",
        "security/ir.model.access.csv",
        "wizard/sale_create_order_plan_view.xml",
        "wizard/sale_make_planned_order_view.xml",
        "views/sale_blanket_order.xml",
        "views/sale_blanket_order_sale_order_plan.xml",
    ],
    "application": False,
    "installable": True,
}
