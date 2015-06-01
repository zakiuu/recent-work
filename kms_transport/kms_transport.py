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


class KMSTransport(models.Model):

    _name = 'stock.kms.transport'

    name = fields.Char("Name", required=True, default='/')

    trip_date = fields.Date(string="Trip Date", required=True, default=fields.Date.today())

    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('pending', 'Ready to Load'),
                              ('load', 'Loaded'),
                              ('delivery', 'Delivery'), ('done', 'Done')],
                             string="State", default='draft')

    trip_priority = fields.Selection([('normal', 'Normal'), ('low', 'Low'),('high', 'High')],
                                     string="Priority", default='normal', required=True)

    trip_type = fields.Selection([('regular', 'Regular'), ('LTL', 'Less Than Loaded'), ('FTL', 'Full truck Logistic')],
                                 string="Trip Type", default='regular', required=True)

    is_backhual = fields.Boolean(string="Backhual")
    is_pallet_exchange = fields.Boolean(string="Pallet Exch.")

    carrier_id = fields.Many2one("res.partner", string='Transport Company ', required=True)

    delivery_method = fields.Many2one("delivery.carrier", string="Final Destination", required=True)

    truck_id = fields.Many2one(comodel_name="fleet.vehicle", string="Truck",
                               required=True, domain=[('tag_ids', 'like', 'Truck')])
    truck_asset_number = fields.Char(string="Truck Unit #", related='truck_id.asset_number')

    starting_odometer = fields.Float(string="Starting Odometer", related="truck_id.odometer")

    ending_odometer = fields.Float(string="Ending Odometer")

    trailer_temp = fields.Float(string="Trailer Temp", required=True)

    trailer_number = fields.Many2one(comodel_name="fleet.vehicle",
                                     string="Trailer", domain=[('tag_ids', 'like', 'Trailer')])

    trailer_asset_number = fields.Char(string="Trailer Unit #", related='trailer_number.asset_number')

    driver_id = fields.Many2one(comodel_name="hr.employee", string="Driver", required=True)

    total_positions = fields.Integer(string="Total Positions")

    assigned_positions = fields.Integer(string="Assigned Positions", compute="_compute_positions")

    unassigned_positions = fields.Integer(string="Unassigned Positions", compute="_compute_positions")

    loaded_positions = fields.Integer(string="Loaded Positions", compute="_compute_positions")

    load_percentage = fields.Float(string="Load", compute="_compute_positions")

    open_positions = fields.Integer(string="Open Positions", compute="_compute_positions")

    full_percentage = fields.Float(string="Full (%)", compute="_compute_positions")

    stock_picking_ids = fields.One2many(comodel_name="stock.picking", inverse_name="trip_id", string="Delivery Orders")

    position_ids = fields.One2many(comodel_name="stock.kms.transport.position", inverse_name="trip_id", string="Trip Positions")

    comments = fields.Text(string="Comment")

    is_local = fields.Boolean(string='Local Trip')

    def create(self, cr, uid, vals, context):
        if vals['total_positions'] <= 0 and not vals['is_local']:
            raise exceptions.ValidationError('You must enter the total position available for this trip')
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'kms.transport.trip', context)
        return super(KMSTransport, self).create(cr, uid, vals, context)


    @api.one
    def action_generate_positions(self):
        if len(self.position_ids) < self.total_positions:
            position_obj = self.env['stock.kms.transport.position']
            if len(self.position_ids) == 0:
                i = 1
            else:
                i = len(self.position_ids) + 1

            while i <= self.total_positions:
                position_obj.create({
                    'name': i,
                    'trip_id': self.id,
                    'max_qty': 100,
                    'assigned_qty': 0,
                    'pallet_package': 2

                })
                i += 1
            return True
        else:
            raise exceptions.ValidationError("All the possible Position have been already generated")


    @api.one
    def action_confirm(self):
        self.state = 'confirm'

    @api.one
    def action_reset(self):
        self.state = 'draft'

    @api.one
    def action_mark_ready(self):
        for position in self.position_ids:
            if position.state not in ['loaded', 'built']:
                raise exceptions.ValidationError("Can't mark trip as Read. The Position %s isn't built yet"
                                                 % position.name)
        self.state = 'pending'

    @api.one
    def action_mark_loaded(self):
        transfer_obj_detail = self.env['stock.transfer_details']
        pack_obj = self.env['stock.quant.package']
        res = {}
        #Assert All positions are being marked as loaded
        for position in self.position_ids:
            if position.state != 'loaded':
                raise exceptions.ValidationError("Can't mark trip as loaded. The Position %s isn't loaded yet"
                                                 % position.name)

        #Create the stock transfer detail for each stock picking object
        # 1) each position is a pack (pallet)
        # 2) a pallet can contain multiple orders
        # 3) Assign position lines to the pack using the assigned qty
        # 4) create detail transfer for each stock picking object (order) in the trip
        # 5) process the stock picking.

        for position in self.position_ids:
            pack = pack_obj.create({'ul_id': position.pallet_package.id})
            for line in position.position_lines:
                lot = self.env['stock.production.lot'].create({'product_id': line.move_id.product_id.id})
                if line.move_id.picking_id.name in res:
                    res[line.move_id.picking_id.name].append(
                        {
                            'product_id': line.move_id.product_id.id,
                            'destinationloc_id': line.move_id.location_dest_id.id,
                            'sourceloc_id': line.move_id.location_id.id,
                            'product_uom_id': line.move_id.product_uom.id,
                            'date': position.load_time,
                            'result_package_id': pack.id,
                            'quantity': line.assigned_qty,
                            'lot_id': lot.id
                        }
                    )
                else:
                    res[line.move_id.picking_id.name] = [
                        {
                            'product_id': line.move_id.product_id.id,
                            'destinationloc_id': line.move_id.location_dest_id.id,
                            'sourceloc_id': line.move_id.location_id.id,
                            'product_uom_id': line.move_id.product_uom.id,
                            'date': position.load_time,
                            'result_package_id': pack.id,
                            'quantity': line.assigned_qty,
                            'lot_id': lot.id
                        }
                    ]

            #assign the package to the position
            position.package_id = pack

        source_location = position.position_lines[0].move_id.location_id.id
        destination_location = position.position_lines[0].move_id.location_dest_id.id

        for picking in self.stock_picking_ids:
            transfer_detail = transfer_obj_detail.create({'picking_id': picking.id,
                                                          'picking_source_location_id': source_location,
                                                          'picking_destination_location_id': destination_location})

            for transfer_line in res[picking.name]:
                transfer_line.update({'transfer_id': transfer_detail.id})
                self.env['stock.transfer_details_items'].create(transfer_line)

            transfer_detail.do_detailed_transfer()

        # for picking in self.stock_picking_ids:
        self.state = 'load'

    @api.one
    @api.depends('position_ids')
    def _compute_positions(self):
        self.assigned_positions = len(self.position_ids)
        self.loaded_positions = 0
        for position in self.position_ids:
            if position.state == 'loaded':
                self.loaded_positions += 1

        self.unassigned_positions = self.total_positions - self.assigned_positions
        self.open_positions = self.total_positions - self.loaded_positions
        if self.total_positions > 0:
            self.full_percentage = round(float(self.assigned_positions) / self.total_positions, 2) * 100
            self.load_percentage = round(float(self.loaded_positions) / self.total_positions, 2) * 100


    @api.multi
    def action_sale_orders(self):
        orders = []
        trip = self.ids[0]
        for order in self.browse(trip).stock_picking_ids:
            orders.append(str(order.origin).split(':')[0])

        sale_tree_view = self.env.ref('sale.view_order_tree')
        sale_form_view = self.env.ref('sale.view_order_form')
        search_view = self.env.ref('sale.view_sales_order_filter')

        return {
            'name': 'Trip Sale Orders',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(sale_tree_view.id, 'tree'),(sale_form_view.id, 'form')],
            #'view_id': search_view.id,
            'res_model': 'sale.order',
            'search_view_id': search_view.id,
            'domain': [('name', 'in', orders)],
        }

    @api.multi
    def open_barcode_interface(self):
        trip = self.browse(self.ids[0])
        if len(trip.stock_picking_ids) > 0 :
            final_url = "/trip/web/#action=transport.ui&trip_id=" + str(self.ids[0])
            return {'type': 'ir.actions.act_url', 'url': final_url, 'target': 'self'}
        else:
            raise exceptions.MissingError(" You mast assign orders to the trip before opening the pallet builder")

    #Return All the pallet Associated to an order in a trip for the web interface
    @api.multi
    def get_positions(self, picking_id):
        positions = []
        trip_id = self.ids[0]
        trip = self.browse(trip_id)
        for position in trip.position_ids:
            if position.picking_id.id == int(picking_id):
                ticket_id = None
                if position.weight_ticket_id:
                    ticket_id = position.weight_ticket_id.id
                pos = {
                    'positions': [],
                    'name': position.name,
                    'items': [],
                    'picking_id': position.picking_id.id,
                    'delete': False,
                    'new_name': None,
                    'bulk': position.is_bulk,
                    'ticket_id': ticket_id
                }
                j = 1
                while j <= trip.total_positions:
                    pos['positions'].append(j)
                    j += 1
                for line in position.position_lines:
                    pos['items'].append({
                        'seq': line.sequence ,
                        'product': line.move_id.product_id.name_get()[0][1],
                        'quantity': line.assigned_qty,
                        'delete': False,
                        'bulk': line.product_bulk
                    })
                positions.append(pos)
        print positions
        return positions

    @api.multi
    def get_order_lines(self, picking_id):
        order_lines = []
        trip_id = self.ids[0]
        trip = self.browse(trip_id)
        for order in trip.stock_picking_ids:
            if order.id == int(picking_id):
                for line in order.move_lines:
                    assigned_qty = 0
                    order_line ={
                        'product': line.product_id.name_get()[0][1],
                        'quantity': line.product_uom_qty,
                        'unit': line.product_uom.name}
                    unit_uom = self.env.ref('product.product_uom_unit')
                    if line.product_uom.name != unit_uom.name:
                        order_line.update({'bulk': True})
                        container_qty = line.product_packaging.qty
                        case_qty = int(line.product_uom_qty/ container_qty)
                        if line.product_uom_qty % container_qty:
                            case_qty +=1
                        order_line.update({'case_qty': case_qty})
                    else:
                        order_line.update({'bulk': False})

                        order_line.update({'case_qty': line.product_uom_qty})
                    for position in trip.position_ids:
                        for position_line in position.position_lines:
                            if line == position_line.move_id:
                                assigned_qty += position_line.assigned_qty
                    order_line.update({'remaining_qty': (order_line['case_qty'] - assigned_qty)})
                    order_lines.append(order_line)
        return order_lines

    @api.multi
    def get_customer_address(self, picking_id):
        address = ''
        trip = self.browse(self.ids[0])
        for order in trip.stock_picking_ids:
            if order.id == int(picking_id):
                if order.partner_id.street:
                    address += order.partner_id.street
                if order.partner_id.street2:
                    address += " " + order.partner_id.street2
                if order.partner_id.city:
                    address += " , " + order.partner_id.city
                if order.partner_id.state_id.code:
                    address += " , " + order.partner_id.state_id.code
                if order.partner_id.zip:
                    address += " , " + order.partner_id.zip

        return address

    @api.multi
    def update_pallets(self, picking_id, pallets):
        print pallets
        update_positions = []
        trip = self.browse(self.ids[0])
        for pallet in pallets:
            if pallet['delete']:
                for position in trip.position_ids:
                    if str(position.name) == str(pallet['name']):
                        position.unlink()
            else:
                pallet_found = False
                total_qty = 0
                for position in trip.position_ids:

                    if pallet['name'] == position.name and position.picking_id.id == picking_id and position not in update_positions:
                        pallet_found = True
                        i = 1
                        if pallet['new_name']:
                            i += 1
                            position.write({'name': pallet['new_name']})
                            update_positions.append(position)
                        for item in pallet['items']:
                            if item['delete']:
                                for line in position.position_lines:
                                    if line.move_id.product_id.name == item['product'].split('] ')[1]:
                                        line.unlink()
                            else:
                                found = False
                                if total_qty > 100:
                                    raise exceptions.Warning("A pallet can't have more than 100 unit(s), total is %s units" % total_qty)
                                for line in position.position_lines:
                                    if line.move_id.product_id.name == item['product'].split('] ')[1]:
                                        line.write({'assigned_qty': float(item['quantity']), 'sequence': int(item['seq'])})
                                        found = True
                                if not found:
                                    for order in trip.stock_picking_ids:
                                        if order.id == int(picking_id):
                                            for move in order.move_lines:
                                                if move.product_id.name == item['product'].split('] ')[1]:
                                                    unit_uom = self.env.ref('product.product_uom_unit')
                                                    if move.product_uom.name != unit_uom.name:
                                                        self.env['stock.kms.transport.position.line'].create({
                                                            'move_id': move.id,
                                                            'position_id': position.id,
                                                            'assigned_qty': int(item['quantity']),
                                                            'sequence': int(item['seq']),
                                                            'product_bulk': True
                                                        })
                                                        position.write({'is_bulk': True})
                                                    else:
                                                        self.env['stock.kms.transport.position.line'].create({
                                                            'move_id': move.id,
                                                            'position_id': position.id,
                                                            'assigned_qty': int(item['quantity']),
                                                            'sequence': int(item['seq']),
                                                            'product_bulk': False
                                                        })
                if not pallet_found:
                    print int(pallet['name'])
                    self.env['stock.kms.transport.position'].create({
                        'trip_id': trip.id,
                        'assigned_qty': 0,
                        'name': pallet['name'],
                        'picking_id': int(picking_id),
                        'state': 'draft',
                        'max_qty': 100,
                        'pallet_package': 2
                    })
        for position in trip.position_ids:
            print position.name
        return True


    @api.multi
    def do_print_order_tags(self, picking_id):
        tag_ids = []
        trip = self.browse(self.ids[0])
        for position in trip.position_ids:
            if position.picking_id.id == int(picking_id):
                tag_ids.append(position.id)

        return self.env["report"].with_context(active_ids=tag_ids).get_action(self.env['stock.kms.transport.position'],
                                                                              'kms_transport.report_pallet_tag')

    @api.multi
    def do_print_all_in_once_tags(self):
        return self.env["report"].with_context(active_ids=self.ids).get_action(self, 'kms_transport.report_pallet_tag_all_in_one')

    @api.multi
    def do_print_order_weight_tickets(self, picking_id):
        print picking_id

    @api.multi
    def do_print_all_in_once_tickets(self):
        print ""

    @api.multi
    def do_print_drop_sheet(self):
        return self.env["report"].with_context(active_ids=self.ids).get_action(self, 'kms_transport.report_trip_drop_sheet')

    @api.multi
    def do_print_pallet_tag(self, pallet_name):
        pallet_ids = []
        trip = self.browse(self.ids[0])
        for pallet in trip.position_ids:
            if pallet.name == int(pallet_name):
                pallet_ids.append(pallet.id)

        return self.env["report"].with_context(active_ids=pallet_ids).get_action(self.env['stock.kms.transport.position'], 'kms_transport.report_pallet_tag')

    @api.multi
    def do_create_weight_ticket(self, pallet):
        trip = self.browse(self.ids[0])
        for position in trip.position_ids:
            if position.name == int(pallet):
                ticket = self.env['kms.stock.weighting'].create({
                    'trip_id': trip.id,
                    'trip_position_id': position.id,
                    'user_id': self._uid,
                    'date': fields.datetime.today()
                })
                position.write({'weight_ticket_id': ticket.id})
                return ticket.id


