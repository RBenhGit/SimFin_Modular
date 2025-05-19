# modules/routes/graphs.py
import json
import plotly.utils
import logging
from flask import render_template, session
from . import graphs_bp

from modules.data_loader import ensure_simfin_configured
from modules.financial_statements import get_dataframe_from_session_or_csv
from modules.chart_creator import create_timeseries_chart
from utils.decorators import ticker_required
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

def _prepare_financial_charts(current_ticker, variant, session_obj):
    logger.info(f"_prepare_financial_charts for ticker: '{current_ticker}', variant: '{variant}'")
    try:
        config_loader = ConfigLoader()
        ensure_simfin_configured(config_loader_instance=config_loader)
    except Exception as e:
        logger.error(f"Error ensuring SimFin configured in _prepare_financial_charts: {e}", exc_info=True)

    df_income, error_data, info_data = get_dataframe_from_session_or_csv(
        current_ticker, variant, 'income', session_obj
    )
    graph_revenue_json, graph_net_income_json = None, None
    chart_title_variant = "שנתי" if variant == "annual" else "רבעוני"

    if df_income is not None and not df_income.empty:
        revenue_col_options = ['Revenue', 'Total Revenue', 'Sales']
        revenue_col = next((col for col in revenue_col_options if col in df_income.columns), None)

        net_income_col_options = ['Net Income Common', 'Net Income', 'Net Income Available to Common Shareholders', 'Net Income (Common)']
        net_income_col = next((col for col in net_income_col_options if col in df_income.columns), None)

        if revenue_col:
            chart_rev = create_timeseries_chart(
                df_income, revenue_col, f'הכנסות ({revenue_col}) - {chart_title_variant}', y_axis_title='סכום'
            )
            if chart_rev and "error" not in chart_rev:
                graph_revenue_json = json.dumps(chart_rev, cls=plotly.utils.PlotlyJSONEncoder)
            elif chart_rev and "error" in chart_rev:
                error_data = (error_data + "; " if error_data else "") + \
                             f"שגיאה בגרף הכנסות ({chart_title_variant}): {chart_rev['error']}"
        else:
            error_data = (error_data + "; " if error_data else "") + \
                         f"עמודת הכנסות לא נמצאה בנתוני ההכנסה ({chart_title_variant})."

        if net_income_col:
            chart_ni = create_timeseries_chart(
                df_income, net_income_col, f'רווח נקי ({net_income_col}) - {chart_title_variant}', y_axis_title='סכום'
            )
            if chart_ni and "error" not in chart_ni:
                graph_net_income_json = json.dumps(chart_ni, cls=plotly.utils.PlotlyJSONEncoder)
            elif chart_ni and "error" in chart_ni:
                error_data = (error_data + "; " if error_data else "") + \
                             f"שגיאה בגרף רווח נקי ({chart_title_variant}): {chart_ni['error']}"
        else:
            error_data = (error_data + "; " if error_data else "") + \
                         f"עמודת רווח נקי לא נמצאה בנתוני ההכנסה ({chart_title_variant})."

    elif df_income is None and not error_data: # df_income could be None if get_dataframe_from_session_or_csv returns it
        no_data_msg = f"אין נתוני הכנסה ({chart_title_variant}) זמינים ליצירת גרפים."
        error_data = (error_data + "; " if error_data else "") + no_data_msg
    
    if error_data:
        logger.warning(f"Errors preparing charts for {current_ticker} ({variant}): {error_data}")
    if info_data:
        logger.info(f"Info messages for {current_ticker} ({variant}): {info_data}")
        
    return graph_revenue_json, graph_net_income_json, error_data, info_data

@graphs_bp.route('/annual')
@ticker_required
def route_graphs_annual(current_ticker):
    logger.info(f"Route /graphs/annual for ticker: '{current_ticker}'. Session keys: {list(session.keys())}") # <--- תיקון כאן
    graph_revenue_json, graph_net_income_json, error_data, info_data = \
        _prepare_financial_charts(current_ticker, 'annual', session)

    return render_template('base_layout.html',
                           page_title=f'גרפים שנתיים' + (f' - {session.get("company_name")} ({current_ticker})' if current_ticker and session.get('company_name') else f' - {current_ticker}' if current_ticker else ''),
                           content_template='content_graphs.html',
                           graph_type='Annual',
                           current_ticker=current_ticker,
                           graph_revenue_json=graph_revenue_json,
                           graph_net_income_json=graph_net_income_json,
                           data_error_message=error_data,
                           data_info_message=info_data)

@graphs_bp.route('/quarterly')
@ticker_required
def route_graphs_quarterly(current_ticker):
    logger.info(f"Route /graphs/quarterly for ticker: '{current_ticker}'. Session keys: {list(session.keys())}") # <--- תיקון כאן
    graph_revenue_json, graph_net_income_json, error_data, info_data = \
        _prepare_financial_charts(current_ticker, 'quarterly', session)

    return render_template('base_layout.html',
                           page_title=f'גרפים רבעוניים' + (f' - {session.get("company_name")} ({current_ticker})' if current_ticker and session.get('company_name') else f' - {current_ticker}' if current_ticker else ''),
                           content_template='content_graphs.html',
                           graph_type='Quarterly',
                           current_ticker=current_ticker,
                           graph_revenue_json=graph_revenue_json,
                           graph_net_income_json=graph_net_income_json,
                           data_error_message=error_data,
                           data_info_message=info_data)