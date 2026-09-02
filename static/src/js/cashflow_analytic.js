/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class CashFlowAnalyticReport extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            data: null,
            dateFrom: "",
            dateTo: "",
            datePreset: "this_year",
            comparison: "none",
            inflowsExpanded: true,
            outflowsExpanded: true,
            availableAccounts: [],
            selectedAccounts: [],
            months: [
                { id: 'month_0', name: 'January' }, { id: 'month_1', name: 'February' },
                { id: 'month_2', name: 'March' }, { id: 'month_3', name: 'April' },
                { id: 'month_4', name: 'May' }, { id: 'month_5', name: 'June' },
                { id: 'month_6', name: 'July' }, { id: 'month_7', name: 'August' },
                { id: 'month_8', name: 'September' }, { id: 'month_9', name: 'October' },
                { id: 'month_10', name: 'November' }, { id: 'month_11', name: 'December' }
            ],
            quarters: [
                { id: 'quarter_0', name: 'Q1' }, { id: 'quarter_1', name: 'Q2' },
                { id: 'quarter_2', name: 'Q3' }, { id: 'quarter_3', name: 'Q4' }
            ]
        });

        onWillStart(() => {
            this.loadAnalyticAccounts().then(() => {
                this.setPresetDates('this_year');
                this.loadData();
            });
        });
    }

    async loadAnalyticAccounts() {
        const accounts = await this.orm.call(
            "havano.cashflow.analytic.report",
            "get_available_analytic_accounts",
            []
        );
        this.state.availableAccounts = accounts;
        this.state.selectedAccounts = accounts.map(a => a.id);
    }

    setPresetDates(preset) {
        this.state.datePreset = preset;
        const now = new Date();
        const currentYear = now.getFullYear();

        if (preset === 'this_year') {
            this.state.dateFrom = `${currentYear}-01-01`;
            this.state.dateTo = `${currentYear}-12-31`;
        } else if (preset === 'last_year') {
            this.state.dateFrom = `${currentYear - 1}-01-01`;
            this.state.dateTo = `${currentYear - 1}-12-31`;
        } else if (preset === 'this_month') {
            const m = String(now.getMonth() + 1).padStart(2, '0');
            const lastDay = new Date(currentYear, now.getMonth() + 1, 0).getDate();
            this.state.dateFrom = `${currentYear}-${m}-01`;
            this.state.dateTo = `${currentYear}-${m}-${lastDay}`;
        } else if (preset === 'last_month') {
            const lastMonthDate = new Date(currentYear, now.getMonth() - 1, 1);
            const lmYear = lastMonthDate.getFullYear();
            const lm = String(lastMonthDate.getMonth() + 1).padStart(2, '0');
            const lastDay = new Date(lmYear, lastMonthDate.getMonth() + 1, 0).getDate();
            this.state.dateFrom = `${lmYear}-${lm}-01`;
            this.state.dateTo = `${lmYear}-${lm}-${lastDay}`;
        } else if (preset === 'this_quarter') {
            const q = Math.floor(now.getMonth() / 3);
            const startMonth = String(q * 3 + 1).padStart(2, '0');
            const endMonth = q * 3 + 3;
            const lastDay = new Date(currentYear, endMonth, 0).getDate();
            this.state.dateFrom = `${currentYear}-${startMonth}-01`;
            this.state.dateTo = `${currentYear}-${String(endMonth).padStart(2, '0')}-${lastDay}`;
        } else if (preset.startsWith('month_')) {
            const mIndex = parseInt(preset.split('_')[1]);
            const m = String(mIndex + 1).padStart(2, '0');
            const lastDay = new Date(currentYear, mIndex + 1, 0).getDate();
            this.state.dateFrom = `${currentYear}-${m}-01`;
            this.state.dateTo = `${currentYear}-${m}-${lastDay}`;
        } else if (preset.startsWith('quarter_')) {
            const qIndex = parseInt(preset.split('_')[1]);
            const startMonth = String(qIndex * 3 + 1).padStart(2, '0');
            const endMonth = qIndex * 3 + 3;
            const lastDay = new Date(currentYear, endMonth, 0).getDate();
            this.state.dateFrom = `${currentYear}-${startMonth}-01`;
            this.state.dateTo = `${currentYear}-${String(endMonth).padStart(2, '0')}-${lastDay}`;
        }
    }

    async loadData() {
        const data = await this.orm.call(
            "havano.cashflow.analytic.report",
            "get_report_data",
            [],
            {
                date_from: this.state.dateFrom || null,
                date_to: this.state.dateTo || null,
                analytic_account_ids: this.state.selectedAccounts.length > 0 ? this.state.selectedAccounts : null,
                comparison: this.state.comparison
            }
        );
        this.state.data = data;
    }

    applyPreset(preset) {
        this.setPresetDates(preset);
        this.loadData();
    }

    onFilterChange() {
        this.state.datePreset = 'custom';
        this.loadData();
    }

    setComparison(comp) {
        this.state.comparison = comp;
        this.loadData();
    }

    toggleAccount(accId) {
        const idx = this.state.selectedAccounts.indexOf(accId);
        if (idx > -1) {
            this.state.selectedAccounts.splice(idx, 1);
        } else {
            this.state.selectedAccounts.push(accId);
        }
        this.loadData();
    }

    toggleInflows() {
        this.state.inflowsExpanded = !this.state.inflowsExpanded;
    }

    toggleOutflows() {
        this.state.outflowsExpanded = !this.state.outflowsExpanded;
    }

    formatCurrency(amount) {
        if (amount === null || amount === undefined) return "0.00";
        return Number(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    formatPercent(val) {
        if (val === null || val === undefined) return "0.0%";
        return `${Number(val).toFixed(1)}%`;
    }
}

CashFlowAnalyticReport.template = "havano_cashflow_analytic.CashFlowAnalyticReport";
registry.category("actions").add("havano_cashflow_analytic_report", CashFlowAnalyticReport);
