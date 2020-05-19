# Copyright 2020 Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    directsale = fields.Boolean(
        store=True,
        string='Direct Sale',
    )
