# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@joanodoo> 
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).#

{
    'name': 'Workshop',
    'category': 'Sale',
    'version': '12.0.1.0.0',
    'author': 'Joan Marín Github@joanodoo, '
              'Guillermo Montoya Github@guillermm',
    'website': 'http://www.exaap.com',
    'license': 'AGPL-3',
    'summary': 'Functionalities for the operation of a vehicle workshop Odoo version 12',
    'depends': [
        'sale',
        'fleet'
    ],
    'data': [
        'views/account_invoice.xml',
        'views/sale_order.xml'
    ],
    'installable': True,
}