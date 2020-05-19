# Copyright 2020 Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class SaleCommissionMakeInvoice(models.TransientModel):

    _inherit = 'sale.commission.make.invoice'

    def _default_settlements(self):
        return self.env.context.get('settlement_ids', [])

    settlements = fields.Many2many(
        comodel_name='sale.commission.settlement',
        relation="sale_commission_make_invoice_settlement_rel",
        column1='wizard_id', column2='settlement_id',
        domain="[('state', '=', 'settled'),('agent_type', 'in',['agent','supplier']),"
               "('company_id', '=', company_id)]",
        default=_default_settlements)

    @api.multi
    def button_create(self):
        self.ensure_one()
        if not self.settlements:
            self.settlements = self.env['sale.commission.settlement'].search([
                ('state', '=', 'settled'),
                ('agent_type', 'in', ['agent', 'supplier']),
                ('company_id', '=', self.journal.company_id.id)
            ])
        self.settlements.make_invoices(
            self.journal, self.product, date=self.date)
        # go to results
        if len(self.settlements):
            return {
                'name': _('Created Invoices'),
                'type': 'ir.actions.act_window',
                'views': [[False, 'list'], [False, 'form']],
                'res_model': 'account.invoice',
                'domain': [
                    ['id', 'in', [x.invoice.id for x in self.settlements]],
                ],
            }
        else:
            return {'type': 'ir.actions.act_window_close'}
