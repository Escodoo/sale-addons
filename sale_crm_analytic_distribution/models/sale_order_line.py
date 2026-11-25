# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def default_get(self, fields_list):
        context = {
            key: value
            for key, value in self.env.context.items()
            if key != "default_analytic_distribution"
        }
        self_without_leaked_default = self.with_env(self.env(context=context))
        return super(SaleOrderLine, self_without_leaked_default).default_get(
            fields_list
        )

    @api.depends("order_id.opportunity_id.analytic_account_id")
    def _compute_analytic_distribution(self):
        res = super()._compute_analytic_distribution()
        for line in self:
            account = line.order_id.opportunity_id.analytic_account_id
            if not line.analytic_distribution and account:
                line.analytic_distribution = {str(account.id): 100}
        return res
