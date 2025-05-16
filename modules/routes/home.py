"""Home route handlers for SimFin Analyzer."""

import os
import json
import pandas as pd
import plotly.utils
import simfin as sf

from flask import render_template, request, url_for, redirect, flash, session
from . import home_bp

from modules.data_loader import get_api_key_status_for_display
from modules.financial_statements import download_financial_statements, save_financial_statements
from modules.price_history import download_price_history_with_mavg
from modules.chart_creator import create_candlestick_chart_with_mavg


@home_bp.route('/')
def route_home():
    """Home page route handler."""
    current_ticker = session.get('current_ticker', '')
    api_key_status = get_api_key_status_for_display()
    chart_json = None
    price_error = None

    if current_ticker:
        moving_averages_config = [20, 50, 100, 150, 200]
        df_prices = download_price_history_with_mavg(current_ticker, period="10y", interval="1d", moving_averages=moving_averages_config)

        if df_prices is not None and not df_prices.empty:
            ma_cols_to_plot = [f'MA{ma}' for ma in moving_averages_config if f'MA{ma}' in df_prices.columns]
            chart_data = create_candlestick_chart_with_mavg(df_prices, current_ticker, ma_cols_to_plot)
            if chart_data and "error" not in chart_data:
                chart_json = json.dumps(chart_data, cls=plotly.utils.PlotlyJSONEncoder)
            elif chart_data and "error" in chart_data:
                price_error = chart_data["error"]
        else:
            price_error = f"לא נמצאו נתוני מחירים עבור {current_ticker} או שגיאה בהורדה."

    return render_template('base_layout.html', 
                           page_title='ניתוח מניות - דף הבית', 
                           current_ticker=current_ticker,
                           content_template='content_home.html',
                           candlestick_chart_json=chart_json, 
                           price_data_error=price_error,
                           api_key_status_display=api_key_status)


@home_bp.route('/set_ticker', methods=['POST'])
def route_set_ticker():
    """Handle setting the current ticker."""
    if request.method == 'POST':
        ticker = request.form.get('ticker_input', '').upper().strip() 
        if ticker: 
            session['current_ticker'] = ticker
            download_results = download_financial_statements(ticker_symbol=ticker)
            
            # Clear previous session data
            for stmt_key_for_session in ['income']: 
                for variant_for_session in ['annual', 'quarterly']:
                    session.pop(f'{stmt_key_for_session}_{variant_for_session}_df_json', None)
            
            # Save statements and update session
            status = save_financial_statements(download_results, ticker)
            session['data_download_status'] = status
            
            # Store income statements in session for quick access
            any_success = False
            for variant in ['annual', 'quarterly']:
                result_key = f"income_{variant}"
                data_item = download_results.get(result_key)
                if isinstance(data_item, pd.DataFrame) and not data_item.empty:
                    session[f'{result_key}_df_json'] = data_item.to_json(orient='split', date_format='iso')
                    any_success = True
            
            flash(f"Data for {ticker} processed." if any_success else f"Failed to process or no data found for {ticker}.", "success" if any_success else "danger")
            return redirect(url_for('home.route_home')) 
        else:
            flash("לא הוזן טיקר או שהטיקר מכיל רק רווחים.", "warning")
    return redirect(url_for('home.route_home'))


@home_bp.route('/update_api_key_action', methods=['POST'])
def route_update_api_key_action():
    """Handle updating the SimFin API key."""
    if request.method == 'POST':
        new_api_key = request.form.get('api_key_input_modal', '').strip()
        
        from utils.config_loader import ConfigLoader
        config = ConfigLoader()
        api_key_file = config.get('API', 'api_key_file')
        
        try:
            if new_api_key: 
                # Make sure the config directory exists
                os.makedirs(os.path.dirname(api_key_file), exist_ok=True)
                
                # Write the new key to file
                with open(api_key_file, 'w') as f:
                    f.write(new_api_key)
                sf.set_api_key(new_api_key) 
                session['api_key_status_display'] = get_api_key_status_for_display() 
                flash('מפתח API עודכן בהצלחה!', 'success')
            else: 
                # If no key provided, remove existing key or use free
                if os.path.exists(api_key_file):
                    try: 
                        os.remove(api_key_file)
                    except OSError as e: 
                        print(f"Could not remove API key file: {e}") 
                        flash('שגיאה במחיקת קובץ מפתח API קיים, אך האפליקציה תשתמש בנתוני "free".', 'warning')
                    else:
                         flash('מפתח API נמחק/נוקה. האפליקציה תשתמש כעת בנתוני "free".', 'info')
                else: 
                    flash('לא היה מפתח API מותאם אישית, האפליקציה ממשיכה להשתמש בנתוני "free".', 'info')

                sf.set_api_key('free') 
                session['api_key_status_display'] = get_api_key_status_for_display() 

        except Exception as e: 
            error_message_for_user = "שגיאה בעדכון מפתח API. אנא בדוק את הלוגים של השרת."
            flash(error_message_for_user, 'danger')
            print(f"Error updating API key: {e}") 
            session['api_key_status_display'] = "שגיאה בעדכון מפתח." 

        return redirect(request.referrer or url_for('home.route_home'))

    return redirect(url_for('home.route_home'))
