# Copyright 2020 Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    # route_id = fields.Many2one(
    #     'stock.location.route', string='Route',
    #     ondelete='restrict', readonly=True, track_visibility='onchange',
    #     states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    #     domain=[('sale_selectable', '=', True)], check_company=True)

    direct_sale = fields.Boolean(
        #related='route_id.direct_sale',
        store=True,
        string='Direct Sale',
    )
