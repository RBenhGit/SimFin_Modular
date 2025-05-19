# modules/routes/home.py
import os
import json
import pandas as pd
import plotly.utils
import simfin as sf
import logging

from flask import render_template, request, url_for, redirect, flash, session, current_app, jsonify
from . import home_bp

from modules.data_loader import ensure_simfin_configured, get_company_info, get_company_name_yf
from modules.financial_statements import download_financial_statements, save_financial_statements
from modules.price_history import download_price_history_with_mavg
from modules.chart_creator import create_candlestick_chart_with_mavg
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

STATEMENTS_TO_MANAGE_IN_SESSION = ['income']
VARIANTS_TO_MANAGE = ['annual', 'quarterly']
MOVING_AVERAGES_CONFIG = [20, 50, 100, 150, 200]
# Define a prefix for price data cache keys in session
PRICE_DATA_CACHE_PREFIX = 'price_data_cache_'

@home_bp.route('/')
def route_home():
    current_ticker = session.get('current_ticker')
    chart_json = None
    price_error = None
    logger.info(f"Home route accessed. Current ticker in session: '{current_ticker}'")
    logger.info(f"Session company info - name: '{session.get('company_name')}', sector: '{session.get('company_sector')}'")

    if current_ticker:
        try:
            download_period = current_app.config.get('PRICE_DATA_DOWNLOAD_PERIOD', '2y')
            display_years = current_app.config.get('PRICE_DATA_DISPLAY_YEARS', 1)
            
            # Cache key for default daily view
            # For route_home, interval is always '1d' effectively for the initial download_period
            cache_key = f"{PRICE_DATA_CACHE_PREFIX}{current_ticker}_{download_period}_1d"
            df_prices_full_json = session.get(cache_key)
            df_prices_full = None

            if df_prices_full_json:
                try:
                    df_prices_full = pd.read_json(df_prices_full_json, orient='split')
                    # Ensure index is DatetimeIndex
                    df_prices_full.index = pd.to_datetime(df_prices_full.index, errors='coerce')
                    df_prices_full = df_prices_full[df_prices_full.index.notna()]
                    if not df_prices_full.empty:
                         logger.info(f"Loaded initial daily price data for {current_ticker} from session cache (key: {cache_key}).")
                    else: # Cache was empty or failed to parse
                        df_prices_full = None # Ensure it's None to trigger download
                        logger.info(f"Cache for {cache_key} was empty/invalid, will re-download.")
                except Exception as e:
                    logger.warning(f"Error deserializing cached price data for {cache_key}: {e}. Will re-download.")
                    df_prices_full = None # Ensure download if cache is corrupt

            if df_prices_full is None:
                logger.info(f"No valid cache for {cache_key}, downloading initial daily price data for {current_ticker} with period {download_period}.")
                df_prices_full = download_price_history_with_mavg(
                    current_ticker,
                    period=download_period,
                    interval="1d", # Default interval for home page
                    moving_averages=MOVING_AVERAGES_CONFIG
                )
                if df_prices_full is not None and not df_prices_full.empty:
                    session[cache_key] = df_prices_full.to_json(orient='split', date_format='iso')
                    logger.info(f"Stored initial daily price data for {current_ticker} in session cache (key: {cache_key}).")
                elif df_prices_full is None: # download_price_history_with_mavg can return None
                     logger.warning(f"download_price_history_with_mavg returned None for {current_ticker}, period {download_period}, interval 1d.")
                # If df_prices_full is empty, it will be handled by the logic below.

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
            else: # This handles if df_prices_full is None or empty after attempt to load/download
                price_error = f"לא נמצאו נתוני מחירים עבור {current_ticker} או שגיאה בהורדה."
                logger.warning(f"No price data for {current_ticker} to display on home page (either cache empty/invalid or download failed/empty).")
        except Exception as e:
            logger.error(f"Error in home route processing for ticker {current_ticker}: {e}", exc_info=True)
            price_error = f"שגיאה כללית בעיבוד נתוני מחיר עבור {current_ticker}."

    return render_template('base_layout.html',
                           page_title=f'ניתוח מניות - דף הבית' + (f' - {session.get("company_name")} ({current_ticker})' if current_ticker and session.get('company_name') else f' - {current_ticker}' if current_ticker else ''),
                           content_template='content_home.html',
                           current_ticker=current_ticker,
                           candlestick_chart_json=chart_json,
                           price_data_error=price_error)

