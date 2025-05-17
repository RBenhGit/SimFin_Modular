# modules/routes/home.py
import os
import json
import pandas as pd
import plotly.utils
import simfin as sf
import logging

from flask import render_template, request, url_for, redirect, flash, session
from . import home_bp

from modules.data_loader import ensure_simfin_configured
from modules.financial_statements import download_financial_statements, save_financial_statements
from modules.price_history import download_price_history_with_mavg
from modules.chart_creator import create_candlestick_chart_with_mavg
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

STATEMENTS_TO_MANAGE_IN_SESSION = ['income']
VARIANTS_TO_MANAGE = ['annual', 'quarterly']
MOVING_AVERAGES_CONFIG = [20, 50, 100, 150, 200]

@home_bp.route('/')
def route_home():
    current_ticker = session.get('current_ticker')
    chart_json = None
    price_error = None
    logger.info(f"Home route accessed. Current ticker in session: '{current_ticker}'")

    if current_ticker:
        try:
            df_prices = download_price_history_with_mavg(
                current_ticker, period="10y", interval="1d", moving_averages=MOVING_AVERAGES_CONFIG
            )
            if df_prices is not None and not df_prices.empty:
                ma_cols_to_plot = [f'MA{ma}' for ma in MOVING_AVERAGES_CONFIG if f'MA{ma}' in df_prices.columns]
                chart_data = create_candlestick_chart_with_mavg(df_prices, current_ticker, ma_cols_to_plot)
                if chart_data and "error" not in chart_data:
                    chart_json = json.dumps(chart_data, cls=plotly.utils.PlotlyJSONEncoder)
                elif chart_data and "error" in chart_data:
                    price_error = chart_data["error"]
                    logger.warning(f"Error creating candlestick chart for {current_ticker}: {price_error}")
            else:
                price_error = f"לא נמצאו נתוני מחירים עבור {current_ticker} או שגיאה בהורדה."
                logger.warning(f"No price data for {current_ticker} or download_price_history_with_mavg returned None/empty.")
        except Exception as e:
            logger.error(f"Error in home route processing for ticker {current_ticker}: {e}", exc_info=True)
            price_error = f"שגיאה כללית בעיבוד נתוני מחיר עבור {current_ticker}."

    return render_template('base_layout.html',
                           page_title='ניתוח מניות - דף הבית',
                           content_template='content_home.html',
                           current_ticker=current_ticker,
                           candlestick_chart_json=chart_json,
                           price_data_error=price_error)

@home_bp.route('/set_ticker', methods=['POST'])
def route_set_ticker():
    ticker = request.form.get('ticker_input', '').upper().strip()
    logger.info(f"set_ticker called for ticker input: '{ticker}'")

    if not ticker:
        flash("לא הוזן טיקר.", "warning")
        return redirect(url_for('home.route_home'))

    session['current_ticker'] = ticker
    logger.info(f"Ticker '{ticker}' set in session.")
    flash(f"מעבד נתונים עבור {ticker}...", "info")

    try:
        config_loader = ConfigLoader()
        api_key_cfg, data_dir_cfg = ensure_simfin_configured(config_loader_instance=config_loader)

        if not data_dir_cfg:
            flash(f"שגיאה קריטית: תיקיית הנתונים של SimFin אינה מוגדרת כראוי. לא ניתן להוריד דוחות כספיים.", "danger")
            logger.error(f"SimFin data directory not configured for ticker {ticker} in set_ticker. Aborting.")
            return redirect(url_for('home.route_home'))

        download_results = download_financial_statements(ticker_symbol=ticker)

        for stmt_key_clear in STATEMENTS_TO_MANAGE_IN_SESSION:
            for variant_clear in VARIANTS_TO_MANAGE:
                session.pop(f'{stmt_key_clear}_{variant_clear}_df_json', None)
        session.pop('data_download_status', None)
        logger.info(f"Cleared previous statement data and download status from session for ticker {ticker}.")

        save_status = save_financial_statements(download_results, ticker)
        session['data_download_status'] = save_status

        any_data_processed_successfully = False
        for stmt_key_session in STATEMENTS_TO_MANAGE_IN_SESSION:
            for variant_session in VARIANTS_TO_MANAGE:
                result_key = f"{stmt_key_session}_{variant_session}"
                data_item = download_results.get(result_key)
                if isinstance(data_item, pd.DataFrame) and not data_item.empty:
                    session[f'{result_key}_df_json'] = data_item.to_json(orient='split', date_format='iso')
                    any_data_processed_successfully = True
        
        if any_data_processed_successfully or any("Saved" in str(status_msg) for status_msg in save_status.values()):
            flash(f"הנתונים עבור {ticker} עובדו בהצלחה.", "success")
        else:
            first_error = next((str(msg) for msg in save_status.values() if "Error" in str(msg) or "Failed" in str(msg) or "NoDataFound" in str(msg)),
                               next((str(val.get('Details', 'Unknown download error')) for val in download_results.values() if isinstance(val, dict) and "Error" in val), None))
            if first_error:
                 flash(f"עיבוד נתונים עבור {ticker} נכשל. שגיאה עיקרית: {first_error}", "danger")
                 logger.error(f"Data processing failed for {ticker}. Main error: {first_error}")
            else:
                flash(f"עיבוד נתונים עבור {ticker} נכשל או שלא נמצאו נתונים (אין הודעת שגיאה ספציפית).", "danger")
                logger.warning(f"Data processing failed for {ticker} with no specific error message.")
    except Exception as e:
        flash(f"שגיאה כללית בעת עיבוד הנתונים עבור {ticker}: {str(e)}", "danger")
        logger.error(f"Generic error processing data for ticker {ticker}: {e}", exc_info=True)

    return redirect(url_for('home.route_home'))

