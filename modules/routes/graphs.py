"""Graph route handlers for SimFin Analyzer."""

import json
import plotly.utils

from flask import render_template, redirect, url_for, session, flash
from . import graphs_bp

from modules.data_loader import get_api_key_status_for_display
from modules.financial_statements import get_dataframe_from_session_or_csv
from modules.chart_creator import create_timeseries_chart


@graphs_bp.route('/annual')
def route_graphs_annual():
    """Annual graphs route handler."""
    current_ticker = session.get('current_ticker')
    api_key_status = get_api_key_status_for_display()
    if not current_ticker: 
        flash("אנא בחר טיקר תחילה.", "warning")
        return redirect(url_for('home.route_home'))

    df_income, error_data, info_data = get_dataframe_from_session_or_csv(current_ticker, 'annual', 'income', session)
    graph_revenue_json, graph_net_income_json = None, None

    if df_income is not None and not df_income.empty:
        revenue_col = next((col for col in ['Revenue', 'Total Revenue', 'Sales'] if col in df_income.columns), None)
        net_income_col_options = ['Net Income (Common)', 'Net Income', 'Net Income Available to Common Shareholders']
        net_income_col = next((col for col in net_income_col_options if col in df_income.columns), None)

        if revenue_col:
            chart_rev = create_timeseries_chart(df_income, revenue_col, f'הכנסות ({revenue_col}) - שנתי', y_axis_title='סכום')
            if chart_rev and "error" not in chart_rev: 
                graph_revenue_json = json.dumps(chart_rev, cls=plotly.utils.PlotlyJSONEncoder)
            elif chart_rev and "error" in chart_rev : 
                error_data = (error_data + "; " if error_data else "") + f"Revenue chart error: {chart_rev['error']}"
        else:
            error_data = (error_data + "; " if error_data else "") + "Revenue column not found in annual income data."

        if net_income_col:
            chart_ni = create_timeseries_chart(df_income, net_income_col, f'רווח נקי ({net_income_col}) - שנתי', y_axis_title='סכום')
            if chart_ni and "error" not in chart_ni: 
                graph_net_income_json = json.dumps(chart_ni, cls=plotly.utils.PlotlyJSONEncoder)
            elif chart_ni and "error" in chart_ni:
                error_data = (error_data + "; " if error_data else "") + f"Net income chart error: {chart_ni['error']}"
        else:
            error_data = (error_data + "; " if error_data else "") + "Net income column not found in annual income data."

    elif df_income is None: 
        no_data_msg = "No annual income data available to generate graphs."
        error_data = (error_data + "; " if error_data else "") + no_data_msg

    return render_template('base_layout.html', 
                           page_title=f'גרפים שנתיים - {current_ticker}', 
                           current_ticker=current_ticker,
                           content_template='content_graphs.html', 
                           graph_type='Annual',
                           graph_revenue_json=graph_revenue_json, 
                           graph_net_income_json=graph_net_income_json,
                           data_error_message=error_data, 
                           data_info_message=info_data, 
                           api_key_status_display=api_key_status)


@graphs_bp.route('/quarterly')
def route_graphs_quarterly():
    """Quarterly graphs route handler."""
    current_ticker = session.get('current_ticker')
    api_key_status = get_api_key_status_for_display()
    if not current_ticker: 
        flash("אנא בחר טיקר תחילה.", "warning")
        return redirect(url_for('home.route_home'))

    df_income_q, error_data_q, info_data_q = get_dataframe_from_session_or_csv(current_ticker, 'quarterly', 'income', session)
    graph_revenue_json_q, graph_net_income_json_q = None, None

    if df_income_q is not None and not df_income_q.empty:
        revenue_col = next((col for col in ['Revenue', 'Total Revenue', 'Sales'] if col in df_income_q.columns), None)
        net_income_col_options = ['Net Income (Common)', 'Net Income', 'Net Income Available to Common Shareholders']
        net_income_col = next((col for col in net_income_col_options if col in df_income_q.columns), None)

        if revenue_col:
            chart_rev_q = create_timeseries_chart(df_income_q, revenue_col, f'הכנסות ({revenue_col}) - רבעוני', y_axis_title='סכום')
            if chart_rev_q and "error" not in chart_rev_q: 
                graph_revenue_json_q = json.dumps(chart_rev_q, cls=plotly.utils.PlotlyJSONEncoder)
            elif chart_rev_q and "error" in chart_rev_q :
                 error_data_q = (error_data_q + "; " if error_data_q else "") + f"Quarterly revenue chart error: {chart_rev_q['error']}"
        else:
            error_data_q = (error_data_q + "; " if error_data_q else "") + "Revenue column not found in quarterly income data."

        if net_income_col:
            chart_ni_q = create_timeseries_chart(df_income_q, net_income_col, f'רווח נקי ({net_income_col}) - רבעוני', y_axis_title='סכום')
            if chart_ni_q and "error" not in chart_ni_q: 
                graph_net_income_json_q = json.dumps(chart_ni_q, cls=plotly.utils.PlotlyJSONEncoder)
            elif chart_ni_q and "error" in chart_ni_q:
                error_data_q = (error_data_q + "; " if error_data_q else "") + f"Quarterly net income chart error: {chart_ni_q['error']}"
        else:
             error_data_q = (error_data_q + "; " if error_data_q else "") + "Net income column not found in quarterly income data."

    elif df_income_q is None:
        no_data_msg_q = "No quarterly income data available to generate graphs."
        error_data_q = (error_data_q + "; " if error_data_q else "") + no_data_msg_q

    return render_template('base_layout.html', 
                           page_title=f'גרפים רבעוניים - {current_ticker}', 
                           current_ticker=current_ticker,
                           content_template='content_graphs.html', 
                           graph_type='Quarterly',
                           graph_revenue_json=graph_revenue_json_q, 
                           graph_net_income_json=graph_net_income_json_q,
                           data_error_message=error_data_q, 
                           data_info_message=info_data_q, 
                           api_key_status_display=api_key_status)
