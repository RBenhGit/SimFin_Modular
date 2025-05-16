"""Module for creating charts from financial data in SimFin Analyzer."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_timeseries_chart(df, y_column, title, x_column_name_in_df=None, y_axis_title=None, chart_type='bar'):
    """
    Create a time series chart from DataFrame data.
    
    Args:
        df (pd.DataFrame): DataFrame containing the data to plot
        y_column (str): Column name for the y-axis values
        title (str): Chart title
        x_column_name_in_df (str, optional): Column name for x-axis values. If None, uses index
        y_axis_title (str, optional): Label for y-axis. If None, uses y_column name
        chart_type (str, optional): Type of chart ('bar' or 'line'). Defaults to 'bar'
    
    Returns:
        dict: Chart data in format compatible with Plotly JSON or error message
    """
    if df is None or df.empty:
        return {"error": f"No data available to create chart: {title} (DataFrame is None or empty)."}

    x_data = None
    x_label = None
    df_for_plotting = df.copy()

    # Handle x-axis data - use either index or specified column
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
                else:
                    x_data = df.index.astype(str)
                    df_for_plotting = df.copy()
            except Exception as e: 
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
        if pd.api.types.is_datetime64_any_dtype(df_for_plotting[x_column_name_in_df]):
             df_for_plotting = df_for_plotting.sort_values(by=x_column_name_in_df)
             x_data = df_for_plotting[x_column_name_in_df] 

    # Verify y-axis column exists
    if y_column not in df_for_plotting.columns:
        return {"error": f"Column '{y_column}' not found for chart '{title}'. Available: {df_for_plotting.columns.tolist()}"}

    # Convert y-column data to numeric
    try:
        df_for_plotting[y_column] = pd.to_numeric(df_for_plotting[y_column], errors='coerce')
        df_cleaned = df_for_plotting.dropna(subset=[y_column]) 
        if df_cleaned.empty:
            return {"error": f"No valid numeric data to display for '{y_column}' in chart '{title}'."}
    except Exception as e:
        return {"error": f"Error processing numeric data for chart '{title}': {e}"}

    # Get final x-data for plotting
    if x_column_name_in_df is None:
        final_x_data = df_cleaned.index
    else:
        final_x_data = df_cleaned[x_column_name_in_df]

    # Create chart based on type
    try:
        if chart_type == 'bar':
            fig = px.bar(df_cleaned, x=final_x_data, y=y_column, title=title,
                           labels={y_column: y_axis_title if y_axis_title else y_column, 
                                   x_label: x_label})
        elif chart_type == 'line':
            fig = px.line(df_cleaned, x=final_x_data, y=y_column, title=title,
                            labels={y_column: y_axis_title if y_axis_title else y_column, 
                                    x_label: x_label}, 
                            markers=True)
        else: 
            return {"error": f"Unsupported chart type: {chart_type}"}

        # Update layout
        fig.update_layout(yaxis_title=y_axis_title if y_axis_title else y_column, 
                          xaxis_title=x_label,
                          yaxis_tickformat=',.0f', height=450, margin=dict(l=40, r=20, t=60, b=40))

        # Handle datetime x-axis
        if pd.api.types.is_datetime64_any_dtype(final_x_data):
             fig.update_xaxes(tickformat='%Y-%m-%d', type='category') 

        # Return chart data and layout (compatible with plotly JSON encoding)
        chart_json_output = {"data": fig.data, "layout": fig.layout}
        return chart_json_output

    except Exception as e:
        print(f"Chart '{title}': Error creating Plotly figure object: {e}")
        return {"error": f"Error generating chart '{title}'. Details: {e}"}


def create_candlestick_chart_with_mavg(df_prices, ticker_symbol, moving_averages_to_plot=None):
    """
    Create a candlestick chart with moving averages.
    
    Args:
        df_prices (pd.DataFrame): DataFrame with OHLC price data
        ticker_symbol (str): Stock ticker symbol
        moving_averages_to_plot (list, optional): List of moving average column names to plot
    
    Returns:
        dict: Chart data in format compatible with Plotly JSON or error message
    """
    if df_prices is None or df_prices.empty:
        return {"error": "No price data available for candlestick chart."}
    
    try:
        # Create candlestick chart
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df_prices.index, 
            open=df_prices['Open'], 
            high=df_prices['High'],
            low=df_prices['Low'], 
            close=df_prices['Close'], 
            name=f'{ticker_symbol}'
        ))
        
        # Add moving averages if provided
        if moving_averages_to_plot:
            for ma_col in moving_averages_to_plot:
                if ma_col in df_prices.columns: 
                    fig.add_trace(go.Scatter(
                        x=df_prices.index, 
                        y=df_prices[ma_col], 
                        mode='lines', 
                        name=ma_col, 
                        line=dict(width=1.5)
                    ))
        
        # Update layout
        fig.update_layout(
            title=f'גרף נרות יומי וממוצעים נעים - {ticker_symbol}', 
            xaxis_title='תאריך', 
            yaxis_title='מחיר',
            xaxis_rangeslider_visible=False, 
            height=600, 
            legend_title_text='מקרא'
        )
        
        return {"data": fig.data, "layout": fig.layout}
    except Exception as e:
        print(f"Error creating candlestick chart for {ticker_symbol}: {e}")
        return {"error": f"Error generating candlestick chart: {e}"}
