# utils/decorators.py
from functools import wraps
from flask import session, flash, redirect, url_for
import logging

logger = logging.getLogger(__name__)

def ticker_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_ticker_val = session.get('current_ticker')
        session_keys_info = list(session.keys()) if session else "No Active Session or session is empty"
        # The following debug log is useful during development if session issues persist.
        # For cleaner production logs, consider removing or changing its level.
        logger.debug(f"ticker_required decorator: Checking session. current_ticker: '{current_ticker_val}'. Session keys: {session_keys_info}")
        
        if not current_ticker_val:
            flash("אנא בחר טיקר תחילה.", "warning")
            logger.warning(f"ticker_required: No current_ticker in session. Redirecting to home. Session keys: {session_keys_info}")
            return redirect(url_for('home.route_home'))
        
        kwargs['current_ticker'] = current_ticker_val
        return f(*args, **kwargs)
    return decorated_function