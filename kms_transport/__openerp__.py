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


{
    'name': 'KMS Transport',
    'version': '1.0',
    'author': 'Zakaria Makrelouf',
    'website': '',
    'category': 'Transport',
    'summary': 'Trasportation Module Tailored to KMS Business and WorkFlow',
    'depends': ['base', 'stock','fleet', 'web_kanban_gauge', 'delivery', 'report', 'product'],
    'description': """
KMS Transport module
===========================================

    """,
    'data': [
        'kms_transport_report.xml', 'kms_transport_view.xml', 'views/trip.xml', 'views/report_kmstransport.xml',
        'transport_data.xml',

    ],
    'demo': [],
    'test': [

    ],
    'installable': True,
    'auto_install': False,
    'qweb': ['static/src/xml/transport.xml'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
