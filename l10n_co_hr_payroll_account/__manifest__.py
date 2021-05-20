# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@joanodoo>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).#).

{
    'name':
    'Nómina Colombia',
    'category':
    'Localization',
    'version':
    '11.0.1.0.0',
    'author':
    'EXA Auto Parts S.A.S - Alejandro Olano Github@alejo-code, '
    'Joan Marín Github@joanodoo, Guillermo Montoya Github@guillermm',
    'website':
    'http://www.exaap.com',
    'license':
    'AGPL-3',
    'summary':
    'Liquidación de Nómina - Colombia',
    'depends': ['hr_payroll_account'],
    'data': [
        'security/ir.model.access.csv', 'data/hr_contribution_register.xml',
        'data/hr_contract_risk.xml', 'views/hr_contract_risk.xml',
        'views/hr_contract.xml', 'views/hr_payslip.xml'
    ],
    'installable':
    True,
}