# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleBlanketOrderWizard(models.TransientModel):
    _inherit = "sale.blanket.order.wizard"

    def _prepare_so_line_vals(self, line):
        vals = super()._prepare_so_line_vals(line)
        analytic_account = line.blanket_line_id.analytic_account_id
        if analytic_account:
            vals["analytic_distribution"] = {analytic_account.id: 100}
        return vals
