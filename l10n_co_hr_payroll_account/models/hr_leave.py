# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
import math
import datetime
from datetime import date
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class HrHolidays(models.Model):
    _description = "Leave"
    _inherit = "hr.leave"

    def _check_date_period(self):
        for holiday in self:
            if holiday.period_date_to:
                if holiday.period_date_to < holiday.period_date_from:
                    return False
        return True

    def _compute_days_real(self, cr, uid, ids, name, args, context=None):
        check_pool = self.pool.get('account.check')
        rs_data = {}

        employee_obj = self.pool.get('hr.employee')
        holidays_obj = self.pool.get('hr.holidays.public')
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

        for line in self.browse(cr, uid, ids, context=context):
            diff_day = 0.0
            f_desde = datetime.strptime(line.date_from, DATETIME_FORMAT).date()
            f_hasta = datetime.strptime(line.date_to, DATETIME_FORMAT).date()

            #Determina si el empleado trabaja el sabado y cuando sabado hay en el rango de fechas
            for emp in employee_obj.browse(cr,
                                           uid, [line.employee_id.id],
                                           context=None):
                sabado = emp.sabado

            diff_day = 0
            delta = timedelta(days=1)

            while f_desde <= f_hasta:
                if (not sabado and f_desde.strftime('%A').upper()
                        == 'SATURDAY') or (f_desde.strftime('%A').upper()
                                           == 'SUNDAY'):
                    print('Es sabado no habil o domingo')
                else:
                    if holidays_obj.is_public_holiday(cr,
                                                      uid,
                                                      f_desde,
                                                      context=None):
                        print('Es festivo')
                    else:
                        diff_day = diff_day + 1

                f_desde += delta

            rs_data[line.id] = diff_day

        return rs_data

    period_date_from = fields.Date(string='Period start date',
                                   states={
                                       'draft': [('readonly', False)],
                                       'confirm': [('readonly', False)]
                                   },
                                   select=True,
                                   copy=False)
    period_date_to = fields.Date(string='End date period',
                                 states={
                                     'draft': [('readonly', False)],
                                     'confirm': [('readonly', False)]
                                 },
                                 select=True,
                                 copy=False)
    date_medical_disability = fields.Date(string='Disability approval date',
                                          select=True,
                                          copy=False)
    number_of_days_real = fields.Float(string='Business days',
                                       compute='_compute_days_real',
                                       default=0.0,
                                       readonly=True,
                                       store=True)

    _constraints = [
        (_check_date_period,
         'The start date must be less than the greater date!',
         ['period_date_from', 'period_date_to']),
    ]

    @api.one
    @api.depends('period_date_from', 'period_date_to')
    def _compute_days_real(self):

        for line in self:
            line.number_of_days_real = 0

    def _get_number_of_days_new(self, date_from, date_to, employee_id):
        """Returns a float equals to the timedelta between two dates given as string."""

        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

        from_dt = datetime.datetime.strptime(date_from, DATETIME_FORMAT).date()
        to_dt = datetime.datetime.strptime(date_to, DATETIME_FORMAT).date()

        dias = 0
        delta = datetime.timedelta(days=1)
        while from_dt <= to_dt:
            dias = dias + 1
            if from_dt.month == 2:
                if from_dt.day == 28:
                    dias = dias + 2
                if from_dt.day == 29:
                    dias = dias + 1

            if (from_dt.month in (1, 3, 5, 7, 8, 10, 12)) and (from_dt.day
                                                               == 31):
                dias = dias - 1

            from_dt += delta

        return dias

    @api.onchange('date_from', 'date_to')
    def onchange_date_from(self):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (self.date_from
                and self.date_to) and (self.date_from > self.date_to):
            raise ValidationError(
                _('Warning!'),
                _('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if self.date_from and not self.date_to:
            #date_to_with_delta = datetime.datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=8)
            date_to_with_delta = datetime.strptime(
                self.date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT)
            result['value']['date_to'] = str(date_to_with_delta)

        # Compute and update the number of days
        if (self.date_to
                and self.date_from) and (self.date_from <= self.date_to):
            diff_day = self._get_number_of_days(self.date_from, self.date_to,
                                                self.employee_id.id)
            result['value']['number_of_days_temp'] = round(
                math.floor(diff_day))
        else:
            result['value']['number_of_days_temp'] = 0

        return result
