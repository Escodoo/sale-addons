# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _check_exchausted_blanket_order_line(self):
        if self.blanket_order_id and self.blanket_order_id.allow_over_qty:
            return False
        return super()._check_exchausted_blanket_order_line()
