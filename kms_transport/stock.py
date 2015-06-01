# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    
    _columns = {
        'address_id': fields.related('move_lines', 'partner_id', type='many2one', relation='res.partner', string='Address')
    }