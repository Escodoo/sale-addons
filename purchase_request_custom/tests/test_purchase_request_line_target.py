# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.sale_blanket_order_custom.tests.common import SaleBlanketOrderCommon


class TestPurchaseRequestLineTarget(SaleBlanketOrderCommon):
    def _set_standard_price(self, product, price):
        product.standard_price = price

    def _prepare_blanket_product_cost(self, blanket, product, price_unit, quantity):
        self.env["sale.blanket.order.product"].search(
            [("blanket_order_id", "=", blanket.id), ("product_id", "=", product.id)]
        ).unlink()
        return self.env["sale.blanket.order.product"].create(
            {
                "blanket_order_id": blanket.id,
                "product_id": product.id,
                "quantity": quantity,
                "price_unit": price_unit,
            }
        )

    def _prepare_blanket_service_cost(self, blanket, product, price_unit, quantity):
        self.env["sale.blanket.order.service"].search(
            [("blanket_order_id", "=", blanket.id), ("product_id", "=", product.id)]
        ).unlink()
        return self.env["sale.blanket.order.service"].create(
            {
                "blanket_order_id": blanket.id,
                "product_id": product.id,
                "quantity": quantity,
                "price_unit": price_unit,
            }
        )

    def test_target_value_product_branch_above_true(self):
        price_unit = 200.0
        quantity = 7.0
        self._prepare_blanket_product_cost(
            self.blanket, self.product_a, price_unit=price_unit, quantity=quantity
        )

        self._set_standard_price(self.product_a, 1000.0)

        analytic_distribution = {str(self.analytic_account_a1.id): 100.0}
        line = self.env["purchase.request.line"].new(
            {
                "product_id": self.product_a.id,
                "analytic_distribution": analytic_distribution,
            }
        )
        line._compute_estimated_unit_cost()
        line._compute_target()

        self.assertEqual(line.target_value, price_unit)
        self.assertEqual(line.target_quantity, quantity)
        self.assertTrue(line.target_above)

    def test_target_value_service_branch_above_false_when_equal(self):
        price_unit = 80.0
        quantity = 9.0

        self.env["sale.blanket.order.product"].search(
            [
                ("blanket_order_id", "=", self.blanket.id),
                ("product_id", "=", self.service_a.id),
            ]
        ).unlink()
        self._prepare_blanket_service_cost(
            self.blanket, self.service_a, price_unit=price_unit, quantity=quantity
        )

        self._set_standard_price(self.service_a, price_unit)

        analytic_distribution = {str(self.analytic_account_a1.id): 100.0}
        line = self.env["purchase.request.line"].new(
            {
                "product_id": self.service_a.id,
                "analytic_distribution": analytic_distribution,
            }
        )
        line._compute_estimated_unit_cost()
        line._compute_target()

        self.assertEqual(line.target_value, price_unit)
        self.assertEqual(line.target_quantity, quantity)
        self.assertFalse(line.target_above)

    def test_target_value_without_analytic_distribution_returns(self):
        self._set_standard_price(self.product_a, 10.0)
        self._prepare_blanket_product_cost(
            self.blanket, self.product_a, price_unit=50.0, quantity=2.0
        )

        line = self.env["purchase.request.line"].new(
            {
                "product_id": self.product_a.id,
                "analytic_distribution": {},
            }
        )
        line._compute_estimated_unit_cost()
        line._compute_target()

        self.assertEqual(line.target_value, 0.0)
        self.assertEqual(line.target_quantity, 0.0)
        self.assertTrue(line.target_above)

    def test_target_value_without_product_id_returns_zero_and_above_false(self):
        line = self.env["purchase.request.line"].new(
            {
                "analytic_distribution": {str(self.analytic_account_a1.id): 100.0},
            }
        )
        line._compute_estimated_unit_cost()
        line._compute_target()

        self.assertEqual(line.target_value, 0.0)
        self.assertEqual(line.target_quantity, 0.0)
        self.assertFalse(line.target_above)
