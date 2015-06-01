# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, exceptions
import openerp.addons.decimal_precision as dp

class QuickSale(models.TransientModel):

    _name = 'kms.sale.quick.sale'

    order_id = fields.Many2one('sale.order', string='Sale Order')
    quick_sale_lines = fields.One2many('kms.sale.quick.sale.line', 'quick_sale_id', string='Quick Sale Lines')

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}

        res = super(QuickSale, self).default_get(cr, uid, fields, context=context)
        sale_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not sale_ids or len(sale_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res

        assert active_model in ('sale.order'), 'Bad context propagation'
        sale_id, = sale_ids
        order = self.pool.get('sale.order').browse(cr, uid, sale_id, context=context)
        items = []
        if not order.pricelist_id:
            raise exceptions.ValidationError("You have to select a price list "
                                             "in the order to be able to add quick items")


        pricelist_version = order.pricelist_id.version_id[0]

        for item in pricelist_version.items_id :
            if item.product_id:
                line = {
                    'product_id' : item.product_id.id,
                    'product_uom': item.product_id.uom_id.id,
                    'product_uom_qty': 0,
                }
                price = self.pool.get('product.pricelist').price_get(cr, uid, [order.pricelist_id.id],
                                                                     item.product_id.id, 1.0, order.partner_id.id,
                                                                     {
                                                                         'uom': item.product_id.uom_id.id,
                                                                         'date': order.date_order
                                                                     })[order.pricelist_id.id]

                if not price:
                    raise exceptions.ValidationError("Error in getting item prices contact your Administrator")

                line.update({'price_unit': price})


                for order_line in order.order_line:
                    if order_line.product_id.id == line['product_id']:
                        line['product_uom_qty'] = order_line.product_uom_qty
                        line['price_unit'] = order_line.price_unit

                items.append(line)

        res.update(quick_sale_lines=items)
        return res

    @api.multi
    def wizard_view(self):
        view = self.env.ref('kms_sale.kms_sale_quick_sale_form')

        return {
            'name': 'Add Items',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'kms.sale.quick.sale',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context,
        }

    @api.one
    def action_add_item(self):
        for item in self.quick_sale_lines:
            sale_line = {}
            update = True
            if item.product_uom_qty > 0:
                for order_line in self.order_id.order_line:
                    if order_line.product_id == item.product_id:
                        order_line.write({'product_uom_qty': item.product_uom_qty,
                                          'price_unit': item.price_unit})
                        update = False

                if update:
                    sale_line.update({
                        'product_id': item.product_id.id,
                        'product_uom': item.product_uom.id,
                        'product_uom_qty': item.product_uom_qty,
                        'price_unit': item.price_unit,
                        'order_id': self.order_id.id,
                    })
                    name = item.product_id.name_get()[0][1]
                    if item.product_id.description_sale:
                        name = '\n' + item.product_id.description_sale
                    sale_line.update({'name': name})
                    fpos = self.order_id.partner_id.property_account_position or False
                    if fpos:
                        sale_line['tax_id'] = fpos.map_tax(item.product_id.taxes_id)

                    #add a default property if property found for the chosen product for the order partner
                    property_ids = []
                    bom_obj = self.env['mrp.bom']
                    bom_ids = bom_obj.search([('product_id', '=', item.product_id.id)])
                    print "BOOOOOOOOOOM", bom_ids
                    for bom in bom_ids:
                        for sale_property in bom.property_ids:
                            if sale_property.partner_id == self.order_id.partner_id:
                                property_ids.append(sale_property.id)
                    sale_line.update({'property_ids': [(6, False, property_ids)]})

                    print "BOOOOOOOOOOM33333", sale_line
                    self.env['sale.order.line'].create(sale_line)

        return True


class QuickSaleLine(models.TransientModel):

    _name = 'kms.sale.quick.sale.line'

    quick_sale_id = fields.Many2one('kms.sale.quick.sale', string="Quick Sale")
    product_id = fields.Many2one('product.product', string='Product', required=True)
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    product_uom = fields.Many2one('product.uom', string='UoM', required=True)
    product_uom_qty = fields.Float(string='Qty', digits=dp.get_precision('Product UoS'), required=True)
