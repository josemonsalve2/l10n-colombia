# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrContractRisk(models.Model):
    _name = 'hr.contract.risk'
    _description = 'Riesgos profesionales'

    code = fields.Char('Codigo', size=10, required=True)
    name = fields.Char('Nombre', size=100, required=True)
    percent = fields.Float('Porcentaje',
                           default=0,
                           required=True,
                           help="porcentaje del riesgo profesional")
    date = fields.Date('Fecha vigencia')
