# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class SaleInvoicePlan(models.Model):

    _inherit = "sale.invoice.plan"

    def write(self, vals):
        for line in self:
            if line.invoiced:
                raise UserError(
                    _(
                        "This row already has an invoice created and therefore"
                        "cannot be edited."
                    )
                )
        return super(SaleInvoicePlan, self).write(vals)
