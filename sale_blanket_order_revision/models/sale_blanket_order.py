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
    revision_count = fields.Integer(
        compute="_compute_revision_count",
        help="Count of revisions associated with this blanket order.",
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

    @api.depends("revision_wizard_ids")
    def _compute_revision_count(self):
        for record in self:
            record.revision_count = len(record.revision_wizard_ids)

    def action_view_revisions(self):
        """Open a window to view all revisions of the blanket order."""
        self.ensure_one()

        revision_ids = self.revision_wizard_ids.mapped("new_blanket_order_id.id")

        if not revision_ids:
            return {"type": "ir.actions.act_window_close"}

        return {
            "type": "ir.actions.act_window",
            "name": _("Revisions"),
            "res_model": "sale.blanket.order",
            "view_mode": "tree,form",
            "domain": [("id", "in", revision_ids)],
        }

    def set_to_draft(self):
        """Restrict setting the order to draft if there are associated revisions."""
        for record in self:
            if record.revision_wizard_ids:
                raise UserError(
                    _(
                        "You cannot set this Blanket Order to Draft because "
                        "it has associated revisions."
                    )
                )
        return super().set_to_draft()
