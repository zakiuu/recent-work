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


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def action_quick_sale(self):
        created_id = self.env['kms.sale.quick.sale'].with_context(active_model=self._name, active_ids=self.ids, active_id=self.ids[0]).create({'order_id': self.ids[0]})
        return created_id.wizard_view()

    @api.multi
    def action_create_claim(self):
        claim_obj = self.env['crm.claim']
        order = self.browse(self.ids[0])
        claim = claim_obj.create({
            'name': 'Claim for ' + str(order.name),
            'user_id': self._uid,
            'partner_id': order.partner_id.id,
            'partner_phone': order.partner_id.phone,
            'email_from': order.partner_id.email,
            'ref': str(self._name) + "," + str(self.ids[0]),
        })

        view = self.env.ref('kms_claims.kms_claims_form_view')
        print view
        return {
            'name': 'Claim for Order' + str(order.name),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.claim',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': claim.id,
            'context': self.env.context,
        }