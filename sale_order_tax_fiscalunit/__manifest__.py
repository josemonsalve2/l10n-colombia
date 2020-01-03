# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Tax on Sale Order",
    "category": "Sales",
    "version": "10.0.1.0.0",
    "author": "EXA Auto Parts Github@exaap, "
              "Joan Marín Github@JoanMarin",
    "website": "https://github.com/odooloco/l10n-colombia",
    "license": "AGPL-3",
    "summary": "This module allows to evaluate a tax at sale order level, "
               "using parameters such as total base and others.", 
    "depends": [
        "sale",
        "account_invoice_tax_fiscalunit",
    ],
    "data": [
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "auto_install": True,
}
