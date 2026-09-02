# -*- coding: utf-8 -*-
{
    'name': 'Cash Flow by Analytic Account',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Cash Flow statement report broken down and filtered by Analytic Accounts',
    'description': """
        Cash Flow by Analytic Account for Havano ERP.
        - Adds Analytic Accounts under Accounting Master.
        - Links Analytic Accounts to Sales, Expenses, and Payments.
        - Provides an interactive Cash Flow report filtered and column-grouped by Analytic Accounts.
        - Supports comparison periods (Previous Period, Same Period Last Year) and custom date ranges.
    """,
    'author': 'Havano',
    'depends': [
        'base',
        'web',
        'account',
        'account_reports',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/analytic_account_views.xml',
        'views/transaction_extensions_views.xml',
        'views/cashflow_report_override.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'havano_cashflow_analytic/static/src/scss/cashflow_analytic.scss',
            'havano_cashflow_analytic/static/src/js/cashflow_analytic.js',
            'havano_cashflow_analytic/static/src/xml/cashflow_analytic.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
