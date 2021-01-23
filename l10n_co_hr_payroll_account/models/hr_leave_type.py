# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, _


class HrHolidaysType(models.Model):
    _description = "Types of absences"
    _inherit = "hr.leave.type"

    no_worked = fields.Boolean(
        string='Not worked',
        defualt=False,
        help=
        "Indicates that this type of absence is non-working, such as suspensions, unpaid leave, etc."
    )
    type_absence = fields.Selection(selection=[('vacaciones', 'Vacaciones'),
                                               ('incapacidad',
                                                'Incapacidades'),
                                               ('permiso', 'Permisos'),
                                               ('licencia', 'Licencias'),
                                               ('sancion', 'Sanciones')],
                                    string='Type of absence',
                                    required=True)
    paid = fields.Boolean(string='Paid',
                          defualt=False,
                          help="Indicates if the absence is paid or not")
