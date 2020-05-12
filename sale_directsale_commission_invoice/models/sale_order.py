# Copyright 2020 Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commission_invoice_count = fields.Integer("Number of Purchase Order",
                                              compute='_compute_commission_invoice_count',
                                              groups='purchase.group_purchase_user') # TODO: Corrigir grupo

    @api.depends('order_line.commission_invoice_line_ids')
    def _compute_commission_invoice_count(self):
        commission_invoice_line_data = self.env['account.invoice.line'].read_group(
            [('directsale_sale_order_id', 'in', self.ids)],
            ['directsale_sale_order_id', 'commission_invoice_count:count_distinct(order_id)'], ['directsale_sale_order_id']
        )
        commission_invoice_count_map = {item['directsale_sale_order_id'][0]: item['commission_invoice_count'] for item in commission_invoice_line_data}
        for order in self:
            order.commission_invoice_count = commission_invoice_count_map.get(order.id, 0)

    @api.multi
    def _action_confirm(self):
        result = super(SaleOrder, self)._action_confirm()
        for order in self:
            order.order_line.sudo()._commission_invoice_service_generation()
        return result

    @api.multi
    def action_cancel(self):
        result = super(SaleOrder, self).action_cancel()
        # When a sale person cancel a SO, he might not have the rights to write
        # on PO. But we need the system to create an activity on the PO (so 'write'
        # access), hence the `sudo`.
        self.sudo()._activity_cancel_on_commission_invoice()
        return result

    @api.multi
    def action_view_commission_invoice(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [('id', 'in', self.mapped('order_line.commission_invoice_line_ids.order_id').ids)]
        return action

    @api.multi
    def _activity_cancel_on_commission_invoice(self):
        """ If some SO are cancelled, we need to put an activity on their generated purchase. If sale lines of
            differents sale orders impact different purchase, we only want one activity to be attached.
        """
        commission_invoice_to_notify_map = {}  # map PO -> recordset of SOL as {account.invoice: set(sale.orde.liner)}

        account_invoice_lines = self.env['account.invoice.line'].search([('directsale_sale_order_line_id', 'in', self.mapped('order_line').ids), ('state', '!=', 'cancel')])
        for commission_invoice_line in account_invoice_lines:
            commission_invoice_to_notify_map.setdefault(commission_invoice_line.order_id, self.env['sale.order.line'])
            commission_invoice_to_notify_map[commission_invoice_line.order_id] |= commission_invoice_line.directsale_sale_order_line_id

        for commission_invoice, sale_order_lines in commission_invoice_to_notify_map.items():
            commission_invoice.activity_schedule_with_view('mail.mail_activity_data_warning',
                user_id=commission_invoice.user_id.id or self.env.uid,
                views_or_xmlid='sale_directsale_commission_invoice.exception_purchase_on_sale_cancellation',
                render_context={
                    'sale_orders': sale_order_lines.mapped('order_id'),
                    'sale_order_lines': sale_order_lines,
            })


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    commission_invoice_line_ids = fields.One2many('account.invoice.line', 'directsale_sale_order_line_id', string="Generated Purchase Lines", readonly=True, help="Purchase line generated by this Sales item on order confirmation, or when the quantity was increased.")
    commission_invoice_line_count = fields.Integer("Number of generated purchase items", compute='_compute_commission_invoice_count')

    @api.multi
    @api.depends('commission_invoice_line_ids')
    def _compute_commission_invoice_count(self):
        database_data = self.env['account.invoice.line'].sudo().read_group([('directsale_sale_order_line_id', 'in', self.ids)], ['directsale_sale_order_line_id'], ['directsale_sale_order_line_id'])
        mapped_data = dict([(db['directsale_sale_order_line_id'][0], db['directsale_sale_order_line_id_count']) for db in database_data])
        for line in self:
            line.commission_invoice_line_count = mapped_data.get(line.id, 0)

    @api.onchange('product_uom_qty')
    def _onchange_service_product_uom_qty(self):
        if self.state == 'sale' and self.product_id.type == 'service' and self.product_id.service_to_commission_invoice:
            if self.product_uom_qty < self._origin.product_uom_qty:
                if self.product_uom_qty < self.qty_delivered:
                    return {}
                warning_mess = {
                    'title': _('Ordered quantity decreased!'),
                    'message': _('You are decreasing the ordered quantity! Do not forget to manually update the purchase order if needed.'),
                }
                return {'warning': warning_mess}
        return {}

    # --------------------------
    # CRUD
    # --------------------------

    @api.model
    def create(self, values):
        line = super(SaleOrderLine, self).create(values)
        # Do not generate purchase when expense SO line since the product is already delivered
        if line.state == 'sale' and not line.is_expense:
            line.sudo()._commission_invoice_service_generation()
        return line

    @api.multi
    def write(self, values):
        increased_lines = None
        decreased_lines = None
        increased_values = {}
        decreased_values = {}
        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            increased_lines = self.sudo().filtered(lambda r: r.product_id.service_to_commission_invoice and r.commission_invoice_line_count and float_compare(r.product_uom_qty, values['product_uom_qty'], precision_digits=precision) == -1)
            decreased_lines = self.sudo().filtered(lambda r: r.product_id.service_to_commission_invoice and r.commission_invoice_line_count and float_compare(r.product_uom_qty, values['product_uom_qty'], precision_digits=precision) == 1)
            increased_values = {line.id: line.product_uom_qty for line in increased_lines}
            decreased_values = {line.id: line.product_uom_qty for line in decreased_lines}

        result = super(SaleOrderLine, self).write(values)

        if increased_lines:
            increased_lines._commission_invoice_increase_ordered_qty(values['product_uom_qty'], increased_values)
        if decreased_lines:
            decreased_lines._commission_invoice_decrease_ordered_qty(values['product_uom_qty'], decreased_values)
        return result

    # --------------------------
    # Business Methods
    # --------------------------

    @api.multi
    def _commission_invoice_decrease_ordered_qty(self, new_qty, origin_values):
        """ Decrease the quantity from SO line will add a next acitivities on the related purchase order
            :param new_qty: new quantity (lower than the current one on SO line), expressed
                in UoM of SO line.
            :param origin_values: map from sale line id to old value for the ordered quantity (dict)
        """
        commission_invoice_to_notify_map = {}  # map PO -> set(SOL)
        last_commission_invoice_lines = self.env['account.invoice.line'].search([('directsale_sale_order_line_id', 'in', self.ids)])
        for commission_invoice_line in last_commission_invoice_lines:
            commission_invoice_to_notify_map.setdefault(commission_invoice_line.order_id, self.env['sale.order.line'])
            commission_invoice_to_notify_map[commission_invoice_line.order_id] |= commission_invoice_line.directsale_sale_order_line_id

        # create next activity
        for commission_invoice, sale_lines in commission_invoice_to_notify_map.items():
            render_context = {
                'sale_lines': sale_lines,
                'sale_orders': sale_lines.mapped('order_id'),
                'origin_values': origin_values,
            }
            commission_invoice.activity_schedule_with_view('mail.mail_activity_data_warning',
                user_id=commission_invoice.user_id.id or self.env.uid,
                views_or_xmlid='sale_directsale_commission_invoice.exception_commission_invoice_on_sale_quantity_decreased',
                render_context=render_context)

    @api.multi
    def _commission_invoice_increase_ordered_qty(self, new_qty, origin_values):
        """ Increase the quantity on the related purchase lines
            :param new_qty: new quantity (higher than the current one on SO line), expressed
                in UoM of SO line.
            :param origin_values: map from sale line id to old value for the ordered quantity (dict)
        """
        for line in self:
            last_commission_invoice_line = self.env['account.invoice.line'].search([('directsale_sale_order_line_id', '=', line.id)], order='create_date DESC', limit=1)
            if last_commission_invoice_line.state in ['draft', 'sent', 'to approve']:  # update qty for draft PO lines
                quantity = line.product_uom._compute_quantity(new_qty, last_commission_invoice_line.product_uom)
                last_commission_invoice_line.write({'product_qty': quantity})
            elif last_commission_invoice_line.state in ['purchase', 'done', 'cancel']:  # create new PO, by forcing the quantity as the difference from SO line
                quantity = line.product_uom._compute_quantity(new_qty - origin_values.get(line.id, 0.0), last_commission_invoice_line.product_uom)
                line._commission_invoice_service_create(quantity=quantity)

    @api.multi
    def _commission_invoice_get_write_date(self, supplierinfo):
        """ return the ordered date for the purchase order, computed as : SO commitment date - supplier delay """
        commitment_date = fields.Datetime.from_string(self.order_id.commitment_date or fields.Datetime.now())
        return commitment_date - relativedelta(days=int(supplierinfo.delay))

    @api.multi
    def _commission_invoice_service_prepare_order_values(self, supplierinfo):
        """ Returns the values to create the purchase order from the current SO line.
            :param supplierinfo: record of product.supplierinfo
            :rtype: dict
        """
        self.ensure_one()
        partner_supplier = supplierinfo.name
        fiscal_position_id = self.env['account.fiscal.position'].sudo().with_context(company_id=self.company_id.id).get_fiscal_position(partner_supplier.id)
        write_date = self._commission_invoice_get_write_date(supplierinfo)
        return {
            'partner_id': partner_supplier.id,
            'partner_ref': partner_supplier.ref,
            'company_id': self.company_id.id,
            'currency_id': partner_supplier.property_purchase_currency_id.id or self.env.user.company_id.currency_id.id,
            'dest_address_id': self.order_id.partner_shipping_id.id,
            'origin': self.order_id.name,
            'payment_term_id': partner_supplier.property_supplier_payment_term_id.id,
            'write_date': write_date,
            'fiscal_position_id': fiscal_position_id,
        }

    @api.multi
    def _commission_invoice_service_prepare_line_values(self, commission_invoice, quantity=False):
        """ Returns the values to create the purchase order line from the current SO line.
            :param commission_invoice: record of account.invoice
            :rtype: dict
            :param quantity: the quantity to force on the PO line, expressed in SO line UoM
        """
        self.ensure_one()
        # compute quantity from SO line UoM
        product_quantity = self.product_uom_qty
        if quantity:
            product_quantity = quantity

        purchase_qty_uom = self.product_uom._compute_quantity(product_quantity, self.product_id.uom_po_id)
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id

        # determine vendor (real supplier, sharing the same partner as the one from the PO, but with more accurate informations like validity, quantity, ...)
        # Note: one partner can have multiple supplier info for the same product
        supplierinfo = self.product_id._select_seller(
            partner_id=commission_invoice.partner_id,
            quantity=purchase_qty_uom,
            date=commission_invoice.write_date and commission_invoice.write_date.date(), # and commission_invoice.write_date[:10],
            uom_id=self.product_id.uom_po_id
        )
        fpos = commission_invoice.fiscal_position_id
        taxes = fpos.map_tax(self.product_id.supplier_taxes_id) if fpos else self.product_id.supplier_taxes_id
        if taxes:
            taxes = taxes.filtered(lambda t: t.company_id.id == self.company_id.id)

        # compute unit price
        price_unit = 0.0
        if supplierinfo:
            price_unit = self.env['account.tax'].sudo()._fix_tax_included_price_company(supplierinfo.price, self.product_id.supplier_taxes_id, taxes, self.company_id)
            if commission_invoice.currency_id and supplierinfo.currency_id != commission_invoice.currency_id:
                price_unit = supplierinfo.currency_id.compute(price_unit, commission_invoice.currency_id)

        # purchase line description in supplier lang
        product_in_supplier_lang = self.product_id.with_context({
            'lang': supplierinfo.name.lang,
            'partner_id': supplierinfo.name.id,
        })
        name = '[%s] %s' % (self.product_id.default_code, product_in_supplier_lang.display_name)
        if product_in_supplier_lang.description_purchase:
            name += '\n' + product_in_supplier_lang.description_purchase

        return {
            'name': '[%s] %s' % (self.product_id.default_code, self.name) if self.product_id.default_code else self.name,
            'product_qty': purchase_qty_uom,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': fields.Date.from_string(commission_invoice.write_date) + relativedelta(days=int(supplierinfo.delay)),
            'taxes_id': [(6, 0, taxes.ids)],
            'invoice_id': commission_invoice.id,
            'directsale_sale_order_line_id': self.id,
            'account_id': account.id,
        }

    @api.multi
    def _commission_invoice_service_create(self, quantity=False):
        """ On Sales Order confirmation, some lines (services ones) can create a purchase order line and maybe a purchase order.
            If a line should create a RFQ, it will check for existing PO. If no one is find, the SO line will create one, then adds
            a new PO line. The created purchase order line will be linked to the SO line.
            :param quantity: the quantity to force on the PO line, expressed in SO line UoM
        """
        AccountInvoice = self.env['account.invoice']
        supplier_po_map = {}
        sale_line_commission_invoice_map = {}
        for line in self:
            # determine vendor of the order (take the first matching company and product)
            suppliers = line.product_id.seller_ids.filtered(lambda vendor: (not vendor.company_id or vendor.company_id == line.company_id) and (not vendor.product_id or vendor.product_id == line.product_id))
            if not suppliers:
                raise UserError(_("There is no vendor associated to the product %s. Please define a vendor for this product.") % (line.product_id.display_name,))
            supplierinfo = suppliers[0]
            partner_supplier = supplierinfo.name  # yes, this field is not explicit .... it is a res.partner !

            # determine (or create) PO
            commission_invoice = supplier_po_map.get(partner_supplier.id)
            if not commission_invoice:
                commission_invoice = AccountInvoice.search([
                    ('partner_id', '=', partner_supplier.id),
                    ('state', '=', 'draft'),
                    ('company_id', '=', line.company_id.id),
                ], limit=1)
            if not commission_invoice:
                values = line._commission_invoice_service_prepare_order_values(supplierinfo)
                commission_invoice = AccountInvoice.create(values)
            else:  # update origin of existing PO
                so_name = line.order_id.name
                origins = []
                if commission_invoice.origin:
                    origins = commission_invoice.origin.split(', ') + origins
                if so_name not in origins:
                    origins += [so_name]
                    commission_invoice.write({
                        'origin': ', '.join(origins)
                    })
            supplier_po_map[partner_supplier.id] = commission_invoice

            # add a PO line to the PO
            values = line._commission_invoice_service_prepare_line_values(commission_invoice, quantity=quantity)
            commission_invoice_line = self.env['account.invoice.line'].create(values)

            # link the generated purchase to the SO line
            sale_line_commission_invoice_map.setdefault(line, self.env['account.invoice.line'])
            sale_line_commission_invoice_map[line] |= commission_invoice_line
        return sale_line_commission_invoice_map

    @api.multi
    def _commission_invoice_service_generation(self):
        """ Create a Purchase for the first time from the sale line. If the SO line already created a PO, it
            will not create a second one.
        """
        sale_line_commission_invoice_map = {}
        for line in self:
            # Do not regenerate PO line if the SO line has already created one in the past (SO cancel/reconfirmation case)
            if line.product_id.service_to_commission_invoice and not line.commission_invoice_line_count:
                result = line._commission_invoice_service_create()
                sale_line_commission_invoice_map.update(result)
        return sale_line_commission_invoice_map
