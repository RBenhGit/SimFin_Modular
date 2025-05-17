# modules/chart_creator.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging # הוסף לוגינג

logger = logging.getLogger(__name__) # הוסף לוגר

# הפונקציה create_timeseries_chart נשארת כפי שהייתה

def create_timeseries_chart(df, y_column, title, x_column_name_in_df=None, y_axis_title=None, chart_type='bar'):
    if df is None or df.empty:
        return {"error": f"No data available to create chart: {title} (DataFrame is None or empty)."}

    x_data = None
    x_label = None
    df_for_plotting = df.copy()

    if x_column_name_in_df is None:
        x_data = df_for_plotting.index
        x_label = df_for_plotting.index.name if df_for_plotting.index.name else 'Date'
        if not isinstance(df_for_plotting.index, pd.DatetimeIndex):
            try:
                df_for_plotting.index = pd.to_datetime(df_for_plotting.index, errors='coerce')
                df_for_plotting = df_for_plotting[df_for_plotting.index.notna()]
                if not df_for_plotting.empty:
                    df_for_plotting = df_for_plotting.sort_index()
                    x_data = df_for_plotting.index
                else: # Fallback if all dates were invalid
                    x_data = df.index.astype(str) # Keep original index as string
                    df_for_plotting = df.copy()
            except Exception as e:
                logger.warning(f"Could not convert index to DatetimeIndex for chart '{title}': {e}. Using string representation.")
                x_data = df.index.astype(str)
                df_for_plotting = df.copy()
        elif not (df_for_plotting.index.is_monotonic_increasing or df_for_plotting.index.is_monotonic_decreasing):
             df_for_plotting = df_for_plotting.sort_index()
             x_data = df_for_plotting.index
    else:
        if x_column_name_in_df not in df_for_plotting.columns:
            return {"error": f"X-axis column '{x_column_name_in_df}' not found for chart '{title}'."}
        x_data = df_for_plotting[x_column_name_in_df]
        x_label = x_column_name_in_df
        # If x_column is datetime, sort by it
        if pd.api.types.is_datetime64_any_dtype(df_for_plotting[x_column_name_in_df]):
             df_for_plotting = df_for_plotting.sort_values(by=x_column_name_in_df)
             x_data = df_for_plotting[x_column_name_in_df] # Update x_data after sorting

    if y_column not in df_for_plotting.columns:
        return {"error": f"Column '{y_column}' not found for chart '{title}'. Available: {df_for_plotting.columns.tolist()}"}

    try:
        df_for_plotting[y_column] = pd.to_numeric(df_for_plotting[y_column], errors='coerce')
        # Use the potentially re-indexed/sorted df_for_plotting for cleaning and getting final x_data
        df_cleaned = df_for_plotting.dropna(subset=[y_column])
        if df_cleaned.empty:
            return {"error": f"No valid numeric data to display for '{y_column}' in chart '{title}' after cleaning."}
    except Exception as e:
        return {"error": f"Error processing numeric data for chart '{title}': {str(e)}"}

    if x_column_name_in_df is None:
        final_x_data = df_cleaned.index
    else:
        final_x_data = df_cleaned[x_column_name_in_df]

    try:
        plot_labels = {
            y_column: y_axis_title if y_axis_title else y_column,
            x_label: x_label
        }
        common_layout_args = {
            "yaxis_title": y_axis_title if y_axis_title else y_column,
            "xaxis_title": x_label,
            "yaxis_tickformat": ',.0f', # Format y-axis ticks as numbers with commas, no decimals
            "height": 450,
            "margin": dict(l=50, r=20, t=60, b=50) # Adjusted margins
        }

        if chart_type == 'bar':
            fig = px.bar(df_cleaned, x=final_x_data, y=y_column, title=title, labels=plot_labels)
        elif chart_type == 'line':
            fig = px.line(df_cleaned, x=final_x_data, y=y_column, title=title, labels=plot_labels, markers=True)
        else:
            return {"error": f"Unsupported chart type: {chart_type}"}

        fig.update_layout(**common_layout_args)
        if pd.api.types.is_datetime64_any_dtype(final_x_data):
             fig.update_xaxes(tickformat='%Y-%m-%d', type='category') # Treat dates as categories for more control if needed

        chart_json_output = {"data": fig.data, "layout": fig.layout}
        return chart_json_output
    except Exception as e:
        logger.error(f"Chart '{title}': Error creating Plotly figure object: {e}", exc_info=True)
        return {"error": f"Error generating chart '{title}'. Details: {str(e)}"}


def create_candlestick_chart_with_mavg(df_prices, ticker_symbol, moving_averages_to_plot=None):
    if df_prices is None or df_prices.empty:
        logger.warning(f"No price data available for candlestick chart for {ticker_symbol}.")
        return {"error": "No price data available for candlestick chart."}
    
    try:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df_prices.index,
            open=df_prices['Open'],
            high=df_prices['High'],
            low=df_prices['Low'],
            close=df_prices['Close'],
            name=f'{ticker_symbol} OHLC',
            increasing_line_color='#2ECC71', 
            increasing_fillcolor='rgba(46, 204, 113, 0.5)',
            decreasing_line_color='#E74C3C', 
            decreasing_fillcolor='rgba(231, 76, 60, 0.5)'
        ))
        
        ma_colors = ['#3498DB', '#F1C40F', '#9B59B6', '#E67E22', '#1ABC9C'] # Blue, Yellow, Purple, Orange, Turquoise

        if moving_averages_to_plot:
            for i, ma_col in enumerate(moving_averages_to_plot):
                if ma_col in df_prices.columns:
                    fig.add_trace(go.Scatter(
                        x=df_prices.index,
                        y=df_prices[ma_col],
                        mode='lines',
                        name=ma_col,
                        line=dict(width=1.5, color=ma_colors[i % len(ma_colors)])
                    ))
        
        fig.update_layout(
            title=f'גרף נרות יומי וממוצעים נעים - {ticker_symbol}',
            title_x=0.5, # Center the title
            xaxis_title='תאריך',
            yaxis_title='מחיר', # Consider adding currency, e.g., 'מחיר ($)'
            dragmode='pan',  # <--- *** Set default drag mode to Pan ***
            xaxis_rangeslider_visible=True, # <--- *** Show rangeslider for better navigation ***
            height=650, # Increased height
            template="plotly_white", # A clean template
            plot_bgcolor='white', # White plot background
            paper_bgcolor='white', # White paper background
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            font=dict(
                family="Arial, sans-serif",
                size=12,
                color="#333333"
            ),
            margin=dict(l=60, r=60, t=80, b=60) # Adjusted margins for better spacing
        )
        
        fig.update_xaxes(
            showgrid=True, gridwidth=1, gridcolor='LightGrey',
            showline=True, linewidth=1, linecolor='black', mirror=True,
            # Consider tickformat for dates if needed, e.g., tickformat="%b '%y" for "Jan '23"
        )
        fig.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor='LightGrey',
            showline=True, linewidth=1, linecolor='black', mirror=True,
            fixedrange=False,  # Explicitly set fixedrange to false for y-axis
            # tickprefix="$" # Uncomment if prices are in USD
        )
        
        logger.info(f"Candlestick chart created for {ticker_symbol}")
        return {"data": fig.data, "layout": fig.layout}
    except Exception as e:
        logger.error(f"Error creating candlestick chart for {ticker_symbol}: {e}", exc_info=True)
        return {"error": f"Error generating candlestick chart: {str(e)}"}