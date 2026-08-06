# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestRetentionCommon


@tagged("post_install", "-at_install")
class TestAccountMoveRetention(TestRetentionCommon):
    def test_escrow_fields_propagation(self):
        """Escrow fields flow from the blanket order down to the SO
        and to the invoice."""
        so = self._create_linked_sale_order()
        self.assertEqual(so.blanket_order_id, self.blanket_order)
        self.assertEqual(so.escrow_account_id, self.escrow_account)
        self.assertEqual(so.escrow_journal_id, self.escrow_journal)

        invoice = self._create_posted_invoice(so)
        self.assertEqual(invoice.escrow_account_id, self.escrow_account)
        self.assertEqual(invoice.escrow_journal_id, self.escrow_journal)

    def test_retention_wizard_creates_move_and_reconciles(self):
        """Paying ~80% and retaining the remainder fully closes the
        invoice and flags it as 'payment_retained' instead of a plain
        overdue/open invoice."""
        so = self._create_linked_sale_order(qty=10.0)
        invoice = self._create_posted_invoice(so)
        self.assertGreater(invoice.amount_total, 0.0)

        pay_amount = invoice.currency_id.round(invoice.amount_total * 0.8)
        self._register_payment(invoice, pay_amount)
        self.assertEqual(invoice.payment_state, "partial")

        retain_amount = invoice.amount_residual
        self.assertGreater(retain_amount, 0.0)

        wizard = self._create_wizard(invoice, amount=retain_amount)
        # Escrow account/journal are inherited (readonly) from the invoice.
        self.assertEqual(wizard.escrow_account_id, self.escrow_account)
        self.assertEqual(wizard.journal_id, self.escrow_journal)

        wizard.action_confirm()

        self.assertAlmostEqual(invoice.amount_residual, 0.0)
        self.assertEqual(invoice.payment_state, "payment_retained")
        self.assertEqual(invoice.retention_move_count, 1)

        retention_move = invoice.retention_move_ids
        self.assertEqual(retention_move.state, "posted")
        escrow_line = retention_move.line_ids.filtered(
            lambda line: line.account_id == self.escrow_account
        )
        credit_line = retention_move.line_ids - escrow_line
        self.assertAlmostEqual(escrow_line.debit, retain_amount)
        self.assertAlmostEqual(credit_line.credit, retain_amount)
        self.assertFalse(escrow_line.reconciled)
        self.assertTrue(credit_line.reconciled)

    def test_release_retention_reverts_payment_state(self):
        """Once the escrow line is reconciled (retention released), the
        invoice must go back to a normal 'paid' status."""
        so = self._create_linked_sale_order(qty=10.0)
        invoice = self._create_posted_invoice(so)
        pay_amount = invoice.currency_id.round(invoice.amount_total * 0.8)
        self._register_payment(invoice, pay_amount)
        retain_amount = invoice.amount_residual

        wizard = self._create_wizard(invoice, amount=retain_amount)
        wizard.action_confirm()
        self.assertEqual(invoice.payment_state, "payment_retained")

        retention_move = invoice.retention_move_ids
        escrow_line = retention_move.line_ids.filtered(
            lambda line: line.account_id == self.escrow_account
        )

        release_move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.escrow_journal.id,
                "date": fields.Date.today(),
                "line_ids": [
                    Command.create(
                        {
                            "name": "Release",
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                            "debit": retain_amount,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Release",
                            "account_id": self.escrow_account.id,
                            "debit": 0.0,
                            "credit": retain_amount,
                        }
                    ),
                ],
            }
        )
        release_move.action_post()
        release_line = release_move.line_ids.filtered(
            lambda line: line.account_id == self.escrow_account
        )
        (escrow_line + release_line).reconcile()

        self.assertTrue(escrow_line.reconciled)
        self.assertEqual(invoice.payment_state, "paid")

    def test_wizard_amount_exceeds_residual_raises(self):
        so = self._create_linked_sale_order(qty=10.0)
        invoice = self._create_posted_invoice(so)
        pay_amount = invoice.currency_id.round(invoice.amount_total * 0.8)
        self._register_payment(invoice, pay_amount)
        retain_amount = invoice.amount_residual

        wizard = self._create_wizard(invoice, amount=retain_amount + 50.0)
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_wizard_amount_zero_raises(self):
        so = self._create_linked_sale_order(qty=10.0)
        invoice = self._create_posted_invoice(so)
        pay_amount = invoice.currency_id.round(invoice.amount_total * 0.8)
        self._register_payment(invoice, pay_amount)

        wizard = self._create_wizard(invoice, amount=0.0)
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_wizard_requires_escrow_account_when_missing(self):
        """An invoice not linked to any blanket order has no escrow
        account; the wizard must require one to be filled manually."""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Ad-hoc line",
                            "quantity": 1,
                            "price_unit": 500.0,
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                        }
                    )
                ],
            }
        )
        invoice.action_post()
        self.assertFalse(invoice.escrow_account_id)

        pay_amount = invoice.currency_id.round(invoice.amount_total * 0.8)
        self._register_payment(invoice, pay_amount)
        retain_amount = invoice.amount_residual

        wizard = self._create_wizard(invoice, amount=retain_amount)
        self.assertFalse(wizard.escrow_account_id)
        with self.assertRaises(UserError):
            wizard.action_confirm()

        wizard.escrow_account_id = self.escrow_account
        wizard.journal_id = self.escrow_journal
        wizard.action_confirm()
        self.assertEqual(invoice.payment_state, "payment_retained")
