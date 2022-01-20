# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Tax on Purchase Order",
    "category": "Purchase",
    "version": "12.0.1.0.0",
    "author": "EXA Auto Parts Github@exaap, "
    "Alejandro Olano Github@alejo-code, "
    "Joan Marín Github@JoanMarin",
    "website": "https://github.com/exaap/l10n-colombia",
    "license": "AGPL-3",
    "summary": "This module allows to evaluate a tax at purchase order level, "
    "using parameters such as total base and others.",
    "depends": [
        "purchase_discount",
        "account_invoice_tax_fiscalunit",
    ],
    "data": [
        "views/purchase_order_views.xml",
    ],
    "installable": True,
    "auto_install": True,
}
