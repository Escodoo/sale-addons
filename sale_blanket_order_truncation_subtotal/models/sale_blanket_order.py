# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleBlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    truncate_subtotal = fields.Boolean(
        string="Truncated Subtotal",
        help="If checked, this blanket order's line subtotals are computed "
        "by truncating the extra decimals instead of rounding them, as "
        "required by the customer's sale condition.",
    )

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        self.truncate_subtotal = self.partner_id.truncate_subtotal
        return res
