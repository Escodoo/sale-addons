import re

from odoo import _, api, fields, models


class SaleBlanketOrderRevisionWizard(models.TransientModel):
    """Wizard to manage the revision process of Sale Blanket Orders."""

    _name = "sale.blanket.order.revision.wizard"
    _description = "Wizard for Sale Blanket Order Revision"

    old_blanket_order_id = fields.Many2one(
        comodel_name="sale.blanket.order",
        string="Old Blanket Order",
        help="Reference to the original blanket order before revision.",
        ondelete="cascade",
        readonly=True,
        required=True,
    )
    new_blanket_order_id = fields.Many2one(
        comodel_name="sale.blanket.order",
        string="Revised Blanket Order",
        help="Reference to the newly created blanket order revision.",
        ondelete="cascade",
        readonly=True,
    )
    adjustment_percentage = fields.Float(
        help="Percentage to adjust the unit price for each line in the blanket order.",
    )

    @api.model
    def default_get(self, fields_list):
        """Pre-fill the wizard with the selected blanket order."""
        defaults = super().default_get(fields_list)
        blanket_order_id = self.env.context.get("default_blanket_order_id")
        if blanket_order_id:
            defaults["old_blanket_order_id"] = blanket_order_id
        return defaults

    def _get_revision_count(self):
        """
        Counts how many revisions have been made for this blanket order.
        If `old_blanket_order_id` appears in previous revisions, increment the count.
        """
        count = 1  # Default revision count starts at 1

        # Check if the current blanket order has been revised before
        previous_revisions = (
            self.env["sale.blanket.order.revision.wizard"]
            .sudo()
            .search([("new_blanket_order_id", "=", self.old_blanket_order_id.id)])
        )

        if previous_revisions:
            count += (
                previous_revisions._get_revision_count()
            )  # Recursively count previous revisions

        return count

    def _get_next_revision_name(self):
        """
        Generate a sequential revision name based on the revision depth.
        """
        base_name = re.sub(r"\(Rev \d+\)$", "", self.old_blanket_order_id.name).strip()
        next_revision = self._get_revision_count()

        return _("%(base_name)s (Rev %(revision)s)") % {
            "base_name": base_name,
            "revision": next_revision,
        }

    def _update_blanket_order_lines(self, old_blanket_order, new_blanket_order):
        """
        Update the line values of both the original and revised blanket orders.
        """
        # Iterate over the lines of the old and new blanket orders simultaneously
        new_blanket_order.write(
            {
                "analytic_account_id": old_blanket_order.analytic_account_id,
                "use_sale_order_plan": old_blanket_order.use_sale_order_plan,
                "order_product_ids": old_blanket_order.order_product_ids,
                "order_service_ids": old_blanket_order.order_service_ids,
                "sale_order_plan_ids": old_blanket_order.sale_order_plan_ids,
            }
        )
        for old_line, new_line in zip(
            old_blanket_order.line_ids,
            new_blanket_order.line_ids,
            strict=True,
        ):
            # Update quantities in the new line
            new_line.write(
                {
                    "original_uom_qty": old_line.remaining_uom_qty,
                    "contracted_quantity": old_line.original_uom_qty,
                }
            )

            # Apply percentage adjustment if applicable
            if self.adjustment_percentage:
                new_line.price_unit *= 1 + (self.adjustment_percentage / 100)

            # Update the original line to reflect the revision
            old_line.write(
                {
                    "contracted_quantity": old_line.original_uom_qty,
                    "original_uom_qty": old_line.invoiced_uom_qty,
                }
            )

    def _copy_blanket_order(self):
        """Duplicate the blanket order while maintaining key values."""
        default_data = self.old_blanket_order_id.default_get([])
        default_data.update({"name": self._get_next_revision_name()})
        return self.old_blanket_order_id.copy(default_data)

    def create_revision(self):
        """Create a revised blanket order using
        the copy method with necessary updates."""
        for rec in self:
            new_blanket_order = rec._copy_blanket_order()
            rec.new_blanket_order_id = new_blanket_order.id

            # Link revision wizard to original blanket order
            rec.old_blanket_order_id.write({"revision_wizard_ids": [(4, rec.id)]})

            # Update both original and new blanket order lines
            self._update_blanket_order_lines(
                rec.old_blanket_order_id, new_blanket_order
            )

            # Log messages for tracking revision creation
            if hasattr(self, "message_post"):
                msg = _("New revision created: %s") % new_blanket_order.name
                new_blanket_order.message_post(body=msg)
                rec.old_blanket_order_id.message_post(body=msg)

        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "name": _("Revised Blanket Order"),
            "res_model": "sale.blanket.order",
            "res_id": self.new_blanket_order_id.id,
            "target": "current",
        }
