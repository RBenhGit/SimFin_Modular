# modules/routes/valuations.py
import logging
from flask import render_template, session # Removed redirect, url_for, flash
from . import valuations_bp

# from modules.data_loader import ensure_simfin_configured # Only if needed
from utils.decorators import ticker_required
# from utils.config_loader import ConfigLoader # Only if ensure_simfin_configured is called

logger = logging.getLogger(__name__)

@valuations_bp.route('/')
@ticker_required
def route_valuations(current_ticker):
    logger.info(f"Route /valuations for ticker: '{current_ticker}'")
    # If valuations will require fresh SimFin data:
    # try:
    #     config_loader = ConfigLoader()
    #     ensure_simfin_configured(config_loader_instance=config_loader)
    # except Exception as e:
    #     logger.error(f"Error ensuring SimFin configured in route_valuations: {e}", exc_info=True)
    #     flash("שגיאה בהכנת נתוני הערכות שווי.", "danger")
    #     return redirect(url_for('home.route_home'))

    return render_template('base_layout.html',
                           page_title=f'הערכות שווי - {current_ticker}',
                           content_template='content_valuations.html',
                           current_ticker=current_ticker)