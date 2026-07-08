# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class SaleBlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    price_reduction_warning = fields.Text(
        compute="_compute_price_reduction_warning",
    )

    @api.depends("previous_blanket_order_id.line_ids.price_unit", "line_ids.price_unit")
    def _compute_price_reduction_warning(self):
        for order in self:
            previous = order.previous_blanket_order_id
            if not previous:
                order.price_reduction_warning = False
                continue

            previous_prices = {
                line.product_id.id: line.price_unit for line in previous.line_ids
            }
            reduced_lines = [
                _("%(product)s: %(old).2f → %(new).2f")
                % {
                    "product": line.product_id.display_name,
                    "old": previous_prices[line.product_id.id],
                    "new": line.price_unit,
                }
                for line in order.line_ids
                if line.product_id.id in previous_prices
                and line.price_unit < previous_prices[line.product_id.id]
            ]
            order.price_reduction_warning = (
                "\n".join(reduced_lines) if reduced_lines else False
            )
