# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Colombian Data Districts',
    'version': '12.0.1.1.0',
    'depends': ['l10n_co_base_location', 'base_location_districts'],
    'author': "EXA Auto Parts S.A.S - Alejandro Olano Github@alejo-code",
    'license': "AGPL-3",
    'summary': '''Enhanced base_location_districts with districts data.''',
    'data': [
        'data/res.city.zip.district.csv',
    ],
    'installable': True,
    'auto_install': False,
}
