# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleTierValidationDynamicState(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_reviewer = cls.env["res.users"].create(
            {
                "name": "Reviewer Mitchell",
                "login": "reviewer_mitchell",
                "email": "m@test.com",
            }
        )

        def get_selection_id(value):
            return (
                cls.env["ir.model.fields.selection"]
                .search(
                    [
                        ("field_id.model", "=", "sale.order"),
                        ("field_id.name", "=", "state"),
                        ("value", "=", value),
                    ],
                    limit=1,
                )
                .id
            )

        cls.draft_state = get_selection_id("draft")
        cls.sent_state = get_selection_id("sent")
        cls.sale_state = get_selection_id("sale")
        cls.cancel_state = get_selection_id("cancel")

        cls.env["tier.definition"].create(
            {
                "name": "Approve Sending",
                "model_id": cls.env.ref("sale.model_sale_order").id,
                "review_type": "individual",
                "reviewer_id": cls.user_reviewer.id,
                "state_from": cls.draft_state,
                "state_to": cls.sent_state,
            }
        )
        cls.env["tier.definition"].create(
            {
                "name": "Approve Cancellation",
                "model_id": cls.env.ref("sale.model_sale_order").id,
                "review_type": "individual",
                "reviewer_id": cls.user_reviewer.id,
                "state_from": cls.sale_state,
                "state_to": cls.cancel_state,
            }
        )

    def setUp(self):
        super().setUp()
        self.order = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_1").id,
            }
        )

    def test_action_quotation_send_interception(self):
        """Test if 'Send by Email' button is blocked and create tier review."""
        order = self.order
        self.assertEqual(order.state, "draft")
        self.assertFalse(order.review_ids)

        res = order.action_quotation_send()
        self.assertTrue(res is True, "Should return True")

        review = order.review_ids.filtered(lambda r: r.state_to == "sent")
        self.assertTrue(review, "Should create the tier review")

        review.write(
            {
                "status": "approved",
                "done_by": self.env.user.id,
                "reviewed_date": fields.Datetime.now(),
            }
        )

        res_approved = order.action_quotation_send()
        self.assertIsInstance(res_approved, dict, "After approve, should return a dict")

    def test_action_cancel_interception(self):
        """Test if 'Cancel' button is blocked and create tier review."""
        order = self.order
        self.assertEqual(order.state, "draft")
        self.assertFalse(order.review_ids)

        order.action_confirm()
        self.assertEqual(order.state, "sale")
        self.assertFalse(order.review_ids)

        res = order.action_cancel()
        self.assertTrue(res is True, "Should return True")

        review = order.review_ids.filtered(lambda r: r.state_to == "cancel")
        self.assertTrue(review, "Should create the tier review")

        review.write(
            {
                "status": "approved",
                "done_by": self.env.user.id,
                "reviewed_date": fields.Datetime.now(),
            }
        )

        res_approved = order.action_cancel()
        self.assertIsInstance(res_approved, dict, "After approve, should return a dict")

    def test_no_interception_if_no_definition(self):
        """The buttons should work if no definition from the state is find."""
        order = self.order
        self.assertEqual(order.state, "draft")
        self.assertFalse(order.review_ids)

        order.action_cancel()
        self.assertFalse(order.review_ids)
        self.assertEqual(order.state, "cancel")
