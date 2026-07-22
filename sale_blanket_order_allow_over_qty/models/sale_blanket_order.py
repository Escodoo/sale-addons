# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleBlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    allow_over_qty = fields.Boolean(
        string="Allow Exceeding Quantity",
        default=False,
        copy=False,
    )
