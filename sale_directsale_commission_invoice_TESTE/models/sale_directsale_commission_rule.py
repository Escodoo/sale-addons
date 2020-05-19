# Copyright 2020 Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class SaleDirectsaleCommissionRule(models.Model):

    _name = 'sale.directsale.commission.rule'
    _description = 'Sale Directsale Commission Rule'  # TODO

    name = fields.Char()

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('activated', 'Activated'),
            ('canceled', 'Canceled'),
        ],
        default='draft',
        required=True,
        readonly=True,
        track_visibility='always'
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Supplier",
        required=True,
        index=True,
    )







