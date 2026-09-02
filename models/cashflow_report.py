# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

class CashFlowAnalyticReport(models.AbstractModel):
    _name = 'havano.cashflow.analytic.report'
    _description = 'Cash Flow by Analytic Account Report Data'

    @api.model
    def get_available_analytic_accounts(self):
        domain = [('active', '=', True), ('company_id', '=', self.env.company.id)]
        accounts = self.env['havano.analytic.account'].sudo().search_read(
            domain, ['id', 'name', 'code']
        )
        for acc in accounts:
            label = f"[{acc['code']}] {acc['name']}" if acc.get('code') else acc['name']
            acc['display_name'] = label
        return accounts

    @api.model
    def get_report_data(self, date_from=None, date_to=None, analytic_account_ids=None, comparison='none'):
        company_id = self.env.company.id

        domain_move_out = [('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted'), ('company_id', '=', company_id)]
        domain_move_in = [('move_type', 'in', ['in_invoice', 'in_refund']), ('state', '=', 'posted'), ('company_id', '=', company_id)]
        domain_payment = [('state', '=', 'posted'), ('company_id', '=', company_id)]

        comp_domain_move_out = [('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted'), ('company_id', '=', company_id)]
        comp_domain_move_in = [('move_type', 'in', ['in_invoice', 'in_refund']), ('state', '=', 'posted'), ('company_id', '=', company_id)]
        comp_domain_payment = [('state', '=', 'posted'), ('company_id', '=', company_id)]

        if date_from:
            domain_move_out.append(('invoice_date', '>=', date_from))
            domain_move_in.append(('invoice_date', '>=', date_from))
            domain_payment.append(('date', '>=', date_from))
        if date_to:
            domain_move_out.append(('invoice_date', '<=', date_to))
            domain_move_in.append(('invoice_date', '<=', date_to))
            domain_payment.append(('date', '<=', date_to))

        has_comparison = comparison in ['previous_period', 'previous_year'] and date_from and date_to

        if has_comparison:
            dt_from = datetime.strptime(date_from[:10], '%Y-%m-%d')
            dt_to = datetime.strptime(date_to[:10], '%Y-%m-%d')

            if comparison == 'previous_year':
                comp_from = (dt_from - relativedelta(years=1)).strftime('%Y-%m-%d')
                comp_to = (dt_to - relativedelta(years=1)).strftime('%Y-%m-%d')
            else:
                delta = dt_to - dt_from
                comp_to = (dt_from - relativedelta(days=1))
                comp_from = comp_to - delta
                comp_to = comp_to.strftime('%Y-%m-%d')
                comp_from = comp_from.strftime('%Y-%m-%d')

            comp_domain_move_out.append(('invoice_date', '>=', comp_from))
            comp_domain_move_out.append(('invoice_date', '<=', comp_to))
            comp_domain_move_in.append(('invoice_date', '>=', comp_from))
            comp_domain_move_in.append(('invoice_date', '<=', comp_to))
            comp_domain_payment.append(('date', '>=', comp_from))
            comp_domain_payment.append(('date', '<=', comp_to))

        # Analytic accounts to process
        selected_accounts = []
        if analytic_account_ids:
            recs = self.env['havano.analytic.account'].browse(analytic_account_ids)
            for r in recs:
                if r.exists():
                    label = f"[{r.code}] {r.name}" if r.code else r.name
                    selected_accounts.append({'id': r.id, 'name': label})
        else:
            domain = [('active', '=', True), ('company_id', '=', company_id)]
            recs = self.env['havano.analytic.account'].search(domain)
            for r in recs:
                label = f"[{r.code}] {r.name}" if r.code else r.name
                selected_accounts.append({'id': r.id, 'name': label})

        selected_accounts.append({'id': 'unassigned', 'name': 'General / Unassigned'})
        selected_accounts.append({'id': 'total', 'name': 'Total'})

        columns = []
        for acc in selected_accounts:
            if has_comparison:
                columns.extend([acc['name'], f"{acc['name']} (Prev)", f"{acc['name']} (%)"])
            else:
                columns.append(acc['name'])

        report_data = {
            'columns': columns,
            'operating_inflows': {},
            'total_inflows': {col: 0.0 for col in columns},
            'operating_outflows': {},
            'total_outflows': {col: 0.0 for col in columns},
            'net_cashflow': {col: 0.0 for col in columns},
        }

        def calculate_percent(current, previous):
            if previous == 0:
                return 100.0 if current > 0 else (0.0 if current == 0 else -100.0)
            return ((current - previous) / abs(previous)) * 100.0

        def process_dataset(dom_out, dom_in, dom_p, is_comparison=False):
            # 1. Customer Invoices (Sales Cash Inflows)
            moves_out = self.env['account.move'].sudo().search(dom_out)
            for m in moves_out:
                amt = float(m.amount_total or 0.0)
                if m.move_type == 'out_refund':
                    amt = -abs(amt)
                
                acc = getattr(m, 'havano_analytic_account_id', False)
                acc_name = 'General / Unassigned'
                if acc:
                    code_prefix = f"[{acc.code}] " if acc.code else ""
                    acc_name = f"{code_prefix}{acc.name}"

                line_name = "Customer Sales Receipts"
                if line_name not in report_data['operating_inflows']:
                    report_data['operating_inflows'][line_name] = {col: 0.0 for col in columns}

                targets = [f"Total{' (Prev)' if is_comparison else ''}"]
                if acc_name:
                    targets.append(f"{acc_name}{' (Prev)' if is_comparison else ''}")

                for t in targets:
                    if t in report_data['operating_inflows'][line_name]:
                        report_data['operating_inflows'][line_name][t] += amt
                    if t in report_data['total_inflows']:
                        report_data['total_inflows'][t] += amt

            # 2. Payments
            payments = self.env['account.payment'].sudo().search(dom_p)
            for p in payments:
                amt = float(p.amount or 0.0)
                acc = getattr(p, 'havano_analytic_account_id', False)
                acc_name = 'General / Unassigned'
                if acc:
                    code_prefix = f"[{acc.code}] " if acc.code else ""
                    acc_name = f"{code_prefix}{acc.name}"

                targets = [f"Total{' (Prev)' if is_comparison else ''}"]
                if acc_name:
                    targets.append(f"{acc_name}{' (Prev)' if is_comparison else ''}")

                if p.payment_type == 'inbound':
                    line_name = "Other Inbound Receipts"
                    if line_name not in report_data['operating_inflows']:
                        report_data['operating_inflows'][line_name] = {col: 0.0 for col in columns}
                    for t in targets:
                        if t in report_data['operating_inflows'][line_name]:
                            report_data['operating_inflows'][line_name][t] += amt
                        if t in report_data['total_inflows']:
                            report_data['total_inflows'][t] += amt
                elif p.payment_type == 'outbound':
                    line_name = "Supplier & Direct Payments"
                    if line_name not in report_data['operating_outflows']:
                        report_data['operating_outflows'][line_name] = {col: 0.0 for col in columns}
                    for t in targets:
                        if t in report_data['operating_outflows'][line_name]:
                            report_data['operating_outflows'][line_name][t] += amt
                        if t in report_data['total_outflows']:
                            report_data['total_outflows'][t] += amt

            # 3. Vendor Bills (Cash Outflows)
            moves_in = self.env['account.move'].sudo().search(dom_in)
            for m in moves_in:
                amt = float(m.amount_total or 0.0)
                if m.move_type == 'in_refund':
                    amt = -abs(amt)

                acc = getattr(m, 'havano_analytic_account_id', False)
                acc_name = 'General / Unassigned'
                if acc:
                    code_prefix = f"[{acc.code}] " if acc.code else ""
                    acc_name = f"{code_prefix}{acc.name}"

                exp_category = "Vendor Bills & Operational Expenses"
                if exp_category not in report_data['operating_outflows']:
                    report_data['operating_outflows'][exp_category] = {col: 0.0 for col in columns}

                targets = [f"Total{' (Prev)' if is_comparison else ''}"]
                if acc_name:
                    targets.append(f"{acc_name}{' (Prev)' if is_comparison else ''}")

                for t in targets:
                    if t in report_data['operating_outflows'][exp_category]:
                        report_data['operating_outflows'][exp_category][t] += amt
                    if t in report_data['total_outflows']:
                        report_data['total_outflows'][t] += amt

        # Run for current period
        process_dataset(domain_move_out, domain_move_in, domain_payment, is_comparison=False)

        # Run for comparison period if requested
        if has_comparison:
            process_dataset(comp_domain_move_out, comp_domain_move_in, comp_domain_payment, is_comparison=True)

            for acc in selected_accounts:
                curr_col = acc['name']
                prev_col = f"{acc['name']} (Prev)"
                pct_col = f"{acc['name']} (%)"

                report_data['total_inflows'][pct_col] = calculate_percent(
                    report_data['total_inflows'][curr_col], report_data['total_inflows'][prev_col]
                )
                report_data['total_outflows'][pct_col] = calculate_percent(
                    report_data['total_outflows'][curr_col], report_data['total_outflows'][prev_col]
                )

                for item in report_data['operating_inflows']:
                    report_data['operating_inflows'][item][pct_col] = calculate_percent(
                        report_data['operating_inflows'][item][curr_col],
                        report_data['operating_inflows'][item][prev_col]
                    )

                for item in report_data['operating_outflows']:
                    report_data['operating_outflows'][item][pct_col] = calculate_percent(
                        report_data['operating_outflows'][item][curr_col],
                        report_data['operating_outflows'][item][prev_col]
                    )

        # Compute Net Cash Flow = Total Inflows - Total Outflows
        for col in columns:
            if '(%)' not in col:
                report_data['net_cashflow'][col] = (
                    report_data['total_inflows'].get(col, 0.0) - report_data['total_outflows'].get(col, 0.0)
                )

        if has_comparison:
            for acc in selected_accounts:
                curr_col = acc['name']
                prev_col = f"{acc['name']} (Prev)"
                pct_col = f"{acc['name']} (%)"
                report_data['net_cashflow'][pct_col] = calculate_percent(
                    report_data['net_cashflow'][curr_col], report_data['net_cashflow'][prev_col]
                )

        formatted_inflows = []
        for name, cols in report_data['operating_inflows'].items():
            formatted_inflows.append({'name': name, 'values': cols})

        formatted_outflows = []
        for name, cols in report_data['operating_outflows'].items():
            formatted_outflows.append({'name': name, 'values': cols})

        return {
            'columns': columns,
            'has_comparison': has_comparison,
            'operating_inflows': formatted_inflows,
            'total_inflows': report_data['total_inflows'],
            'operating_outflows': formatted_outflows,
            'total_outflows': report_data['total_outflows'],
            'net_cashflow': report_data['net_cashflow'],
        }

