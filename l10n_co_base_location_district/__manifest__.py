# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'l10n_co_base_location_districts',
    'version': '10.0.1.1.0',
    'depends': [
        'l10n_co_base_location','base_location_districts'
    ],
    'author': "EXA Auto Parts S.A.S -",
    'license': "AGPL-3",
    'summary': '''Enhanced base_location_districts with districts data.''',
    'data': [
            'data/res.better.zip.district.csv',
            ],
    'installable': True,
    'auto_install': False,
}
