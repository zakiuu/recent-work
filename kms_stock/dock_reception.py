# -*- coding: utf-8 -*-
# #############################################################################
#
# OpenERP, Open Source Management Solution
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
from datetime import timedelta

from openerp.addons.mrp.mrp import mrp_production


class DockReception(models.Model):
    """
    This module aim to customize the reception of the mushroom from the farm houses to the
    Dock, by booking the hauler, the house and the grade of the mushroom.
    The user will be able to enter the total gross weight of the whole pallet.
    plus the number of units of the graded mushroom.
    The system will calculate the weight for each line using the following formula.
        1- set weight = gross weight - pallet weight - (total number of units * empty package weight)
        2-
    """

    _name = 'dock.reception'

    name = fields.Char(size=16, string='Reference', select=True, copy=False,
                       default='/')

    responsible_id = fields.Many2one('res.partner', string='Responsible', required=True)

    total_net_weight = fields.Float(string='Total Net Weight', compute='_total_net_weight')

    number_pallets = fields.Integer(string='Number of Pallets', compute='_number_of_pallets')

    reception_date = fields.Datetime(string='Reception Date', required=True, default=fields.datetime.today())

    reception_line = fields.One2many('dock.reception.line', 'dock_reception_id', 'Receptions')

    state = fields.Selection([('draft', "Draft"), ('confirmed', "Confirmed"), ('done', "Done")],
                             string='State', default='draft')




    @api.one
    @api.depends('reception_line')
    def _number_of_pallets(self):
        self.number_pallets = len(self.reception_line)

    @api.one
    @api.depends('reception_line')
    def _total_net_weight(self):
        net = 0
        for line in self.reception_line:
            net += line.net_weight
        self.total_net_weight = net

    @api.one
    def action_confirm(self):
        sequence_obj = self.env['ir.sequence']
        self.name = sequence_obj.get('dock.reception')
        self.state = 'confirmed'

    @api.one
    def action_done(self):

        manufacturing_obj = self.env['mrp.production']
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        transfer_obj_detail = self.env['stock.transfer_details']

        pack_obj = self.env['stock.quant.package']

        # loop around the reception lines
        for recep_line in self.reception_line:

            stock_picking_lines = []  # Contains the stock picking lines for stock picking obj generated
            transfer_detail_lines = []

            #Create the lot for the pallet

            # Create the Package for the pallet
            parent_pack = pack_obj.create({'ul_id' : recep_line.pallet_package.id})

            # for each line loop around the products received
            for line in recep_line.product_lines:
                # get the manufacturing order where the bill of material of the producted selected in the line
                #is ready to be produced.

                self.env.cr.execute('''
                                      select id
                                      from mrp_production m
                                      where m.location_src_id = %s
                                            and m.state in ('confirmed','ready','in_production')
                                            and m.product_id in
                                                (select l.product_id
                                                 from mrp_bom m, mrp_bom_line l
                                                 where m.id = l.bom_id and m.product_id =%s)
                                            ''', [line.location_id.id, line.product_id.id])

                production_id = self.env.cr.fetchall()[0][0]
                print "MANUFACTURING NUMBERSSS >>>>>>>>", production_id
                #Assuming that the bill of material contain only one product and the quantity of the main
                # product is equal to the product in the bill of material (ex 1 lb Product A -> 1  lb Product B)


                # Produce the same qty that user selected on the reception line
                # TODO Create lot for the production
                manufacturing_obj.action_produce(
                    production_id,
                    line.product_uom_qty, "consume_produce")

                # TODO : Create Manufacturing Order for the received order.

                # Create manufacturing order to grade the mushroom (e.x Convert a white medium
                # Mushroom to a Prime Mushroom)
                vals = {
                    'product_id': line.product_id.id,
                    'location_src_id': line.location_id.id,
                    'location_dest_id': 13,
                    'product_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'date_planned': self.reception_date
                }

                # select the right Bill of Material to be used in the manufacturing
                # depending on the variant of the product
                # Assuming the product is using variants

                bom_ids = self.env['mrp.bom'].search([('product_id', '=', line.product_id.id)])
                print "Bom >>>>>>>>>>>>>>>", bom_ids[0].id
                vals.update({'bom_id': bom_ids[0].id})

                # Create, confirm, assign, produce the manufacturing order.
                man_order = manufacturing_obj.create(vals)
                print "man_order >>>>>>>>>>>", man_order, man_order.id
                man_order.signal_workflow('button_confirm')
                man_order.action_assign()
                manufacturing_obj.action_produce(man_order.id, line.product_uom_qty, 'consume_produce')

                # Create the final picking lines.
                #TODO create stock move lines for the stock picking

                stock_picking_lines.append({
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'procure_method': 'make_to_stock',
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'date': self.reception_date,
                    'date_exptected': self.reception_date,
                    'invoice_state': 'none',
                    'description': line.product_id.name,
                    'location_id': 13,
                    'location_dest_id': line.destination_location_id.id,
                    'product_package': line.package_unit.id,
                })

                # Create Stock Picking Detail Line and packages

                #Create Lot
                lot = self.env['stock.production.lot'].create({'product_id': line.product_id.id})
                line.product_lot_id = lot
                #Create the package object for each preferred packaging

                number_of_package = int(line.product_uom_qty / line.package_unit.qty) # number of packs to create
                remaining_qty = line.product_uom_qty

                i = 0

                while i < number_of_package:

                    pack = pack_obj.create({'ul_id' : line.package_unit.ul.id, 'parent_id' : parent_pack.id})
                    transfer_detail_lines.append({
                        'product_id': line.product_id.id,
                        'destinationloc_id': line.destination_location_id.id,
                        'sourceloc_id': line.destination_location_id.id,
                        'product_uom_id': line.product_uom.id,
                        'date': self.reception_date,
                        'result_package_id': pack.id,
                        'quantity': line.package_unit.qty,
                        'lot_id': lot.id
                    })

                    remaining_qty = remaining_qty -  line.package_unit.qty
                    i += 1

                if remaining_qty > 0:
                    pack = pack_obj.create({'ul_id' : line.package_unit.ul.id, 'parent_id' : parent_pack.id})
                    transfer_detail_lines.append({
                        'product_id': line.product_id.id,
                        'destinationloc_id': line.destination_location_id.id,
                        'sourceloc_id': line.destination_location_id.id,
                        'product_uom_id': line.product_uom.id,
                        'date': self.reception_date,
                        'result_package_id': pack.id,
                        'quantity': remaining_qty,
                        'lot_id': lot.id
                    })


            picking_destination_location_id = line.destination_location_id.id

            # Create Stock Picking for all the reception Lines

            vals = {
                'partner_id': self.env.user.partner_id.id,
                'date': self.reception_date,
                #'move_lines' : stock_picking_lines,
                #'pack_operation_ids': package_lines,
                'picking_type_id': 8,
                'move_type': 'one',
                'invoice_state': 'none',
                'priority': '1'
            }

            picking_id = picking_obj.create(vals)

            # Create stock picking lines
            for pick_line in stock_picking_lines:
                pick_line.update({'picking_id': picking_id.id})
                move_obj.create(pick_line)

            picking_id.action_confirm()
            picking_id.action_assign()

            #create stock transfer details ( lots and packages )
            transfer_detail = transfer_obj_detail.create({'picking_id': picking_id.id,
                                                          'picking_source_location_id': 13,
                                                          'picking_destination_location_id': picking_destination_location_id})

            for transfer_line in transfer_detail_lines:
                transfer_line.update({'transfer_id': transfer_detail.id})
                self.env['stock.transfer_details_items'].create(transfer_line)

            transfer_detail.do_detailed_transfer()

            #Assign main package and stock picking to the reception line
            recep_line.picking_id = picking_id
            recep_line.package_id = parent_pack

        self.state = 'done'
        return True