@home_bp.route('/set_ticker', methods=['POST'])
def route_set_ticker():
    ticker = request.form.get('ticker_input', '').upper().strip()
    logger.info(f"set_ticker called for ticker input: '{ticker}'")

    if not ticker:
        logger.warning("לא הוזן טיקר בעת קריאה ל-set_ticker.")
        return redirect(url_for('home.route_home'))

    # Clear previous ticker's price data from session
    if session.get('current_ticker') and session.get('current_ticker') != ticker:
        keys_to_delete = [key for key in session.keys() if key.startswith(f"{PRICE_DATA_CACHE_PREFIX}{session.get('current_ticker')}_")]
        for key in keys_to_delete:
            session.pop(key, None)
            logger.info(f"Cleared old price cache from session: {key}")

    session['current_ticker'] = ticker
    logger.info(f"Ticker '{ticker}' set in session.")
    logger.info(f"מעבד נתונים עבור {ticker}...")

    try:
        config_loader = ConfigLoader()
        api_key_cfg, data_dir_cfg = ensure_simfin_configured(config_loader_instance=config_loader)

        if not data_dir_cfg:
            logger.error(f"שגיאה קריטית: תיקיית הנתונים של SimFin אינה מוגדרת כראוי עבור טיקר {ticker} ב-set_ticker. לא ניתן להוריד דוחות כספיים.")
            return redirect(url_for('home.route_home'))

        # Get company info
        company_info = get_company_info(ticker)
        logger.info(f"Company info result for {ticker}: {company_info}")
        
        if isinstance(company_info, dict) and 'name' in company_info and company_info['name']:
            session['company_name'] = company_info['name']
            session['company_sector'] = company_info.get('sector')
            session['company_industry'] = company_info.get('industry')
            logger.info(f"Company info loaded for {ticker}: {company_info['name']}")
            logger.info(f"Session after setting company info - name: '{session.get('company_name')}', sector: '{session.get('company_sector')}'")
        else:
            # נסה להביא את שם החברה מ-yfinance
            yf_name = get_company_name_yf(ticker)
            if yf_name:
                session['company_name'] = yf_name
                session['company_sector'] = None
                session['company_industry'] = None
                logger.info(f"Company name loaded from yfinance for {ticker}: {yf_name}")
            else:
                session.pop('company_name', None)
                session.pop('company_sector', None)
                session.pop('company_industry', None)
                logger.warning(f"Could not load company info for {ticker}: {company_info.get('Details', 'Unknown error')}")

        # Clear previous financial statement data and download status
        for stmt_key_clear in STATEMENTS_TO_MANAGE_IN_SESSION:
            for variant_clear in VARIANTS_TO_MANAGE:
                session.pop(f'{stmt_key_clear}_{variant_clear}_df_json', None)
        session.pop('data_download_status', None)
        logger.info(f"Cleared previous financial statement data and download status from session for ticker {ticker}.")

        # Download and save financial statements
        download_results = download_financial_statements(ticker_symbol=ticker)
        save_status = save_financial_statements(download_results, ticker)
        session['data_download_status'] = save_status

        # Store financial statements in session
        any_data_processed_successfully = False
        for stmt_key_session in STATEMENTS_TO_MANAGE_IN_SESSION:
            for variant_session in VARIANTS_TO_MANAGE:
                result_key = f"{stmt_key_session}_{variant_session}"
                data_item = download_results.get(result_key)
                if isinstance(data_item, pd.DataFrame) and not data_item.empty:
                    session[f'{result_key}_df_json'] = data_item.to_json(orient='split', date_format='iso')
                    any_data_processed_successfully = True
        
        if any_data_processed_successfully or any("Saved" in str(status_msg) for status_msg in save_status.values()):
            logger.info(f"הנתונים הפיננסיים עבור {ticker} עובדו ונשמרו בהצלחה.")
        else:
            first_error = next((str(msg) for msg in save_status.values() if "Error" in str(msg) or "Failed" in str(msg) or "NoDataFound" in str(msg)),
                               next((str(val.get('Details', 'Unknown download error')) for val in download_results.values() if isinstance(val, dict) and "Error" in val), None))
            if first_error:
                logger.error(f"עיבוד הנתונים הפיננסיים עבור {ticker} נכשל. שגיאה עיקרית: {first_error}")
            else:
                logger.warning(f"עיבוד הנתונים הפיננסיים עבור {ticker} נכשל או שלא נמצאו נתונים (אין הודעת שגיאה ספציפית). Mozambiqueב-save_status: {save_status}, download_results: {download_results}")
    except Exception as e:
        logger.error(f"שגיאה כללית בעת עיבוד הנתונים עבור {ticker}: {e}", exc_info=True)

    return redirect(url_for('home.route_home'))

