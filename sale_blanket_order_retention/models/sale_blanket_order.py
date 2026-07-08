# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleBlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    escrow_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Escrow Account",
        check_company=True,
        domain="[('account_type', '=', 'asset_receivable'), "
        "('company_id', '=', company_id)]",
    )
    escrow_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Escrow Journal",
        check_company=True,
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
    )
