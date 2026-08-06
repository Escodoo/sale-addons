# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveRetentionWizard(models.TransientModel):
    _name = "account.move.retention.wizard"
    _description = "Invoice Escrow/Retention"

    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
        required=True,
        readonly=True,
    )
    company_id = fields.Many2one(related="move_id.company_id")
    currency_id = fields.Many2one(related="move_id.currency_id")
    move_escrow_account_id = fields.Many2one(
        related="move_id.escrow_account_id", string="Invoice Escrow Account"
    )
    move_escrow_journal_id = fields.Many2one(
        related="move_id.escrow_journal_id", string="Invoice Escrow Journal"
    )
    date = fields.Date(
        required=True,
        default=fields.Date.context_today,
    )
    amount = fields.Monetary(required=True)
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Escrow Journal",
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
    )
    date_due = fields.Date(string="Due Date")
    escrow_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Escrow Account",
        domain="[('account_type', '=', 'asset_receivable'), "
        "('company_id', '=', company_id)]",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        move_id = res.get("move_id") or self.env.context.get("default_move_id")
        move = self.env["account.move"].browse(move_id)
        if move:
            res["escrow_account_id"] = move.escrow_account_id.id
            res["journal_id"] = (move.escrow_journal_id or move.journal_id).id
        return res

    def _get_open_receivable_lines(self):
        self.ensure_one()
        return self.move_id.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
            and not line.reconciled
        )

    def action_confirm(self):
        self.ensure_one()
        if self.currency_id.is_zero(self.amount) or self.amount < 0:
            raise UserError(_("The retention amount must be greater than zero."))
        if not self.escrow_account_id:
            raise UserError(_("Please set the Escrow Account."))

        open_lines = self._get_open_receivable_lines()
        if not open_lines:
            raise UserError(_("This invoice has no open balance to retain."))
        receivable_accounts = open_lines.account_id
        if len(receivable_accounts) > 1:
            raise UserError(
                _(
                    "Cannot create the retention because the invoice has "
                    "an open balance on more than one receivable account."
                )
            )
        residual_total = sum(open_lines.mapped("amount_residual"))
        if self.currency_id.compare_amounts(self.amount, residual_total) > 0:
            raise UserError(
                _(
                    "The retention amount (%(amount)s) cannot be greater "
                    "than the invoice's open balance (%(residual)s)."
                )
                % {
                    "amount": self.amount,
                    "residual": residual_total,
                }
            )

        journal = self.journal_id or self.move_id.journal_id
        partner = self.move_id.partner_id
        description = _("Escrow/Retention - %s") % self.move_id.name

        retention_move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": self.date,
                "ref": description,
                "retention_invoice_id": self.move_id.id,
                "line_ids": [
                    Command.create(
                        {
                            "name": description,
                            "account_id": receivable_accounts.id,
                            "partner_id": partner.id,
                            "credit": self.amount,
                            "debit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "name": description,
                            "account_id": self.escrow_account_id.id,
                            "partner_id": partner.id,
                            "debit": self.amount,
                            "credit": 0.0,
                            "date_maturity": self.date_due or False,
                        }
                    ),
                ],
            }
        )
        retention_move.action_post()

        credit_line = retention_move.line_ids.filtered(
            lambda line: line.account_id == receivable_accounts
        )
        (credit_line + open_lines).reconcile()

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.move_id.id,
            "view_mode": "form",
            "views": [(self.env.ref("account.view_move_form").id, "form")],
            "target": "current",
        }
