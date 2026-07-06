# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("order_id.truncate_subtotal")
    def _compute_amount(self):
        res = super()._compute_amount()
        for line in self.filtered("order_id.truncate_subtotal"):
            raw_subtotal = (
                line.price_unit
                * (1 - (line.discount or 0.0) / 100.0)
                * line.product_uom_qty
            )
            price_subtotal = self.env["decimal.precision"].truncate(
                raw_subtotal, "Sale Order subtotal line", currency=line.currency_id
            )
            line.update(
                {
                    "price_subtotal": price_subtotal,
                    "price_total": price_subtotal + line.price_tax,
                }
            )
        return res
