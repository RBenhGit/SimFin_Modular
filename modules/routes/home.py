# modules/routes/home.py
import os
import json
import pandas as pd
import plotly.utils
import simfin as sf
import logging

from flask import render_template, request, url_for, redirect, flash, session, current_app, jsonify
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
            # קרא את ההגדרות מ-app.config
            download_period = current_app.config.get('PRICE_DATA_DOWNLOAD_PERIOD', '2y') # Default to '2y' if not set
            display_years = current_app.config.get('PRICE_DATA_DISPLAY_YEARS', 1)    # Default to 1 year if not set

            # הורד נתונים לפי התקופה שהוגדרה
            df_prices_full = download_price_history_with_mavg(
                current_ticker,
                period=download_period, # Use configured download period
                interval="1d",
                moving_averages=MOVING_AVERAGES_CONFIG
            )

            if df_prices_full is not None and not df_prices_full.empty:
                # הצג רק את התקופה שהוגדרה כברירת מחדל
                # ודא שהאינדקס הוא datetime
                if not isinstance(df_prices_full.index, pd.DatetimeIndex):
                    # נסה להמיר אם זה לא אינדקס תאריכים, או טפל בשגיאה אם ההמרה נכשלת
                    # בהנחה ש-download_price_history_with_mavg אמור להחזיר אינדקס תאריכים
                    logger.warning(f"Price data for {current_ticker} does not have a DatetimeIndex. Chart may be incorrect.")
                    df_prices_display = df_prices_full # השתמש בכל הנתונים אם האינדקס לא תקין לסינון
                else:
                    # הנחה שהאינדקס כבר מודע ל-timezone או שהוא naive ויש להתייחס אליו בהתאם
                    # אם האינדקס הוא timezone-naive, pd.Timestamp.now() יהיה timezone-naive.
                    # אם האינדקס הוא timezone-aware, pd.Timestamp.now(tz=df_prices_full.index.tz) עדיף.
                    now_timestamp = pd.Timestamp.now()
                    if df_prices_full.index.tz is not None:
                        now_timestamp = now_timestamp.tz_localize(df_prices_full.index.tz) # אם now הוא naive והאינדקס aware
                    elif now_timestamp.tz is not None and df_prices_full.index.tz is None:
                        # זה מקרה פחות סביר אם yfinance מחזיר naive
                        now_timestamp = now_timestamp.tz_convert(None) 
                        
                    start_display_date = now_timestamp - pd.DateOffset(years=display_years) # Use configured display years
                    df_prices_display = df_prices_full[df_prices_full.index >= start_display_date]
                    if df_prices_display.empty:
                        logger.warning(f"No data found for {current_ticker} in the last {display_years} year(s), displaying all downloaded {download_period} data.")
                        df_prices_display = df_prices_full # חזור לכל הנתונים אם הסינון הותיר DataFrame ריק
                
                ma_cols_to_plot = [f'MA{ma}' for ma in MOVING_AVERAGES_CONFIG if f'MA{ma}' in df_prices_display.columns]
                chart_data = create_candlestick_chart_with_mavg(df_prices_display, current_ticker, ma_cols_to_plot)
                
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

