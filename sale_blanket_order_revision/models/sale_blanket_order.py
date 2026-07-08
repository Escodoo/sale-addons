# Copyright 2025 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleBlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    revision_wizard_ids = fields.One2many(
        comodel_name="sale.blanket.order.revision.wizard",
        inverse_name="old_blanket_order_id",
        string="Revision Wizards",
        help="References to the revision wizards associated with this blanket order.",
    )
    previous_blanket_order_id = fields.Many2one(
        comodel_name="sale.blanket.order",
        string="Previous Version",
        readonly=True,
        copy=False,
        help="Blanket order this record was revised from. Stored directly "
        "here (not only on the revision wizard) because the wizard is a "
        "transient record that Odoo eventually purges, which would "
        "otherwise break the revision history over time.",
    )
    has_revision_history = fields.Boolean(
        compute="_compute_has_revision_history",
    )
    has_next_revision = fields.Boolean(
        compute="_compute_has_next_revision",
    )

    all_quotations_invoiced = fields.Boolean(
        compute="_compute_all_quotations_invoiced",
        help="True if all related quotations are invoiced.",
    )

    def _compute_all_quotations_invoiced(self):
        for record in self:
            quotations = record.mapped("line_ids.sale_lines.order_id")
            if quotations:
                record.all_quotations_invoiced = all(
                    q.invoice_status == "invoiced" for q in quotations
                )
            else:
                record.all_quotations_invoiced = False

    def _get_revision_chain_ids(self):
        self.ensure_one()
        chain_ids = {self.id}

        current = self
        while (
            current.previous_blanket_order_id
            and current.previous_blanket_order_id.id not in chain_ids
        ):
            chain_ids.add(current.previous_blanket_order_id.id)
            current = current.previous_blanket_order_id

        current_id = self.id
        while True:
            next_order = self.search(
                [("previous_blanket_order_id", "=", current_id)], limit=1
            )
            if not next_order or next_order.id in chain_ids:
                break
            chain_ids.add(next_order.id)
            current_id = next_order.id

        return chain_ids

    @api.depends("previous_blanket_order_id", "revision_wizard_ids")
    def _compute_has_revision_history(self):
        for record in self:
            record.has_revision_history = len(record._get_revision_chain_ids()) > 1

    def _has_next_revision(self):
        self.ensure_one()
        return bool(self.search_count([("previous_blanket_order_id", "=", self.id)]))

    @api.depends("previous_blanket_order_id", "revision_wizard_ids")
    def _compute_has_next_revision(self):
        for record in self:
            record.has_next_revision = record._has_next_revision()

    def action_view_revisions(self):
        """Open a window to view all other versions of the blanket order,
        regardless of whether this record is the original or a revision."""
        self.ensure_one()

        other_ids = self._get_revision_chain_ids() - {self.id}

        if not other_ids:
            return {"type": "ir.actions.act_window_close"}

        return {
            "type": "ir.actions.act_window",
            "name": _("Revisions"),
            "res_model": "sale.blanket.order",
            "view_mode": "tree,form",
            "domain": [("id", "in", list(other_ids))],
        }

    def set_to_draft(self):
        """Restrict setting the order to draft if a later revision exists."""
        for record in self:
            if record._has_next_revision():
                raise UserError(
                    _(
                        "You cannot set this Blanket Order to Draft because "
                        "it has associated revisions."
                    )
                )
        return super().set_to_draft()
