# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.base.tests.common import BaseCommon


class TestSaleCrmAnalyticDistribution(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.analytic_plan = cls.env["account.analytic.plan"].create({"name": "Plan"})
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {"name": "Analytic Account", "plan_id": cls.analytic_plan.id}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env.ref("product.product_product_4")
        cls.lead = cls.env["crm.lead"].create(
            {
                "name": "Test Opportunity",
                "type": "opportunity",
                "partner_id": cls.partner.id,
                "analytic_account_id": cls.analytic_account.id,
            }
        )

    def test_quotation_context_has_analytic_distribution(self):
        action = self.lead.action_new_quotation()
        self.assertEqual(
            action["context"].get("default_analytic_distribution"),
            {str(self.analytic_account.id): 100},
        )

    def test_quotation_context_without_analytic_account(self):
        lead = self.env["crm.lead"].create(
            {
                "name": "No Analytic Account",
                "type": "opportunity",
                "partner_id": self.partner.id,
            }
        )
        action = lead.action_new_quotation()
        self.assertNotIn("default_analytic_distribution", action["context"])

    def test_quotation_created_from_context_propagates_to_lines(self):
        action = self.lead.action_new_quotation()
        sale_order = (
            self.env["sale.order"]
            .with_context(**action["context"])
            .create(
                {
                    "partner_id": self.partner.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product.id,
                                "product_uom_qty": 1,
                            },
                        )
                    ],
                }
            )
        )
        self.assertEqual(
            sale_order.analytic_distribution,
            {str(self.analytic_account.id): 100},
        )
        self.assertEqual(
            sale_order.order_line.analytic_distribution,
            {str(self.analytic_account.id): 100},
        )

    def test_order_line_default_get_ignores_leaked_context(self):
        """default_analytic_distribution must not leak into order lines.

        Odoo applies a `default_<field>` context key to every model that
        has a field with that name, not only the one it was meant for.
        Since both `sale.order` and `sale.order.line` have an
        `analytic_distribution` field, this context key would otherwise
        make new order lines carry the opportunity's analytic account as
        their own value, which the analytic distribution widget cannot
        resolve and crashes on (the line disappears from the UI).
        """
        defaults = (
            self.env["sale.order.line"]
            .with_context(
                default_analytic_distribution={str(self.analytic_account.id): 100}
            )
            .default_get(["analytic_distribution"])
        )
        self.assertNotIn("analytic_distribution", defaults)

    def test_adding_line_to_existing_order_inherits_opportunity_account(self):
        """Adding a line to an order linked to the opportunity inherits its
        analytic account directly, even if the header field was reset
        (e.g. because another line was temporarily empty)."""
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "opportunity_id": self.lead.id,
            }
        )
        sale_order.write(
            {
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 1})
                ]
            }
        )
        self.assertEqual(
            sale_order.order_line.analytic_distribution,
            {str(self.analytic_account.id): 100},
        )
