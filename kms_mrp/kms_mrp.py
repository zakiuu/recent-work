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

from openerp import models, fields, api

class MRPProduction(models.Model):
    _inherit = 'mrp.production'
    _inherits = {
        'mrp.production.crop': 'crop_id'
    }

    is_crop = fields.Boolean(string="Is Crop")
    crop_id = fields.Many2one('mrp.production.crop', string="Crop", ondelete="cascade")


class MrpProductionCrop(models.Model):

    _name = 'mrp.production.crop'

    #House Parameters
    crop_grower = fields.Many2one('res.partner', string="Grower", required=False, )
    farm_id = fields.Many2one('stock.location', string='Farm')
    house_id = fields.Many2one('stock.location', string='House')
    spawn_rate = fields.Float(string='Spawn Rate (%)')
    supplement_rate = fields.Float(string='Supplemt Rate (%)')

    # Crop Dates Event
    fill_date = fields.Datetime(string="Fill Date")
    spawn_date = fields.Date(string="Spawn Date")
    start_pick_date = fields.Date(string="Start Pick Date")
    stop_pick_date = fields.Date(string="Stop Pick Date")
    case_date = fields.Date(string="Case Date")
    clean_out_date = fields.Date(string="Clean Out Date")

    # Growing Parameters
    case_moisture = fields.Float(string="Case Moisture")
    peat_mixture = fields.Float(string="Peat Mixture")
    bare_hot_spot = fields.Float(string="Bare and Hot Spots")
    gmold = fields.Float(string="G-Mold")
    sciarids_seven_days = fields.Float(string="Sciarids at 7 Days")
    sciarids_at_pick = fields.Float(string="Sciarids at Pick")
    phorids_seven_days = fields.Float(string="Phorids at 7 Days")
    phorids_at_pick = fields.Float(string="Phorids at Pick")
    casing_ph = fields.Float(string="Casing pH")
    bubble = fields.Float(string="Bubble")
    bubble_bags = fields.Float(string="Bubble Bags")
    crop_comments = fields.Text(string="Comments")

    # Field Information
    first_break = fields.Date(string="1st Break")
    second_break = fields.Date(string="2nd Break")
    third_break = fields.Date(string="3rd Break")
    total_qty = fields.Float(string="Total LBS")
    total_revenue = fields.Float(string="Total Revenue")
    avg_revenue_sqft = fields.Float(string="Average Revenue / SQFT")
    avg_qty_sqft = fields.Float(string="Average LBS / SQFT")
    total_days_picking = fields.Float(string="Number of Days Picking")
    bio_efficiency = fields.Float(string="Bio Efficiency")
    dry_weight = fields.Float(string="Dry Weight")


class MrpProperty(models.Model):

    _inherit = 'mrp.property'

    partner_id = fields.Many2one('res.partner', string='Customer')


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):

        res = super(SaleOrderLine, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom,
                                                           qty_uos, uos, name, partner_id, lang, update_tax, date_order,
                                                           packaging, fiscal_position, flag, context)
        property_ids = []
        mrp_obj = self.pool.get('mrp.bom')
        bom_ids = mrp_obj.search(cr, uid, [('product_id','=', product)])
        for bom in mrp_obj.browse(cr, uid, bom_ids):
            for sale_property in bom.property_ids:
                property_ids.append(sale_property.id)

        res['domain'].update({'property_ids': [('id', 'in', property_ids), ('partner_id', '=', partner_id)]})
        return res









