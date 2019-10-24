# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@JoanMarin>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models, _


class RespartnerIsic(models.Model):
    _name = 'res.partner.isic'
    _description = 'ISIC Codes'

    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'code, name'
    _order = 'parent_left'

    name = fields.Char(
        string = 'Name',
        help = 'ISIC Name',
        required = True,
        index = 1)
    display_name = fields.Char(
        string = 'Display Name',
        compute = '_compute_display_name')
    code = fields.Char(
        string = 'Code',
        help = 'ISIC code',
        required = True,
        index = 1)
    note = fields.Text(
        string = 'Note')
    type = fields.Selection(
        string = 'Type',
        selection = [
            ('view','View'),
            ('other','Other')],
        help = 'Registry Type',
        required = True)
    parent_id = fields.Many2one(
        string = 'Parent',
        comodel_name = 'res.partner.isic',
        ondelete = 'set null')
    child_ids = fields.One2many(
        string = 'Childs Codes',
        comodel_name = 'res.partner.isic',
        inverse_name = 'parent_id')
    parent_left = fields.Integer(
        'Parent Left',
        index = 1)
    parent_right = fields.Integer(
        'Parent Right',
        index = 1)

    _sql_constraints = [
        ('name_uniq', 'unique (code)', _('The code of ISIC must be unique!'))]

    @api.depends('code','name')
    def _compute_display_name(self):
        for isic in self:
            isic.display_name = '[%s] %s' % (isic.code, isic.name)

    @api.model
    def name_search(self, name, args = None, operator = 'ilike', limit = 100):
        if not args:
            args = []

        if name:
            isic = self.search([
                '|',
                ('name', operator, name),
                ('code', operator, name)] + args, limit = limit)
        else:
            isic = self.search(args, limit = limit)

        return isic.name_get()

    @api.multi
    def name_get(self):
        res = []

        for record in self:
            name = u'[%s] %s' % (record.code, record.name)
            res.append((record.id, name))

        return res
