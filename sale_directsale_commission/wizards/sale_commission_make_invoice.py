# # Copyright 2020 Marcel Savegnago - Escodoo
# # License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# from odoo import api, fields, models, _
#
#
# class SaleDsCommissionMakeInvoice(models.TransientModel):
#
#     _inherit = 'sale.ds.commission.make.invoice'
#
#     journal = fields.Many2one(
#         comodel_name='account.journal', required=True,
#         domain="[('type', 'in', ['purchase','sale'])]")
#
#     # settlements = fields.Many2many(
#     #     comodel_name='sale.commission.settlement',
#     #     relation="sale_commission_make_invoice_settlement_rel",
#     #     column1='wizard_id', column2='settlement_id',
#     #     domain="[('state', '=', 'settled'),('agent_type', '=', 'agent'),('agent_type', '=', 'directsale'),"
#     #            "('company_id', '=', company_id)]")
