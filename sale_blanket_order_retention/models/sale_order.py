# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    escrow_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Escrow Account",
        compute="_compute_escrow_fields",
        store=True,
        readonly=True,
    )
    escrow_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Escrow Journal",
        compute="_compute_escrow_fields",
        store=True,
        readonly=True,
    )

    @api.depends(
        "order_line.blanket_order_line.order_id.escrow_account_id",
        "order_line.blanket_order_line.order_id.escrow_journal_id",
    )
    def _compute_escrow_fields(self):
        for order in self:
            blanket_order = order.order_line.blanket_order_line.order_id[:1]
            order.escrow_account_id = blanket_order.escrow_account_id
            order.escrow_journal_id = blanket_order.escrow_journal_id