@home_bp.route('/update_chart_interval', methods=['POST'])
def route_update_chart_interval():
    try:
        data = request.get_json()
        ticker = data.get('ticker')
        interval = data.get('interval') # e.g., "1d", "1wk", "1mo"

        if not ticker or not interval:
            return jsonify({"error": "Ticker or interval missing."}), 400

        logger.info(f"Updating chart interval for {ticker} to {interval}")

        # --- DEBUGGING CONFIG ACCESS ---
        app_config = current_app.config # Store config in a local variable
        logger.debug(f"Type of app_config: {type(app_config)}")
        # logger.debug(f"Contents of app_config: {app_config}") # Can be very verbose
        try:
            config_items_repr = list(app_config.items()) # Get items for logging
            logger.debug(f"All items in app_config: {config_items_repr}")
        except Exception as e_items:
            logger.debug(f"Could not get items from app_config: {e_items}")

        # Attempt to use .get() again, now that type seems correct
        daily_period_key = 'PRICE_DATA_DOWNLOAD_PERIOD_DAILY'
        weekly_period_key = 'PRICE_DATA_DOWNLOAD_PERIOD_WEEKLY'
        monthly_period_key = 'PRICE_DATA_DOWNLOAD_PERIOD_MONTHLY'

        logger.debug(f"Accessing with .get('{daily_period_key}'): {app_config.get(daily_period_key, 'DEFAULT_DAILY_NOT_FOUND')}")
        logger.debug(f"Accessing with .get('{weekly_period_key}'): {app_config.get(weekly_period_key, 'DEFAULT_WEEKLY_NOT_FOUND')}")
        logger.debug(f"Accessing with .get('{monthly_period_key}'): {app_config.get(monthly_period_key, 'DEFAULT_MONTHLY_NOT_FOUND')}")
        # --- END DEBUGGING CONFIG ACCESS ---

        if interval == '1mo':
            download_period = app_config.get(monthly_period_key, '10y') 
        elif interval == '1wk':
            download_period = app_config.get(weekly_period_key, '5y')
        else: # Daily
            download_period = app_config.get(daily_period_key, '2y')
        
        if "NOT_FOUND" in download_period: # Check if we hit a default from the debug .get because key was missing
            logger.error(f"CRITICAL: Config key for interval {interval} was not found! Defaulted to {download_period}")
            # Potentially raise an error or handle this state if critical

        df_prices = download_price_history_with_mavg(
            ticker,
            period=download_period, 
            interval=interval,
            moving_averages=MOVING_AVERAGES_CONFIG 
            # Note: MOVING_AVERAGES_CONFIG might need adjustment for weekly/monthly charts (e.g., 20-week MA instead of 20-day MA)
            # For now, we keep them as is, meaning they will be calculated based on the new interval's periods.
        )

        if df_prices is None or df_prices.empty:
            logger.warning(f"No price data after attempting to fetch for {ticker} with interval {interval}")
            return jsonify({"error": f"לא נמצאו נתוני מחירים עבור {ticker} באינטרוול {interval}."})

        # For weekly/monthly, we might not need to filter to the last N years if the period itself is long.
        # The `download_period` effectively becomes the display period for resampled data.
        # If PRICE_DATA_DISPLAY_YEARS was to be used, it needs context of the interval.
        # For now, we display all data fetched for the given interval.
        df_prices_display = df_prices 

        ma_cols_to_plot = [f'MA{ma}' for ma in MOVING_AVERAGES_CONFIG if f'MA{ma}' in df_prices_display.columns]
        chart_data = create_candlestick_chart_with_mavg(df_prices_display, ticker, ma_cols_to_plot)

        if chart_data and "error" not in chart_data:
            logger.debug(f"Returning chart data for {ticker}, interval {interval}: {str(chart_data)[:200]}...") # Log snippet of data
            # Serialize Plotly objects correctly before jsonify
            chart_data_json_str = json.dumps(chart_data, cls=plotly.utils.PlotlyJSONEncoder)
            chart_data_for_jsonify = json.loads(chart_data_json_str)
            return jsonify(chart_data_for_jsonify)
        elif chart_data and "error" in chart_data:
            error_payload = chart_data.get('error', 'שגיאה לא ידועה ביצירת הגרף')
            logger.warning(f"Error creating candlestick chart for {ticker} with interval {interval}: {error_payload}")
            logger.debug(f"Returning error payload: {{'error': '{error_payload}'}}")
            return jsonify({"error": error_payload})
        else:
            logger.warning(f"Unknown error or no data from create_candlestick_chart_with_mavg for {ticker}, interval {interval}")
            logger.debug("Returning generic error payload: {'error': 'שגיאה לא ידועה או נתונים חסרים לאחר יצירת הגרף.'}")
            return jsonify({"error": "שגיאה לא ידועה או נתונים חסרים לאחר יצירת הגרף."})
            
    except Exception as e:
        # Ensure data variable is defined for the logger even if request.get_json() fails
        ticker_val = request.get_json().get('ticker', '?') if request.is_json else '?'
        interval_val = request.get_json().get('interval', '?') if request.is_json else '?'
        logger.error(f"Error in /update_chart_interval for ticker {ticker_val}, interval {interval_val}: {e}", exc_info=True)
        logger.debug(f"Returning exception payload: {{'error': 'שגיאת שרת בעידכון הגרף: {str(e)}'}}")
        return jsonify({"error": f"שגיאת שרת בעידכון הגרף: {str(e)}"}), 500