class DockReceptionLine(models.Model):

    _name = 'dock.reception.line'

    #Select only packaging of type pallet
    pallet_package = fields.Many2one('product.ul', string='Pallet', required=True,
                                     domain=[('type', '=', 'pallet')])

    total_units_number = fields.Float(string="Total Units", compute="_total_units")

    gross_weight = fields.Float(string='Gross Weight')  # this field Should be required if is_weighted is TRUE

    net_weight = fields.Float(string='Net Weight' , compute='_total_net_weight')

    is_weighted = fields.Boolean(string='Is Weighted', default=True)

    dock_reception_id = fields.Many2one('dock.reception', string='Dock Reception')

    product_lines = fields.One2many('dock.reception.product', 'dock_reception_line_id', 'Product Lines')

    package_id = fields.Many2one(comodel_name="stock.quant.package", string="Package ID")

    picking_id = fields.Many2one('stock.picking', string="Stock Picking")


    @api.one
    @api.depends('product_lines')
    def _total_units(self):
        total_units = 0
        for line in self.product_lines:
            total_units += line.number_of_unit

        self.total_units_number = total_units


    # Make sure that the margin of error btw the computed gross weight and the calculate one from number of unit
    # is not higher than 10lb
    #TODO: Make it configurable by user in the setting menu
    @api.one
    @api.constrains('gross_weight')
    def _check_gross_weight(self):
        total_line_weight = 0
        total_empty_packages = 0
        for line in self.product_lines:
            total_line_weight += line.product_uom_qty
            total_empty_packages += line.package_unit.ul.weight

        calculated_gross_weight = total_empty_packages + total_line_weight + self.pallet_package.weight

        if self.is_weighted and abs(calculated_gross_weight - self.gross_weight) > 10:
            raise exceptions.ValidationError("The difference btw the total weight entered by user and calculated from"
                                             "the pallet line exceeded 10lb ")


    # Compute the total pallet net weight base on gross weight or total products net weight
    @api.one
    @api.depends('gross_weight', 'net_weight', 'product_lines')
    def _total_net_weight(self):
        net_weight = 0
        if self.is_weighted:
            self.net_weight = self.gross_weight - self.pallet_package.weight
        else:
            for line in self.product_lines:
                net_weight += line.product_uom_qty
            self.net_weight = net_weight


