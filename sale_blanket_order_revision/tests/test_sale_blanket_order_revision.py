# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from types import SimpleNamespace

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.sale_blanket_order_revision.models.sale_blanket_order import (
    SaleBlanketOrder,
)
from odoo.addons.sale_blanket_order_revision.wizard import (
    sale_blanket_order_revision as revision_wizard,
)


class FakeRevisionLinks:
    def __init__(self, new_ids):
        self._new_ids = new_ids

    def mapped(self, field_name):
        if field_name == "new_blanket_order_id.id":
            return self._new_ids
        return []


class FakeWritable:
    def __init__(self, **values):
        for key, value in values.items():
            setattr(self, key, value)

        def _write(vals):
            for key, value in vals.items():
                setattr(self, key, value)
            return True

        self.write = _write


class FakeWizardModel:
    def __init__(self, chain_map):
        self.chain_map = chain_map

    def sudo(self):
        return self

    def search(self, domain):
        target_id = domain[0][2]
        return self.chain_map.get(target_id)


class FakeEnv:
    def __init__(self, chain_map):
        self.chain_map = chain_map

    def __getitem__(self, model_name):
        if model_name == "sale.blanket.order.revision.wizard":
            return FakeWizardModel(self.chain_map)
        raise KeyError(model_name)


class FakeRevisionWizard:
    _get_revision_count = (
        revision_wizard.SaleBlanketOrderRevisionWizard._get_revision_count
    )

    def __init__(self, old_id, env):
        self.old_blanket_order_id = SimpleNamespace(id=old_id)
        self.env = env


class TestSaleBlanketOrderRevision(TransactionCase):
    def test_compute_all_quotations_invoiced(self):
        all_invoiced = SimpleNamespace(
            mapped=lambda _: [
                SimpleNamespace(invoice_status="invoiced"),
                SimpleNamespace(invoice_status="invoiced"),
            ],
            all_quotations_invoiced=False,
        )
        not_all_invoiced = SimpleNamespace(
            mapped=lambda _: [
                SimpleNamespace(invoice_status="invoiced"),
                SimpleNamespace(invoice_status="to invoice"),
            ],
            all_quotations_invoiced=True,
        )
        no_quotation = SimpleNamespace(
            mapped=lambda _: [],
            all_quotations_invoiced=True,
        )

        SaleBlanketOrder._compute_all_quotations_invoiced(
            [all_invoiced, not_all_invoiced, no_quotation]
        )

        self.assertTrue(all_invoiced.all_quotations_invoiced)
        self.assertFalse(not_all_invoiced.all_quotations_invoiced)
        self.assertFalse(no_quotation.all_quotations_invoiced)

    def test_compute_revision_count(self):
        record = SimpleNamespace(revision_wizard_ids=[1, 2, 3], revision_count=0)

        SaleBlanketOrder._compute_revision_count([record])

        self.assertEqual(record.revision_count, 3)

    def test_action_view_revisions(self):
        order_with_revisions = SimpleNamespace(
            revision_wizard_ids=FakeRevisionLinks([11, 12]),
            ensure_one=lambda: True,
        )

        action = SaleBlanketOrder.action_view_revisions(order_with_revisions)
        self.assertEqual(action["res_model"], "sale.blanket.order")
        self.assertEqual(action["domain"], [("id", "in", [11, 12])])

        order_without_revisions = SimpleNamespace(
            revision_wizard_ids=FakeRevisionLinks([]),
            ensure_one=lambda: True,
        )
        close_action = SaleBlanketOrder.action_view_revisions(order_without_revisions)
        self.assertEqual(close_action["type"], "ir.actions.act_window_close")

    def test_set_to_draft_blocked_when_has_revisions(self):
        record = SimpleNamespace(revision_wizard_ids=[1])
        with self.assertRaises(UserError):
            SaleBlanketOrder.set_to_draft([record])

    def test_get_revision_count_recursive_chain(self):
        chain = {}
        env = FakeEnv(chain)
        first = FakeRevisionWizard(old_id=10, env=env)
        second = FakeRevisionWizard(old_id=20, env=env)
        third = FakeRevisionWizard(old_id=30, env=env)
        chain[10] = None
        chain[20] = first
        chain[30] = second

        self.assertEqual(first._get_revision_count(), 1)
        self.assertEqual(second._get_revision_count(), 2)
        self.assertEqual(third._get_revision_count(), 3)

    def test_get_next_revision_name(self):
        wizard = SimpleNamespace(
            old_blanket_order_id=SimpleNamespace(name="BO-001 (Rev 7)"),
            _get_revision_count=lambda: 8,
        )
        name = revision_wizard.SaleBlanketOrderRevisionWizard._get_next_revision_name(
            wizard
        )
        self.assertEqual(name, "BO-001 (Rev 8)")

    def test_update_blanket_order_lines_with_adjustment(self):
        old_line = FakeWritable(
            remaining_uom_qty=3.0,
            original_uom_qty=10.0,
            invoiced_uom_qty=4.0,
            contracted_quantity=0.0,
        )
        new_line = FakeWritable(
            original_uom_qty=0.0,
            contracted_quantity=0.0,
            price_unit=100.0,
        )
        old_order = FakeWritable(
            analytic_account_id=99,
            use_sale_order_plan=True,
            order_product_ids=[1],
            order_service_ids=[2],
            sale_order_plan_ids=[3],
            line_ids=[old_line],
        )
        new_order = FakeWritable(
            analytic_account_id=False,
            use_sale_order_plan=False,
            order_product_ids=[],
            order_service_ids=[],
            sale_order_plan_ids=[],
            line_ids=[new_line],
        )
        wizard = SimpleNamespace(adjustment_percentage=10.0)

        revision_wizard.SaleBlanketOrderRevisionWizard._update_blanket_order_lines(
            wizard, old_order, new_order
        )

        self.assertEqual(new_order.analytic_account_id, 99)
        self.assertEqual(new_line.original_uom_qty, 3.0)
        self.assertEqual(new_line.contracted_quantity, 10.0)
        self.assertAlmostEqual(new_line.price_unit, 110.0)
        self.assertEqual(old_line.contracted_quantity, 10.0)
        self.assertEqual(old_line.original_uom_qty, 4.0)
