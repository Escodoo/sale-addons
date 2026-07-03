# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Blanket Order Allow Over Quantity",
    "summary": """
        Allow creating and confirming sale orders that exceed the blanket
        order's remaining quantity""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/sale-addons",
    "depends": [
        "sale_blanket_order",
    ],
    "data": [
        "views/sale_blanket_order.xml",
    ],
    "maintainers": ["CristianoMafraJunior"],
    "application": False,
    "installable": True,
}
