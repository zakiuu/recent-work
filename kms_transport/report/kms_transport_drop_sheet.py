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


# from openerp import api, models
#
# class ReportDropSheet(models.AbstractModel):
#     _name = 'report.kms_transport.report_trip_drop_sheet'
#
#     @api.multi
#     def render_html(self, data=None):
#         report_obj = self.env['report']
#
#         print "I'm heeeeeerreeeee"
#
#         report = report_obj._get_report_from_name('kms_transport.report_trip_drop_sheet')
#         docargs = {
#             'doc_ids': self._ids,
#             'doc_model': report.model,
#             'docs': self,
#             'test': self.test(),
#         }
#         return report_obj.render('kms_transport.report_trip_drop_sheet', docargs)
#
#     def test(self):
#         return "Test"



from openerp.report import report_sxw
from openerp.osv import osv
import time


class report_drop_sheet(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_drop_sheet, self).__init__(cr, uid, name, context = context)
        self.localcontext.update({
            'time': time,
            'get_orders': self.get_lines,
            'get_delivery_orders': self.get_delivery_orders
        })

    def get_lines(self, trip):
        res = []
        for order in trip.stock_picking_ids:
            pallets = 0
            drop = 1
            found = False
            line = {'customer': order.partner_id.name,
                    'delivery_time': order.min_date,
                    'order': str(order.origin).split(':')[0],
                    'phone': order.partner_id.phone,
                    'destination': order.partner_id.city
                    }
            for position in trip.position_ids:
                for l in position.position_lines:
                    if l.move_id.picking_id == order:
                        if not found:
                            drop = trip.total_positions - position.name
                            if drop == 0:
                                drop = 1
                            found = True
                            pallets += 1
                            break
                        else:
                            pallets += 1
                            break

                line.update({
                    'pallets': pallets,
                    'drop': drop
                })

            res.append(line)
        return res

    def get_delivery_orders(self, trip):
        # sale_obj = self.pool.get['sale.order']
        res = []
        delivery_obj = self.pool.get('stock.picking')
        orders = []
        for picking in trip.stock_picking_ids:
            orders.append(str(picking.origin).split(':')[0],)

        delivery_ids = delivery_obj.search(self.cr, self.uid, [('origin', 'in', orders)])
        print delivery_ids, "BLAAAAAAAA", delivery_obj.browse(self.cr, self.uid, delivery_ids)
        for delivery in delivery_obj.browse(self.cr, self.uid, delivery_ids):
            res.append(delivery)

        print res
        return res


class report_kms_transport_drop_sheet(osv.AbstractModel):
    _name = 'report.kms_transport.report_trip_drop_sheet'
    _inherit = 'report.abstract_report'
    _template = 'kms_transport.report_trip_drop_sheet'
    _wrapped_report_class = report_drop_sheet