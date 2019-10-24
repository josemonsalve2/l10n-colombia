# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@JoanMarin>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Partner ISIC Codes",
    "summary": "ISIC Codes - Classification of Economic Activities ISIC",
    "version": "10.0.1.0.0",
    "license": "AGPL-3",
    "website": "https://www.exaap.com",
    "author": "EXA Auto Parts Github@exaap, "
              "Joan Marín Github@JoanMarin, "
              "Guillermo Montoya Github@guillermm",
    "category": "Localization",
    "depends": [
        "base"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/res.partner.isic.csv",
        "views/res_partner_isic_views.xml",
        "views/res_partner_views.xml"
    ],
    "installable": True,
}
