# Copyright 2025 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from .common import SaleBlanketOrderCommon


class TestSaleBlanketOrderCustom(SaleBlanketOrderCommon, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.analytic_account = cls.analytic_account_a1
        cls.partner = cls.partner_a
        cls.product = cls.product_a
        cls.service = cls.service_a
        cls.currency = cls.currency
        cls.pricelist = cls.pricelist
        cls.blanket = cls.blanket

    def test_00_full_workflow(self):
        """
        Test the full workflow of the custom sale blanket order,
        including cost calculation, analytic lines, plan creation,
        wizard-based order generation, and constraints.
        """
        rec_product = self.env["sale.blanket.order.product"].create(
            {
                "blanket_order_id": self.blanket.id,
                "product_id": self.product.id,
                "quantity": 2.0,
            }
        )
        rec_product._onchange_product_id()
        self.assertEqual(rec_product.price_unit, rec_product.product_id.standard_price)
        rec_product._compute_subtotal()
        self.assertEqual(
            rec_product.subtotal, rec_product.price_unit * rec_product.quantity
        )
        rec_product._compute_amount_total()
        self.assertEqual(rec_product.amount_total, rec_product.subtotal)

        rec_service = self.env["sale.blanket.order.service"].create(
            {
                "blanket_order_id": self.blanket.id,
                "product_id": self.service.id,
                "quantity": 3.0,
            }
        )
        rec_service._onchange_product_id()
        self.assertEqual(rec_service.price_unit, rec_service.product_id.standard_price)
        rec_service._compute_subtotal()
        self.assertEqual(
            rec_service.subtotal, rec_service.price_unit * rec_service.quantity
        )
        rec_service._compute_amount_total()
        self.assertEqual(rec_service.amount_total, rec_service.subtotal)

        self.blanket._compute_total_product_costs()
        self.blanket._compute_total_service_costs()
        self.blanket._compute_total_costs()
        self.assertEqual(
            self.blanket.total_product_costs,
            sum(self.blanket.order_product_ids.mapped("amount_total")),
        )
        self.assertEqual(
            self.blanket.total_service_costs,
            sum(self.blanket.order_service_ids.mapped("amount_total")),
        )
        self.assertEqual(
            self.blanket.total_costs,
            self.blanket.total_product_costs + self.blanket.total_service_costs,
        )

        self.env["account.analytic.line"].create(
            {"name": "TS1", "account_id": self.analytic_account.id}
        )
        self.env["account.analytic.line"].create(
            {"name": "TS2", "account_id": self.analytic_account.id}
        )
        self.blanket._compute_account_analytic_line_ids()
        self.assertEqual(self.blanket.account_analytic_line_count, 2)
        self.assertEqual(len(self.blanket.account_analytic_line_ids), 2)
        action_analytic = self.blanket.action_show_account_analytic_line()
        self.assertEqual(action_analytic["res_model"], "account.analytic.line")
        self.assertIn(
            ("account_id", "=", self.analytic_account.id), action_analytic["domain"]
        )
        self.assertNotIn("group_by", action_analytic["context"])
        self.assertEqual(
            action_analytic["context"].get("tree_view_ref"),
            "analytic.view_account_analytic_line_tree",
        )

        self.blanket._compute_mis_cash_flow_forecast_line_ids()
        self.assertEqual(
            self.blanket.mis_cash_flow_forecast_line_count,
            len(self.blanket.mis_cash_flow_forecast_line_ids),
        )
        action_forecast = self.blanket.action_show_mis_forecast()
        self.assertEqual(action_forecast["res_model"], "mis.cash_flow.forecast_line")
        self.assertIn(("res_model", "=", self.blanket._name), action_forecast["domain"])
        self.assertIn(("res_id", "=", self.blanket.id), action_forecast["domain"])
        self.assertNotIn("group_by", action_forecast["context"])

        wiz_model = self.env["sale.create.order.plan"].with_context(
            active_id=self.blanket.id
        )
        with self.assertRaises(ValidationError):
            wiz_model.create(
                {
                    "num_installment": 1,
                    "installment_date": date.today(),
                    "interval": 1,
                    "interval_type": "month",
                }
            ).sale_create_order_plan()

        wiz = wiz_model.create(
            {
                "num_installment": 2,
                "installment_date": date.today(),
                "interval": 1,
                "interval_type": "month",
            }
        )
        res_wiz = wiz.sale_create_order_plan()
        self.assertEqual(res_wiz.get("type"), "ir.actions.act_window_close")
        self.assertEqual(len(self.blanket.sale_order_plan_ids), 2)

        self.blanket.state = "draft"
        self.blanket.sale_order_plan_ids._compute_to_order()
        for p in self.blanket.sale_order_plan_ids:
            self.assertFalse(p.to_order)
        self.blanket.sale_order_plan_ids._compute_ordered()
        for p in self.blanket.sale_order_plan_ids:
            self.assertFalse(p.ordered)

        self.blanket._compute_ip_sale_order_plan()
        self.assertFalse(self.blanket.ip_sale_order_plan)

        self.blanket.write({"use_sale_order_plan": True})

        self.blanket.remove_order_plan()
        with self.assertRaises(UserError):
            self.blanket.action_confirm()

        self.blanket.create_order_plan(2, date.today(), 1, "month")
        self.blanket.write({"validity_date": date.today() + timedelta(days=1)})

        res_confirm = self.blanket.action_confirm()
        self.assertIsNotNone(res_confirm)
        self.assertEqual(self.blanket.state, "open")

        self.blanket._compute_ip_sale_order_plan()
        self.assertTrue(self.blanket.ip_sale_order_plan)

        plan = self.blanket.sale_order_plan_ids[0]
        plan.write({"percent": 0.0})
        with self.assertRaises(ValidationError):
            self.blanket.write({"state": "done"})
        plan.write({"percent": 50.0})

        self.blanket.sale_order_plan_ids._compute_to_order()
        plans = self.blanket.sale_order_plan_ids.sorted("installment")
        first = plans[0]
        second = plans[1]
        self.assertTrue(first.to_order)
        self.assertFalse(second.to_order)

        wiz_model_cls = self.env["sale.make.planned.order"]
        wiz_default = wiz_model_cls.with_context(active_id=self.blanket.id).create({})
        wiz_default.create_orders_by_plan()

        self.blanket.sale_order_plan_ids._compute_ordered()
        self.assertTrue(first.ordered)
        self.assertFalse(second.ordered)

        self.blanket.sale_order_plan_ids._compute_to_order()
        self.assertTrue(second.to_order)
        self.assertFalse(first.to_order)

        self.blanket.remove_order_plan()
        self.blanket.create_order_plan(2, date.today(), 1, "month")
        plans = self.blanket.sale_order_plan_ids.sorted("installment")
        first = plans[0]
        second = plans[1]
        self.blanket.sale_order_plan_ids._compute_to_order()
        self.assertTrue(first.to_order)
        self.assertFalse(second.to_order)

        wiz_all = wiz_model_cls.with_context(
            active_id=self.blanket.id, all_remain_orders=True
        ).create({})
        wiz_all.create_orders_by_plan()

        self.blanket.sale_order_plan_ids._compute_ordered()
        self.assertTrue(first.ordered)
        self.assertFalse(second.ordered)

        self.blanket.remove_order_plan()
        self.blanket.create_order_plan(2, date.today(), 1, "month")
        plans = self.blanket.sale_order_plan_ids.sorted("installment")
        plans[0]._compute_new_order_quantity(self.blanket)
        plans[1]._compute_new_order_quantity(self.blanket)

        next_m = self.blanket._next_date(date.today(), 1, "month")
        next_y = self.blanket._next_date(date.today(), 1, "year")
        next_d = self.blanket._next_date(date.today(), 10, "day")
        self.assertTrue(fields.Date.from_string(next_m))
        self.assertTrue(fields.Date.from_string(next_y))
        self.assertTrue(fields.Date.from_string(next_d))

        self.blanket.line_ids[0].write({"remaining_uom_qty": 2.0})
        orders = self.blanket.with_context(
            order_plan_id=plans[0].id
        )._create_sale_order()
        self.assertTrue(orders.__class__._name, "sale.order")
        self.assertIsNotNone(orders)

        self.blanket.remove_order_plan()
        self.blanket.create_order_plan(
            num_installment=3,
            installment_date=date.today(),
            interval=1,
            interval_type="month",
        )
        self.assertEqual(len(self.blanket.sale_order_plan_ids), 3)
        last_plan_num = max(self.blanket.sale_order_plan_ids.mapped("installment"))
        for plan in self.blanket.sale_order_plan_ids:
            self.assertEqual(plan.last, plan.installment == last_plan_num)

        self.assertTrue(self.blanket.remove_order_plan())
        self.assertFalse(self.blanket.sale_order_plan_ids)

        self.blanket.create_order_plan(2, date.today(), 1, "month")
        plan = self.blanket.sale_order_plan_ids[0]
        dup = self.env["sale.blanket.order.sale.order.plan"].create(
            {
                "sale_id": plan.sale_id.id,
                "installment": plan.installment + 1000,
                "plan_date": plan.plan_date,
                "order_type": "installment",
                "percent": 50.0,
            }
        )
        self.assertTrue(dup)
