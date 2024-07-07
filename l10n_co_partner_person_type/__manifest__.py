# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Tipos de organización jurídica (Personas) para la localizacion Colombiana",
    "version": "17.0.0.0.0",
    "website": "https://github.com/exaap/exaap_modules",
    "author": "Joan Marín Github@JoanMarin, " "Alejandro Olano Github@alejo-code",
    "category": "Localization",
    "summary": "Este módulo tiene los tipos de organización jurídica (Personas) identificados "
    "por la DIAN para la localizacion Colombiana",
    "depends": ["partner_other_names", "account"],
    "data": [
        "views/res_partner_views.xml",
        "views/account_fiscal_position_views.xml",
    ],
    "installable": True,
}