@home_bp.route('/update_api_key_action', methods=['POST'])
def route_update_api_key_action():
    new_api_key_input = request.form.get('api_key_input_modal', '').strip()
    config_loader = ConfigLoader()
    api_key_file_path = config_loader.get_absolute_path('API', 'api_key_file', 'config/simfin_api_key.txt')
    logger.info(f"Attempting to update API key. New key input: '{'(empty)' if not new_api_key_input else '(provided)'}'. File path: {api_key_file_path}")

    try:
        if not api_key_file_path:
            logger.error("API key file path is not configured in ConfigLoader for update action (update_api_key_action).")
            return redirect(request.referrer or url_for('home.route_home'))

        key_file_dir = os.path.dirname(api_key_file_path)
        if key_file_dir and not os.path.exists(key_file_dir):
            os.makedirs(key_file_dir, exist_ok=True)
            logger.info(f"Created directory for API key file: {key_file_dir}")

        target_api_key_to_set = 'free'

        if new_api_key_input:
            with open(api_key_file_path, 'w') as f:
                f.write(new_api_key_input)
            target_api_key_to_set = new_api_key_input
            logger.info(f"API key updated successfully to file '{api_key_file_path}'.")
        else:
            if os.path.exists(api_key_file_path):
                try:
                    os.remove(api_key_file_path)
                    logger.info(f"API key file '{api_key_file_path}' removed. Application will use 'free' data.")
                except OSError as e:
                    logger.warning(f"Could not remove API key file '{api_key_file_path}': {e}")
                    logger.warning(f"Error removing existing API key file, but application will use 'free' data.")
            else:
                logger.info("No custom API key was set. Application continues to use 'free' data.")
        
        ensure_simfin_configured(api_key_val=target_api_key_to_set, config_loader_instance=config_loader)

    except IOError as e:
        logger.error(f"IOError updating API key to file '{api_key_file_path}': {e}", exc_info=True)
    except Exception as e:
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
        
        app_config = current_app.config
        # Determine download_period based on interval from config
        if interval == '1mo':
            download_period = app_config.get('PRICE_DATA_DOWNLOAD_PERIOD_MONTHLY', '10y') 
        elif interval == '1wk':
            download_period = app_config.get('PRICE_DATA_DOWNLOAD_PERIOD_WEEKLY', '5y')
        else: # Daily ('1d')
            download_period = app_config.get('PRICE_DATA_DOWNLOAD_PERIOD_DAILY', '2y') # Matches route_home initial
        
        # Construct the cache key using ticker, determined download_period, and interval
        cache_key = f"{PRICE_DATA_CACHE_PREFIX}{ticker}_{download_period}_{interval}"
        df_prices_json = session.get(cache_key)
        df_prices = None

        if df_prices_json:
            try:
                df_prices = pd.read_json(df_prices_json, orient='split')
                # Ensure index is DatetimeIndex
                df_prices.index = pd.to_datetime(df_prices.index, errors='coerce')
                df_prices = df_prices[df_prices.index.notna()]
                if not df_prices.empty:
                    logger.info(f"Loaded price data for {ticker}, period {download_period}, interval {interval} from session cache (key: {cache_key}).")
                else: # Cache was empty/invalid
                    df_prices = None
                    logger.info(f"Cache for {cache_key} was empty/invalid, will re-download.")
            except Exception as e:
                logger.warning(f"Error deserializing cached price data for {cache_key}: {e}. Will re-download.")
                df_prices = None # Ensure download if cache is corrupt
        
        if df_prices is None:
            logger.info(f"No valid cache for {cache_key}, downloading price data for {ticker}, period {download_period}, interval {interval}.")
            df_prices = download_price_history_with_mavg(
                ticker,
                period=download_period, 
                interval=interval,
                moving_averages=MOVING_AVERAGES_CONFIG
            )
            if df_prices is not None and not df_prices.empty:
                session[cache_key] = df_prices.to_json(orient='split', date_format='iso')
                logger.info(f"Stored price data for {ticker}, period {download_period}, interval {interval} in session cache (key: {cache_key}).")
            elif df_prices is None:
                 logger.warning(f"download_price_history_with_mavg returned None for {ticker}, period {download_period}, interval {interval}.")
            # If df_prices is empty, it will be handled by the logic below.

        if df_prices is None or df_prices.empty:
            logger.warning(f"No price data after attempting to fetch/load from cache for {ticker} with interval {interval}")
            return jsonify({"error": f"לא נמצאו נתוני מחירים עבור {ticker} באינטרוול {interval}."})

        df_prices_display = df_prices # Use all data from the specific period/interval download

        ma_cols_to_plot = [f'MA{ma}' for ma in MOVING_AVERAGES_CONFIG if f'MA{ma}' in df_prices_display.columns]
        chart_data = create_candlestick_chart_with_mavg(df_prices_display, ticker, ma_cols_to_plot)

        if chart_data and "error" not in chart_data:
            logger.debug(f"Returning chart data for {ticker}, interval {interval}: {str(chart_data)[:200]}...")
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
        ticker_val = request.get_json().get('ticker', '?') if request.is_json else '?'
        interval_val = request.get_json().get('interval', '?') if request.is_json else '?'
        logger.error(f"Error in /update_chart_interval for ticker {ticker_val}, interval {interval_val}: {e}", exc_info=True)
        logger.debug(f"Returning exception payload: {{'error': 'שגיאת שרת בעידכון הגרף: {str(e)}'}}")
        return jsonify({"error": f"שגיאת שרת בעידכון הגרף: {str(e)}"}), 500