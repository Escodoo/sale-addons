# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestSaleTierValidationInvoice(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.so_model = cls.env.ref("sale.model_sale_order")
        sales_group = cls.env.ref("sales_team.group_sale_salesman_all_leads")
        sys_group = cls.env.ref("base.group_system")
        cls.review_group = cls.env["res.groups"].create(
            {"name": "SO Tier Approval Group Test"}
        )
        cls.reviewer = cls.env["res.users"].create(
            {
                "name": "SO Tier Group Reviewer",
                "login": "so_tier_group_reviewer_test",
                "groups_id": [
                    (6, 0, (sales_group + sys_group + cls.review_group).ids),
                ],
                "email": "so_tier_group_reviewer_test@example.com",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Tier Group Partner"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Tier Group Product",
                "type": "service",
                "invoice_policy": "order",
                "list_price": 100.0,
            }
        )

    def setUp(self):
        super().setUp()
        # Isolate tests from any existing sale.order tier definitions.
        self.env["tier.definition"].with_context(active_test=False).search(
            [("model", "=", "sale.order")]
        ).write({"active": False})

    def _create_sale_order(self):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

    def _create_group_tier_definition(self, **extra_vals):
        domain = str([("partner_id", "=", self.partner.id)])
        vals = {
            "model_id": self.so_model.id,
            "review_type": "group",
            "reviewer_group_id": self.review_group.id,
            "definition_domain": domain,
            "sequence": 20,
        }
        vals.update(extra_vals)
        return self.env["tier.definition"].create(vals)

    def _approve_pending_reviews_as_group_reviewer(self, order):
        order.with_user(self.reviewer).validate_tier()
        self.assertFalse(order.review_ids.filtered(lambda r: r.status == "pending"))

    def test_confirm_without_tier_definition(self):
        so = self._create_sale_order()
        so.action_confirm()
        self.assertEqual(so.state, "sale")
        invoices = so._create_invoices()
        self.assertTrue(invoices)

    def test_group_tier_blocks_confirm_until_approved(self):
        self._create_group_tier_definition()
        so = self._create_sale_order()
        with self.assertRaises(ValidationError):
            so.action_confirm()
        so.request_validation()
        pending = so.review_ids.filtered(lambda r: r.status == "pending")
        self.assertTrue(pending)
        self.assertTrue(any(self.reviewer in review.reviewer_ids for review in pending))

        self._approve_pending_reviews_as_group_reviewer(so)
        so.action_confirm()
        self.assertEqual(so.state, "sale")

    def test_group_tier_domain_mismatch_does_not_block_confirm(self):
        other = self.env["res.partner"].create({"name": "Other partner"})
        self._create_group_tier_definition(
            definition_domain=str([("partner_id", "=", other.id)])
        )
        so = self._create_sale_order()
        so.action_confirm()
        self.assertEqual(so.state, "sale")
        self.assertFalse(so.review_ids)

    def test_invoicing_not_blocked_after_group_validation(self):
        self._create_group_tier_definition()
        so = self._create_sale_order()
        with self.assertRaises(ValidationError):
            so.action_confirm()
        so.request_validation()
        self._approve_pending_reviews_as_group_reviewer(so)
        so.action_confirm()
        invoices = so._create_invoices()
        self.assertTrue(invoices)

    def test_state_from_is_draft_sent(self):
        self.assertEqual(self.env["sale.order"]._state_from, ["draft", "sent"])