@home_bp.route('/update_api_key_action', methods=['POST'])
def route_update_api_key_action():
    new_api_key_input = request.form.get('api_key_input_modal', '').strip()
    config_loader = ConfigLoader()
    api_key_file_path = config_loader.get_absolute_path('API', 'api_key_file', 'config/simfin_api_key.txt')
    logger.info(f"Attempting to update API key. New key input: '{'(empty)' if not new_api_key_input else '(provided)'}'. File path: {api_key_file_path}")

    try:
        if not api_key_file_path:
            flash("שגיאת תצורה: נתיב קובץ מפתח API אינו מוגדר.", "danger")
            logger.error("API key file path is not configured in ConfigLoader for update action.")
            return redirect(request.referrer or url_for('home.route_home'))

        key_file_dir = os.path.dirname(api_key_file_path)
        if key_file_dir and not os.path.exists(key_file_dir):
            os.makedirs(key_file_dir, exist_ok=True)
            logger.info(f"Created directory for API key file: {key_file_dir}")

        target_api_key_to_set = 'free'
        flash_message = ""
        flash_category = "info"

        if new_api_key_input:
            with open(api_key_file_path, 'w') as f:
                f.write(new_api_key_input)
            target_api_key_to_set = new_api_key_input
            flash_message = 'מפתח API עודכן בהצלחה!'
            flash_category = 'success'
            logger.info(f"API key updated successfully to file '{api_key_file_path}'.")
        else:
            if os.path.exists(api_key_file_path):
                try:
                    os.remove(api_key_file_path)
                    flash_message = 'מפתח API נמחק. האפליקציה תשתמש כעת בנתוני "free".'
                    logger.info(f"API key file '{api_key_file_path}' removed.")
                except OSError as e:
                    logger.warning(f"Could not remove API key file '{api_key_file_path}': {e}")
                    flash_message = 'שגיאה במחיקת קובץ מפתח API קיים, אך האפליקציה תשתמש בנתוני "free".'
                    flash_category = 'warning'
            else:
                flash_message = 'לא היה מפתח API מותאם אישית, האפליקציה ממשיכה להשתמש בנתוני "free".'
            logger.info("SimFin API key set to 'free' after clearing/no input.")
        
        ensure_simfin_configured(api_key_val=target_api_key_to_set, config_loader_instance=config_loader)
        flash(flash_message, flash_category)

    except IOError as e:
        flash(f"שגיאת קלט/פלט בעדכון מפתח API: {e}. אנא בדוק הרשאות קבצים.", 'danger')
        logger.error(f"IOError updating API key to file '{api_key_file_path}': {e}", exc_info=True)
    except Exception as e:
        flash(f"שגיאה כללית בעדכון מפתח API: {e}.", 'danger')
        logger.error(f"Generic error updating API key: {e}", exc_info=True)

    return redirect(request.referrer or url_for('home.route_home'))