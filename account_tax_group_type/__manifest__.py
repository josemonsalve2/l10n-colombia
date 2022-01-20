# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Tax Group Types",
    "category": "Financial",
    "version": "12.0.1.0.0",
    "author": "EXA Auto Parts Github@exaap, "
    "Joan Marín Github@JoanMarin, "
    "Alejandro Olano Github@alejo-code",
    "website": "https://github.com/odooloco/l10n-colombia",
    "license": "AGPL-3",
    "summary": "Types for Tax Groups",
    "depends": [
        "account_group_menu",
    ],
    "data": [
        'security/ir.model.access.csv',
        "views/account_tax_group_views.xml",
    ],
    "installable": True,
}
