# Copyright 2020 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.one
    @api.depends('product_id')
    def get_seller_count(self):
        for vendor in self:
            vendor.seller_count = len(
                self.env['product.supplierinfo'].search([('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)]))

    seller_count = fields.Integer(string="Number of vendor", compute=get_seller_count,
                                  help="Number of vendor prices for this product")

    @api.one
    @api.depends('product_id')
    def get_template_from_product(self):
        if self.product_id:
            self.product_tmpl_id = self.product_id.product_tmpl_id
        # field product template for domain in view

    product_tmpl_id = fields.Many2one('product.template', string="Product template",
                                      compute='get_template_from_product', store=True)

    seller_price = fields.Float('Seller Price',
                                compute="_get_supplierinfo_pricelist_price")

    seller_id = fields.Many2one('res.partner',
                                compute="_get_supplierinfo_pricelist_seller",
                                store=True,
                                string='Seller')

    ## Existe um problema quando muda a unidade de medida na linha de venda
    # baseado no modulo oca/product-attribute/'product_pricelist_supplierinfo',
    @api.one
    @api.depends('product_id', 'product_uom_qty')
    def _get_supplierinfo_pricelist_price(self):
        """Method for getting the price from supplier info."""
        self.ensure_one()
        if self.product_id:
            domain = [
                '|',
                ('product_id', '=', self.product_id.id),
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ]
        else:
            domain = [
                ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ]
        if self.product_uom_qty:
            domain += [
                '|',
                ('min_qty', '=', False),
                ('min_qty', '<=', self.product_uom_qty),
            ]
        if self.order_id.date_order:
            domain += [
                '|',
                ('date_start', '=', False),
                ('date_start', '<=', self.order_id.date_order),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', self.order_id.date_order),
            ]
        # We use a different default order because we are interested in getting
        # the price for lowest minimum quantity if no_supplierinfo_min_quantity
        supplierinfos = self.env['product.supplierinfo'].search(
            domain, order='min_qty,sequence,price',
        )
        price = supplierinfos[-1:].price
        if price:
            # We have to replicate this logic in this method as pricelist
            # method are atomic and we can't hack inside.
            # Verbatim copy of part of product.pricelist._compute_price_rule.
            qty_uom_id = self._context.get('uom') or self.product_id.uom_id.id
            price_uom = self.env['uom.uom'].browse([qty_uom_id])
            convert_to_price_uom = (
                lambda price: self.uom_id._compute_price(
                    price, price_uom))
        self.seller_price = price
        return

    @api.one
    @api.depends('product_id', 'product_uom_qty')
    def _get_supplierinfo_pricelist_seller(self):
        """Method for getting the price from supplier info."""
        self.ensure_one()
        if self.product_id:
            domain = [
                '|',
                ('product_id', '=', self.product_id.id),
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ]
        else:
            domain = [
                ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ]
        if self.product_uom_qty:
            domain += [
                '|',
                ('min_qty', '=', False),
                ('min_qty', '<=', self.product_uom_qty),
            ]
        if self.order_id.date_order:
            domain += [
                '|',
                ('date_start', '=', False),
                ('date_start', '<=', self.order_id.date_order),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', self.order_id.date_order),
            ]
        # We use a different default order because we are interested in getting
        # the price for lowest minimum quantity if no_supplierinfo_min_quantity
        supplierinfos = self.env['product.supplierinfo'].search(
            domain, order='min_qty,sequence,price',
        )
        price = supplierinfos[-1:].price
        if price:
            # We have to replicate this logic in this method as pricelist
            # method are atomic and we can't hack inside.
            # Verbatim copy of part of product.pricelist._compute_price_rule.
            qty_uom_id = self._context.get('uom') or self.product_id.uom_id.id
            price_uom = self.env['uom.uom'].browse([qty_uom_id])
            convert_to_price_uom = (
                lambda price: self.uom_id._compute_price(
                    price, price_uom))
        self.seller_id = supplierinfos[-1:].name
        return

    def _compute_margin(self, order_id, product_id, product_uom_id):
        frm_cur = self.env.user.company_id.currency_id
        to_cur = order_id.pricelist_id.currency_id
        purchase_price = self.seller_price
        if product_uom_id != product_id.uom_id:
            purchase_price = product_id.uom_id._compute_price(purchase_price, product_uom_id)
        price = frm_cur._convert(
            purchase_price, to_cur, order_id.company_id or self.env.user.company_id,
                                    order_id.date_order or fields.Date.today(), round=False)
        return price

    @api.onchange('product_uom_qty')
    def onchange_product_uom_qty(self):
        order_id = self.order_id
        product_id = self.product_id
        product_uom_id = self.product_uom
        self.purchase_price = self._compute_margin(order_id, product_id, product_uom_id)
        return

    @api.model
    def create(self, vals):
        vals.update(self._prepare_add_missing_fields(vals))

        # Calculation of the margin for programmatic creation of a SO line. It is therefore not
        # necessary to call product_id_change_margin manually
        if 'purchase_price' not in vals and ('display_type' not in vals or not vals['display_type']):
            order_id = self.env['sale.order'].browse(vals['order_id'])
            product_id = self.env['product.product'].browse(vals['product_id'])
            product_uom_id = self.env['uom.uom'].browse(vals['product_uom'])

            vals['purchase_price'] = self._compute_margin(order_id, product_id, product_uom_id)

        return super(SaleOrderLine, self).create(vals)
