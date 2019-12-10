# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    rate_order = fields.Float(
        string='Rate',
        compute='_get_rate_order',
        digits=(12, 4))
    
    @api.multi
    def _get_rate_order(self):
        for order in self:
            company_currency = order.company_id.currency_id
            rate = 1

            if order.currency_id != company_currency:
                date_order = datetime.strptime(order.date_order, "%Y-%m-%d %H:%M:%S")
                date_order = date_order.strftime("%Y-%m-%d")
                currency = order.currency_id.with_context(
                    date=date_order or fields.Date.context_today(order))
                rate = currency.compute(rate, company_currency)
            
            order.rate_order = rate
    
    @api.multi
    def write(self, vals):
        rec = super(PurchaseOrder, self).write(vals)

        if vals.get('order_line'):
            for order in self:
                order.order_line._recompute_tax_id()
            '''
            for line in vals.get('order_line'):
                if line[0] == 2:
                    for order in self:
                        order.order_line._recompute_tax_id()

                    continue

                if not type(line[2]) is dict:
                    continue

                if ('price_unit' in line[2].keys()
                        or 'product_qty' in line[2].keys()
                        or 'discount' in line[2].keys()):
                    for order in self:
                        order.order_line._recompute_tax_id()

                    break
            '''
        return rec

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)

        for order in res:
            order.order_line._recompute_tax_id()

        return res

    @api.multi
    def _get_tax_groups(self):
        tax_groups = {}

        for line in self.order_line:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.taxes_id.compute_all(
                price_unit,
                self.currency_id,
                line.product_qty,
                product=line.product_id,
                partner=self.partner_id)['taxes']
            
            for tax in taxes:
                tax_id = self.env['account.tax'].browse(tax['id'])
                key = str(tax_id.tax_group_id.id)

                if key not in tax_groups:
                    values = {
                        'tax_group_id': tax_id.tax_group_id.id,
                        'base': tax['base'],
                        'amount': tax['amount']}
                    tax_groups[key] = values
                else:
                    tax_groups[key]['base'] += tax['base']
                    tax_groups[key]['amount'] += tax['amount']

        return tax_groups

    @api.multi
    def check_base_to_overcome(self):
        msg = _('There is no date range corresponding to the date of your order')

        if self.date_order:
            date_order = datetime.strptime(self.date_order, "%Y-%m-%d %H:%M:%S")
            date_order = date_order.strftime("%Y-%m-%d")
            param = [
                ('date_start', '<=', date_order),
                ('date_end', '>=', date_order)]
        else:
            param = [
                ('date_start', '<=', fields.Date.today()),
                ('date_end', '>=', fields.Date.today())]

        daterange = self.env['date.range'].search(param)

        if not daterange:
            raise UserError(msg)
        else:
            fiscalunit = daterange.fiscalunit

        tax_groups = self._get_tax_groups()
        remove_tax_groups_ids = []
                
        if tax_groups:
            for group_key in tax_groups.keys():
                tax_group_id = self.env['account.tax.group'].search(
                    [('id', '=', tax_groups[group_key]['tax_group_id'])])
                base_to_overcome = tax_group_id.fiscalunit_factor * fiscalunit
                base = tax_groups[group_key]['base'] * self.rate_order
                    
                if base_to_overcome > base:
                    remove_tax_groups_ids.append(tax_group_id)

        return remove_tax_groups_ids