class TripPosition(models.Model):

    _name = "stock.kms.transport.position"
    _order = 'name'

    name = fields.Integer(string="Position #", required=True, )
    trip_id = fields.Many2one(comodel_name='stock.kms.transport', string="Trip ID", ondelete='cascade')
    assigned_qty = fields.Float(string="Assign Qty", compute="_compute_assigned_qty")
    pallet_package = fields.Many2one('product.ul', string='Pallet', required=True,
                                     domain=[('type', '=', 'pallet')])
    max_qty = fields.Float(string="Max Qty", required=True)
    remaining_qty = fields.Float(string="Remain Qty", compute="_compute_assigned_qty")
    position_lines = fields.One2many(comodel_name='stock.kms.transport.position.line', inverse_name='position_id', string='Order Lines')
    state = fields.Selection([('draft', 'Pending'), ('built', 'Built'), ('loaded', 'Loaded')],
                             string='State', default='draft')
    built_user_id = fields.Many2one('res.users', string='Built by')
    built_time = fields.Datetime(string='Built at')
    load_user_id = fields.Many2one('res.users', string='Loaded By')
    load_time = fields.Datetime(string='Loaded at')
    package_id = fields.Many2one('stock.quant.package', String='Package')
    picking_id = fields.Many2one('stock.picking', string="Order ID")
    is_bulk = fields.Boolean(string='Contains Bulk Product', default=False)
    pallet_temperature = fields.Float(string='Pallet Temperature')
    temperature_user_id = fields.Many2one('res.users', string='Changed By')


    @api.one
    @api.onchange('pallet_temperature')
    def _onchange_pallet_temperature(self):
        self.temperature_user_id = self._uid

    @api.one
    def action_load(self):
        if self.pallet_temperature == 0:
            raise exceptions.ValidationError("The Pallet Temperature can't be Null")
        for line in self.position_lines:
            if line.move_id.state != 'assigned':
                raise exceptions.ValidationError("The product '%s' is not yet Ready, The pallet can't be loaded!" %
                                                 line.move_id.with_context(transport=True).name_get()[0][1])
        self.state = 'loaded'
        self.load_user_id = self._uid
        self.load_time = fields.datetime.today()


    @api.one
    def action_unload(self):
        self.state = 'built'
        self.load_user_id = None
        self.load_time = None


    @api.one
    def action_built(self):
        self.state = 'built'
        self.built_time = fields.datetime.today()
        self.built_user_id = self._uid


    @api.one
    def action_set_draft(self):
        self.state = 'draft'
        self.built_time = None
        self.built_user_id = None

    # Calculate Assigned Qty from lines
    @api.one
    @api.depends('position_lines', 'max_qty')
    def _compute_assigned_qty(self):
        self.assigned_qty = 0
        for line in self.position_lines:
            self.assigned_qty += line.assigned_qty

        self.remaining_qty = self.max_qty - self.assigned_qty


    # Calculate Remaining Qty
    @api.one
    @api.depends('position_lines', 'max_qty')
    def _compute_remaining_qty(self):
        assigned_qty = 0
        for line in self.position_lines:
            assigned_qty += assigned_qty + line.assigned_qty

        self.remaining_qty = self.max_qty - assigned_qty

    # Make sur the assigned qty isn't hire than the max_qty
    # Make sur the user doesn't add two similar lines in one position
    @api.one
    @api.constrains('position_lines')
    def _check_total_assigned_qty(self):
        assigned_qty = 0
        for line in self.position_lines:
            assigned_qty += line.assigned_qty
            for second_line in self.position_lines:
                if line.move_id == second_line.move_id and line.sequence != second_line.sequence:
                    raise exceptions.ValidationError("The Position: '%s' contains two similar product lines" % self.name)

        if assigned_qty > self.max_qty:
            raise exceptions.ValidationError("The Quantity Assigned in position %s is hire than the Max Qty" % self.name)



