# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from .common import SaleBlanketOrderAllowOverQtyCommon


class TestAllowOverQty(SaleBlanketOrderAllowOverQtyCommon, TransactionCase):
    def _create_blanket(self, allow_over_qty, original_uom_qty=5.0):
        blanket = self.env["sale.blanket.order"].create(
            {
                "partner_id": self.partner.id,
                "currency_id": self.currency.id,
                "pricelist_id": self.pricelist.id,
                "analytic_account_id": self.analytic_account.id,
                "validity_date": date.today() + timedelta(days=30),
                "allow_over_qty": allow_over_qty,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "original_uom_qty": original_uom_qty,
                            "price_unit": self.product.lst_price,
                        },
                    )
                ],
            }
        )
        blanket.action_confirm()
        return blanket

    def _get_wizard(self, blanket):
        return (
            self.env["sale.blanket.order.wizard"]
            .with_context(
                active_model="sale.blanket.order",
                active_id=blanket.id,
                active_ids=[blanket.id],
            )
            .create({})
        )

    def test_sale_order_confirm_respects_allow_over_qty(self):
        """
        Confirming a sale order that exceeds the blanket order line's
        remaining quantity must raise, unless allow_over_qty is enabled on
        the blanket order.
        """

        def _create_sale_order(blanket):
            bo_line = blanket.line_ids[0]
            return self.env["sale.order"].create(
                {
                    "partner_id": self.partner.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product.id,
                                "product_uom_qty": 10.0,
                                "price_unit": self.product.lst_price,
                                "blanket_order_line": bo_line.id,
                            },
                        )
                    ],
                }
            )

        # allow_over_qty=False: confirming must raise ValidationError
        b_no_over = self._create_blanket(allow_over_qty=False)
        so_no_over = _create_sale_order(b_no_over)
        with self.assertRaises(ValidationError):
            so_no_over.action_confirm()

        # allow_over_qty=True: confirming must succeed even over qty
        b_over = self._create_blanket(allow_over_qty=True)
        so_over = _create_sale_order(b_over)
        so_over.action_confirm()
        self.assertEqual(so_over.state, "sale")

    def test_wizard_create_sale_order_respects_allow_over_qty(self):
        """
        Reproduce the "Create and view order" wizard flow (button on the
        blanket order form): ordering more than the remaining quantity must
        raise unless allow_over_qty is enabled on the blanket order.
        """
        # allow_over_qty=False: requesting more than remaining must raise
        b_no_over = self._create_blanket(allow_over_qty=False)
        wizard_no_over = self._get_wizard(b_no_over)
        wizard_no_over.line_ids[0].qty = 10.0
        with self.assertRaises(UserError):
            wizard_no_over.create_sale_order()

        # allow_over_qty=True: requesting more than remaining must succeed
        b_over = self._create_blanket(allow_over_qty=True)
        wizard_over = self._get_wizard(b_over)
        wizard_over.line_ids[0].qty = 10.0
        action = wizard_over.create_sale_order()
        created_so = self.env["sale.order"].browse(action["domain"][0][2])
        self.assertEqual(created_so.order_line.product_uom_qty, 10.0)

    def test_wizard_negative_remaining_qty_keeps_blanket_order_open(self):
        """
        Ordering past the remaining quantity leaves it negative (not exactly
        zero), so the blanket order stays "open" (it only becomes "done"
        when the remaining quantity is exactly zero). With allow_over_qty
        enabled, a further order must still be possible afterwards.
        """
        blanket = self._create_blanket(allow_over_qty=True, original_uom_qty=5.0)
        bo_line = blanket.line_ids[0]

        first_wizard = self._get_wizard(blanket)
        first_wizard.line_ids[0].qty = 90.0
        first_wizard.create_sale_order()
        self.assertEqual(bo_line.remaining_uom_qty, 5.0 - 90.0)
        self.assertEqual(blanket.state, "open")

        # The blanket order is still open, so a further order must succeed.
        second_wizard = self._get_wizard(blanket)
        self.assertEqual(len(second_wizard.line_ids), 1)
        second_wizard.line_ids[0].qty = 10.0
        action = second_wizard.create_sale_order()
        created_so = self.env["sale.order"].browse(action["domain"][0][2])
        self.assertEqual(created_so.order_line.product_uom_qty, 10.0)
