# -*- coding: utf-8 -*-


from openerp import models, fields, api


class AssignTransportPosition(models.TransientModel):

    _name = 'kms.transport.assign_transport_position'

    trip_id = fields.Many2one('stock.kms.transport', string='Trip ID')
    line_ids = fields.One2many('kms.transport.assign_transport_position.line', inverse_name='assign_id', String='Lines')


class AssignTransportationPositionLine(models.TransientModel):

    _name = 'kms.transport.assign_transport_position.line'

    assign_id = fields.Many2one('kms.transport.assign_transport_position')
    city = fields.char()
