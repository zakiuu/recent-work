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
    'name': 'KMS Stock',
    'version': '1.0',
    'author': 'Zakaria Makrelouf',
    'website': '',
    'category': 'Manufacturing',
    'summary': 'Bug Fix and Manufacturing Process Customized for KMS Workflow',
    'depends': ['stock','mrp'],
    'description': """
KMS Stock customization module
===========================================


    """,
    'data': [
        'dock_reception_view.xml',
        'dock_reception_seq.xml',
        'dock_reception_report.xml',
        'views/report_dockreception.xml'
    ],
    'demo': [],
    'test': [

    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