class TripPositionLines(models.Model):

    _name = "stock.kms.transport.position.line"
    _order = 'sequence'

    sequence = fields.Integer(string="Sequence", default=1)
    product_id = fields.Many2one('product.product', string='Product', related='move_id.product_id')
    assigned_qty = fields.Float(string="Assign Qty")
    product_qty = fields.Float(string="Qty", related="move_id.product_uom_qty")
    product_uom = fields.Many2one('product.uom', string="UoM", related="move_id.product_uom")
    partner_id = fields.Many2one('res.partner', string='Partner', related='move_id.partner_id')
    city = fields.Char(string='City', related='move_id.partner_id.city')
    remaining_qty = fields.Float(string='Remain Qty', related="move_id.trip_remaining_qty")
    position_id = fields.Many2one('stock.kms.transport.position', string="Position ID", ondelete='cascade')
    move_id = fields.Many2one('stock.move', string='Move')
    product_bulk = fields.Boolean(string="Bulk")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    trip_id = fields.Many2one(comodel_name="stock.kms.transport", string="Trip ID", )
    pallet_ids = fields.One2many(comodel_name='stock.kms.transport.position', inverse_name='picking_id',
                                 string='Transport Pallet')

class StockMove(models.Model):
    _inherit = 'stock.move'

    city = fields.Char(String='City', related='partner_id.city')
    trip_remaining_qty = fields.Float(string='Remain Qty', compute='_get_remaining_qty')



    @api.one
    def _get_remaining_qty(self):
        position_obj = self.env['stock.kms.transport.position.line']
        position_ids = position_obj.search([['move_id', '=', self.id]])
        total_assigned = 0
        for position in position_ids:
            total_assigned += position.assigned_qty

        self.trip_remaining_qty = self.product_uom_qty - total_assigned

    @api.one
    def name_get(self):
        if 'transport' in self._context:
            name = self.partner_id.name + " - " + self.product_id.name
            if self.picking_id.origin:
                name = str(self.picking_id.origin).split(':')[0] + " : " + name
            return (self.id, name)
        else:
            return super(StockMove, self).name_get()[0]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_transport = fields.Boolean(string='Transport Company', default=False)


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    asset_number = fields.Char(string='UNIT #', help="Asset Number of the Vehicle/Trailer")