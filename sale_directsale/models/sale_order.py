# Copyright 2020 Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    # TODO: Don't work correctly when product invoice policy is Delivered Quantities.
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for record in self:
            for line in record.order_line:
                if line.directsale:
                    line.invoice_status = 'invoiced'
                    line.qty_to_invoice = 0
                    line.qty_invoiced = line.product_uom_qty
        return res
