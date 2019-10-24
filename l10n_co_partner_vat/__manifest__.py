# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@JoanMarin>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Partner VAT Colombia",
    "summary": "Module for Type of Identification Document and Colombian NIT Checking.",
    "version": "10.0.1.0.0",
    "license": "AGPL-3",
    "website": "https://www.exaap.com",
    "author": "EXA Auto Parts Github@exaap, "
              "Joan Marín Github@JoanMarin, "
              "Guillermo Montoya Github@guillermm",
    "category": "Localization",
    "depends": [
        "base_vat"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/res_partner_document_type_data.xml", 
        "views/res_partner_views.xml"
    ],
    "installable": True,
}
