# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _state_from = ["draft", "sent", "sale"]
    _state_to = ["sent", "sale", "cancel"]

    def action_quotation_send(self):
        self.ensure_one()
        if self._check_and_request_tier("sent"):
            return True
        return super().action_quotation_send()

    def action_cancel(self):
        self.ensure_one()
        if self._check_and_request_tier("cancel"):
            return True
        return super().action_cancel()
