"""Valuation route handlers for SimFin Analyzer."""

from flask import render_template, redirect, url_for, session, flash
from . import valuations_bp

from modules.data_loader import get_api_key_status_for_display


@valuations_bp.route('/')
def route_valuations():
    """Valuations page route handler."""
    current_ticker = session.get('current_ticker', None)
    api_key_status = get_api_key_status_for_display()
    
    if not current_ticker:
        flash("אנא בחר טיקר תחילה.", "warning")
        return redirect(url_for('home.route_home'))
    
    return render_template('base_layout.html', 
                           page_title='הערכות שווי',
                           current_ticker=current_ticker,
                           content_template='content_valuations.html',
                           api_key_status_display=api_key_status)