class DockReceptionProduct(models.Model):

    _name = "dock.reception.product"


    # Class Columns
    product_id = fields.Many2one('product.product', string='Product', required=True)

    location_id = fields.Many2one('stock.location', string='Source Location', required=True, )

    destination_location_id = fields.Many2one('stock.location', string='Destination Location', required=True)

    package_unit = fields.Many2one('product.packaging', string='Preferred Packaging', required=True)

    number_of_unit = fields.Integer(string='Total Unit', defaults=0, required=True)

    dock_reception_line_id = fields.Many2one('dock.reception.line', string='Dock Reception Line')

    product_uom_qty = fields.Float(string='Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
                                   defaults=0, compute='_product_qty')

    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True, )

    product_lot_id = fields.Many2one(comodel_name="stock.production.lot", string="Lot ID")

    # Make sure that the user enters a positive number of units
    @api.one
    @api.constrains('number_of_unit')
    def _check_product_uom_qty(self):
        if self.number_of_unit == 0:
            raise exceptions.ValidationError("Total Unit can't be Zero")



    #Compute the net product qty based the number of unit and the package unit
    @api.one
    @api.depends('number_of_unit', 'package_unit')
    def _product_qty(self):
        if self.package_unit:
            if self.package_unit.qty == 0:
                raise exceptions.ValidationError("Qty in the package unit can't be Zero")

            self.product_uom_qty = (self.number_of_unit * self.package_unit.qty) - \
                                   (self.number_of_unit * self.package_unit.ul.weight)



    # On Change Method for the Product
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        When the product is changed change set the unit of measure for the user.
        Reset the stock source location and the packaging unit used.
        Also this method allow user to only select location where the products in the Bom of
        the select product are being manufactured.

        :return: Location_id domain, product_uom, reset package_unit and location_id
        """
        # Select the right unit of measure
        self.product_uom = self.product_id.uom_id

        #Reset all the other fields
        self.location_id = None
        self.package_unit = None
        self.number_of_unit = 0
        self.product_uom_qty = 0

        #Allow the user to choose only the house where a crop is active
        location_ids = ()
        if self.product_id:
            self.env.cr.execute('''
            select l.id
            from stock_location l, mrp_production m
            where l.id = m.location_src_id and m.state in (\'confirmed\',\'ready\',\'in_production\')
            and m.product_id in (select l.product_id from mrp_bom m, mrp_bom_line l where m.id = l.bom_id and m.product_id = %s)
            ''', [self.product_id.id])

            for location_id in self.env.cr.fetchall():
                location_ids = location_ids + location_id

        return {
            'domain': {'location_id': [('id', 'in', location_ids)],
                       'package_unit': [('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)]},
        }




