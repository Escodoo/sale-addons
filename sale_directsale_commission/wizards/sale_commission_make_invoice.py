# Copyright 2020 Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class SaleCommissionMakeSettle(models.TransientModel):

    _inherit = 'sale.commission.make.settle'

    def _default_settlements(self):
        return self.env.context.get('settlement_ids', [])

    settlements = fields.Many2many(
        comodel_name='sale.commission.settlement',
        relation="sale_commission_make_invoice_settlement_rel",
        column1='wizard_id', column2='settlement_id',
        domain="[('state', '=', 'settled'),('agent_type', 'in',['agent','supplier']),"
               "('company_id', '=', company_id)]",
        default=_default_settlements)
