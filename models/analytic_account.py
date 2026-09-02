# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AnalyticAccount(models.Model):
    _name = 'havano.analytic.account'
    _description = 'Analytic Account'
    _order = 'code, name'

    _constraints = [
        models.Constraint('unique (name, company_id)', 'Analytic Account name must be unique per company!'),
        models.Constraint('unique (code, company_id)', 'Analytic Account code must be unique per company!'),
    ]

    name = fields.Char(string='Analytic Account Name', required=True)
    code = fields.Char(string='Reference / Code')
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}] {record.name}" if record.code else record.name
