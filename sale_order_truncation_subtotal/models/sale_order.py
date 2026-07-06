# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    truncate_subtotal = fields.Boolean(
        string="Truncated Subtotal",
        compute="_compute_truncate_subtotal",
        store=True,
        readonly=False,
        precompute=True,
        help="If checked, this order's line subtotals are computed by "
        "truncating the extra decimals instead of rounding them, as "
        "required by the customer's sale condition.",
    )

    @api.depends("partner_id")
    def _compute_truncate_subtotal(self):
        for order in self:
            order.truncate_subtotal = order.partner_id.truncate_subtotal
