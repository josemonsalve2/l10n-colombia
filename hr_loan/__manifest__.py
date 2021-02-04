# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name':
    'Gestión de préstamos ',
    'version':
    '12.0.1.0.0',
    'category':
    'Generic Modules/Human Resources',
    'author': "Cybrosys Techno Solutions, EXA Auto Parts Github@exaap, Alejandro Olano Github@alejo-code",
    'depends': ['base', 'hr_payroll', 'hr', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_loan_seq.xml',
        'views/hr_loan.xml',
        'views/hr_payroll.xml',
    ],
    'demo': [],
    'license':
    'AGPL-3',
    'installable':
    True,
    'auto_install':
    False,
    'application':
    False,
}
