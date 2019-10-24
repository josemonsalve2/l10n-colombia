# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Tax Group Types",
    "category": "Financial",
    "version": "10.0.1.0.0",
    "author": "EXA Auto Parts Github@exaap, "
              "Joan Marín Github@JoanMarin",
    "website": "http://www.exaap.com",
    "license": "AGPL-3",
    "summary": "Types for Tax Groups", 
    "depends": [
        "account_tax_group_menu",
    ],
    "data": [
        'security/ir.model.access.csv',
        "views/account_tax_group_views.xml",
    ],
    "installable": True,
}
