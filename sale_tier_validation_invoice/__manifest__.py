# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Tier Validation — Group before confirmation",
    "summary": "Tier approval by group before confirming sales orders.",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/sale-addons",
    "depends": [
        "sale_tier_validation",
    ],
    "data": [
        "views/tier_definition_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
}
