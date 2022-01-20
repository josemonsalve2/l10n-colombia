# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@JoanMarin>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name":
    "Account Tax on Invoice",
    "category":
    "Financial",
    "version":
    "12.0.1.0.0",
    "author":
    "EXA Auto Parts Github@exaap, "
    "Joan Marín Github@JoanMarin, "
    "Guillermo Montoya Github@guillermm, "
    "Alejandro Olano Github@alejo-code, "
    "Odoo Community Association (OCA)",
    "website":
    "https://github.com/odooloco/l10n-colombia",
    "license":
    "AGPL-3",
    "summary":
    "This module allows to evaluate a tax at invoice level, "
    "using parameters such as total base and others.",
    "depends": [
        "account_group_menu",
        "account_fiscal_year",
        "account_invoice_fiscal_position_update",
    ],
    "data": [
        "data/decimal_precision_data.xml", "views/account_invoice_views.xml",
        "views/account_tax_group_views.xml", "views/date_range_views.xml"
    ],
    "installable":
    True,
}
