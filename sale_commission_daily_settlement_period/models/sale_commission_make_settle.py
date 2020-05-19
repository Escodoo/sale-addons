# Copyright 2020 Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class SaleCommissionMakeSettle(models.TransientModel):

    _inherit = 'sale.commission.make.settle'

    def _get_period_start(self, agent, date_to):
        # res = super(SaleCommissionMakeSettle, self)._get_period_start(agent, date_to)
        if isinstance(date_to, str):
            date_to = fields.Date.from_string(date_to)
        if agent.settlement == 'monthly':
            return date(month=date_to.month, year=date_to.year, day=1)
        elif agent.settlement == 'quaterly':
            # Get first month of the date quarter
            month = (date_to.month - 1) // 3 * 3 + 1
            return date(month=month, year=date_to.year, day=1)
        elif agent.settlement == 'semi':
            if date_to.month > 6:
                return date(month=7, year=date_to.year, day=1)
            else:
                return date(month=1, year=date_to.year, day=1)
        elif agent.settlement == 'annual':
            return date(month=1, year=date_to.year, day=1)
        elif agent.settlement == 'daily':
            return date_to
        else:
            raise exceptions.Warning(_("Settlement period not valid."))

    def _get_next_period_date(self, agent, current_date):
        if isinstance(current_date, str):
            current_date = fields.Date.from_string(current_date)
        if agent.settlement == 'monthly':
            return current_date + relativedelta(months=1)
        elif agent.settlement == 'quaterly':
            return current_date + relativedelta(months=3)
        elif agent.settlement == 'semi':
            return current_date + relativedelta(months=6)
        elif agent.settlement == 'annual':
            return current_date + relativedelta(years=1)
        elif agent.settlement == 'daily':
            return current_date
        else:
            raise exceptions.Warning(_("Settlement period not valid."))
