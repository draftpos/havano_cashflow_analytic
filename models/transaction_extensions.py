# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    havano_analytic_account_id = fields.Many2one(
        'havano.analytic.account',
        string='Analytic Account',
        help='Analytic account assigned for cash flow tracking.'
    )

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    havano_analytic_account_id = fields.Many2one(
        'havano.analytic.account',
        string='Analytic Account',
        help='Analytic account assigned for cash flow tracking.'
    )

class AccountReport(models.Model):
    _inherit = 'account.report'

    def _init_options_user_groups(self, options, previous_options):
        super()._init_options_user_groups(options, previous_options)
        options['user_groups']['analytic_accounting'] = True

    def _init_options_analytic(self, options, previous_options):
        super()._init_options_analytic(options, previous_options)
        if self.filter_analytic:
            options['display_analytic'] = True



