# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@Diegoivanc>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "partner_commercial_name",
    "version": "10.0.1.0.0",
    "summary": "Nombre Comercial",
    "description": """
This module adds commercial name to a partner (individual or company),
you can search partner using name or commercial name on partners view,
creating a sale order or purchase.
""",
    "category": "Localization",
    "author": "EXA AUTO PARTS Github@exaap, "
              "DRACOSOFT Github@Diegoivanc, "
              "Joan Marín Github@joanmarin",
    "website": "http://www.dracosw.com",
    "license": "AGPL-3",
    "depends": ["base"],
    "data": [
        "views/res_partner_view.xml"
        ],
    "installable": True,
}
