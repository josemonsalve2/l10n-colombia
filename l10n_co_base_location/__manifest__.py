# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@JoanMarin> 
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Location management (aka Better ZIP) - Colombian Data",
    "summary": "Colombian Data ZIP/Cities, States and Countries",
    "version": "10.0.1.0.0",
    "license": "AGPL-3",
    "website": "https://www.exaap.com",
    "author": "EXA Auto Parts Github@exaap, "
              "Joan Marín Github@JoanMarin, "
              "Guillermo Montoya Github@guillermm",
    "category": "Localization",
    "depends": [
        "base_location"
    ],
    "data": [
        "data/res_country_data.xml",
        "data/res_country_state_data.xml",
        "data/res_better_zip_data.xml",
        "views/res_country_views.xml",
        "views/res_country_state_views.xml",
        "views/res_better_zip_views.xml",
        "views/res_partner_views.xml"
    ],
    "installable": True,
}