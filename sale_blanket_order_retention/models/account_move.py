# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

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
    retention_invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Source Invoice (Retention)",
        copy=False,
        index=True,
    )
    retention_move_ids = fields.One2many(
        comodel_name="account.move",
        inverse_name="retention_invoice_id",
        string="Retention Entries",
    )
    retention_move_count = fields.Integer(
        compute="_compute_retention_move_count",
    )

    payment_state = fields.Selection(
        selection_add=[("payment_retained", "Payment Retained")],
        ondelete={"payment_retained": "set not_paid"},
    )

    @api.depends(
        "invoice_line_ids.sale_line_ids.order_id.escrow_account_id",
        "invoice_line_ids.sale_line_ids.order_id.escrow_journal_id",
    )
    def _compute_escrow_fields(self):
        for move in self:
            orders = move.invoice_line_ids.sale_line_ids.order_id
            move.escrow_account_id = orders[:1].escrow_account_id
            move.escrow_journal_id = orders[:1].escrow_journal_id

    @api.depends("retention_move_ids")
    def _compute_retention_move_count(self):
        for move in self:
            move.retention_move_count = len(move.retention_move_ids)

    @api.depends("retention_move_ids.line_ids.reconciled", "retention_move_ids.state")
    def _compute_payment_state(self):  # pylint: disable=missing-return
        super()._compute_payment_state()
        for move in self:
            if (
                move.payment_state
                in (
                    "paid",
                    "in_payment",
                )
                and move._has_pending_retention()
            ):
                move.payment_state = "payment_retained"

    def _has_pending_retention(self):
        self.ensure_one()
        escrow_lines = self.retention_move_ids.filtered(
            lambda m: m.state == "posted"
        ).line_ids.filtered(lambda line: line.debit > 0)
        return bool(escrow_lines.filtered(lambda line: not line.reconciled))

    def action_open_retention_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Escrow/Retention"),
            "res_model": "account.move.retention.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_move_id": self.id},
        }

    def action_view_retention_moves(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_journal_line"
        )
        moves = self.retention_move_ids
        action["domain"] = [("id", "in", moves.ids)]
        action["context"] = {"default_move_type": "entry"}
        if len(moves) == 1:
            form_view = [
                (self.env.ref("account.view_move_form").id, "form"),
            ]
            action["views"] = form_view + [
                (state, view)
                for state, view in action.get("views", [])
                if view != "form"
            ]
            action["res_id"] = moves.id
        return action
