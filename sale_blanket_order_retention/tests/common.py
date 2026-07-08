# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date, timedelta

from odoo import Command, fields

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestRetentionCommon(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.escrow_account = cls.copy_account(
            cls.company_data["default_account_receivable"]
        )
        cls.escrow_journal = cls.company_data["default_journal_misc"]
        cls.bank_journal = cls.company_data["default_journal_bank"]

        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Retention Test Pricelist",
                "currency_id": cls.company_data["currency"].id,
            }
        )

        cls.blanket_order = cls.env["sale.blanket.order"].create(
            {
                "partner_id": cls.partner_a.id,
                "validity_date": fields.Date.to_string(
                    date.today() + timedelta(days=365)
                ),
                "payment_term_id": cls.pay_terms_a.id,
                "pricelist_id": cls.pricelist.id,
                "escrow_account_id": cls.escrow_account.id,
                "escrow_journal_id": cls.escrow_journal.id,
                "line_ids": [
                    Command.create(
                        {
                            "product_id": cls.product_a.id,
                            "product_uom": cls.product_a.uom_id.id,
                            "original_uom_qty": 20.0,
                            "price_unit": 100.0,
                        }
                    ),
                ],
            }
        )
        cls.blanket_order.sudo().onchange_partner_id()
        cls.blanket_order.sudo().action_confirm()

    @classmethod
    def _create_linked_sale_order(cls, qty=10.0):
        so = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_a.id,
                "order_line": [
                    Command.create(
                        {
                            "name": cls.product_a.name,
                            "product_id": cls.product_a.id,
                            "product_uom_qty": qty,
                            "product_uom": cls.product_a.uom_id.id,
                            "price_unit": 100.0,
                        }
                    )
                ],
            }
        )
        so_line = so.order_line[0]
        so_line.with_context(from_sale_order=True).name_get()
        so_line.onchange_product_id()
        so.action_confirm()
        return so

    @classmethod
    def _create_posted_invoice(cls, sale_order):
        invoice = sale_order._create_invoices()
        invoice.action_post()
        return invoice

    def _register_payment(self, invoice, amount):
        payment_register = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "amount": amount,
                    "journal_id": self.bank_journal.id,
                    "payment_date": fields.Date.today(),
                }
            )
        )
        payment_register.action_create_payments()

    def _create_wizard(self, invoice, **vals):
        """Create the retention wizard the same way the invoice button
        does (passing default_move_id in the context), so that
        default_get() properly inherits the escrow account/journal from
        the invoice when they are set."""
        vals.setdefault("date", fields.Date.today())
        vals["move_id"] = invoice.id
        return (
            self.env["account.move.retention.wizard"]
            .with_context(default_move_id=invoice.id)
            .create(vals)
        )
