# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo.tests.common import TransactionCase


class TestSaleBlanketOrderRevisionPriceAlert(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.product = self.env["product.product"].create(
            {"name": "Test Product", "type": "consu"}
        )
        self.pricelist = self.env["product.pricelist"].search([], limit=1)
        self.blanket_order = self.env["sale.blanket.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "validity_date": datetime.date.today() + datetime.timedelta(days=1),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "original_uom_qty": 10.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

    def _create_revision(self, adjustment_percentage=0.0):
        wizard = self.env["sale.blanket.order.revision.wizard"].create(
            {
                "old_blanket_order_id": self.blanket_order.id,
                "adjustment_percentage": adjustment_percentage,
            }
        )
        wizard.create_revision()
        return wizard.new_blanket_order_id

    def test_warning_shown_for_price_reduction_via_wizard_percentage(self):
        new_order = self._create_revision(adjustment_percentage=-10.0)

        self.assertTrue(new_order.price_reduction_warning)
        self.assertIn("90.00", new_order.price_reduction_warning)

    def test_warning_shown_for_price_reduction_via_manual_edit(self):
        new_order = self._create_revision(adjustment_percentage=0.0)
        self.assertFalse(new_order.price_reduction_warning)
        new_order.line_ids.write({"price_unit": 90.0})

        self.assertTrue(new_order.price_reduction_warning)
        self.assertIn("90.00", new_order.price_reduction_warning)

    def test_no_warning_when_price_does_not_go_down(self):
        new_order = self._create_revision(adjustment_percentage=10.0)
        self.assertFalse(new_order.price_reduction_warning)

    def test_no_warning_when_there_is_no_previous_version(self):
        self.assertFalse(self.blanket_order.price_reduction_warning)

    def test_warning_clears_when_price_is_raised_back(self):
        new_order = self._create_revision(adjustment_percentage=-10.0)
        self.assertTrue(new_order.price_reduction_warning)
        new_order.line_ids.write({"price_unit": 150.0})
        self.assertFalse(new_order.price_reduction_warning)
