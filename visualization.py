# visualization.py
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from matplotlib.dates import AutoDateLocator, DateFormatter
import numpy as np
from datetime import datetime

class ChartManager:
    #this class will handel everything that has to do with the charting
    def __init__(self, ax, canvas, fig, accent):
        self.ax = ax
        self.canvas = canvas
        self.fig = fig
        self.accent = accent
        self.show_forecast = False

    def toggle_trend_line(self):
        """handles the forecast visibility and update plot"""
        self.show_forecast = not self.show_forecast
        if hasattr(self, 'current_data'):
            self.update_plot(self.current_data)
    
    def calculate_forecast(self, dates, prices, years_to_forecast=6):
        """Calculate forecast using polyfit for years in advance"""
        # convert dates to  numbers for calc
        date_ordinals = pd.to_datetime(dates).map(lambda x: x.toordinal()).values
        y = prices.values
        
        # get coefficients of the line
        coefficients = np.polyfit(date_ordinals, y, 1)
        polynomial = np.poly1d(coefficients)
        
        # line for future dates
        last_date = pd.to_datetime(dates.iloc[-1])
        future_dates = pd.date_range(
            start=last_date,
            periods=years_to_forecast * 12 + 1,  # monthly
            freq='ME'
        )
        
        # line for  historical dates
        first_date = pd.to_datetime(dates.iloc[0])
        all_dates = pd.date_range(
            start=first_date,
            end=future_dates[-1],
            freq='ME'
        )
        
        #convert all dates into ordinals
        all_X = all_dates.map(lambda x: x.toordinal()).values
        
        # get forcast for range
        forecast_values = polynomial(all_X)
        
        return all_dates, forecast_values
    
    def setup_initial_plot(self):
        """define empty plot labels"""
        self.ax.set_title('Housing Prices Over Time')
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Price ($)')
        self.ax.text(0.5, 0.5, 'Select filters and click Update Viz', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.ax.transAxes)
        self.canvas.draw()
    
    def update_plot(self, data):
        """update the plot with new data"""
        if data is not None and not data.empty:
            self.current_data = data
            
            self.ax.clear()
            #convert prive to float
            data['price'] = data['price'].astype(float)
            #find whether we are displaying the city, zipcode or state
            location_cols = []
            if 'stateabbr' in data.columns:
                location_cols.append('stateabbr')
                if 'city' in data.columns:
                    location_cols.append('city')
                    if 'zipcode' in data.columns:
                        location_cols.append('zipcode')
            
            if 'city' in data.columns:
                main_title = f"Housing Prices in {data['city'].iloc[0]}, {data['stateabbr'].iloc[0]}"
                avg_desc = f"(Average across {data['included_zipcodes'].iloc[0]:.0f} zipcodes)"
            elif 'stateabbr' in data.columns:
                main_title = f"Housing Prices in {data['stateabbr'].iloc[0]}"
                avg_desc = f"(Average across {data['included_zipcodes'].iloc[0]:.0f} zipcodes)"
            else:
                main_title = "Housing Prices in United States"
                avg_desc = f"(Average across {data['included_zipcodes'].iloc[0]:.0f} zipcodes)"
            
            title = f"\n{main_title}"
            
            has_multiple_lines = False
            
            if location_cols:
                locations = data.groupby(location_cols)
                has_multiple_lines = len(locations) > 1
                
                for location_values, group in locations:
                    if isinstance(location_values, tuple):
                        label = ', '.join(str(v) for v in location_values)
                    else:
                        label = str(location_values)
                    
                    self.ax.plot(group['date'], group['price'], label=f"Actual - {label}")
                    
                    if self.show_forecast:
                        all_dates, forecast_values = self.calculate_forecast(
                            group['date'], group['price']
                        )
                        self.ax.plot(all_dates, forecast_values, '--', 
                                   label=f'Forecast - {label} (6 years)', alpha=0.7)
            else:
                self.ax.plot(data['date'], data['price'], 
                           color=self.accent, label="Actual Data")
                
                if self.show_forecast:
                    all_dates, forecast_values = self.calculate_forecast(
                        data['date'], data['price']
                    )
                    self.ax.plot(all_dates, forecast_values, '--', 
                               label='Forecast (6 years)', color='red', alpha=0.7)
            #set matplot labels x and y
            self.ax.set_title(title)
            self.ax.set_xlabel('Date')
            self.ax.set_ylabel('Average Home Value ($)')
            # set locations of date
            locator = AutoDateLocator()
            self.ax.xaxis.set_major_locator(locator)
            self.ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
            self.ax.tick_params(axis='x', rotation=45)
            #return curreny format
            def currency_formatter(x, p):
                return f'${x:,.0f}'
            self.ax.yaxis.set_major_formatter(currency_formatter)
            #grtid
            self.ax.grid(True, linestyle='--', alpha=0.7)
            
            #add forecast information if trend line showiung
            stats_text = f"\nAvg: ${data['price'].mean():,.0f}"
            stats_text += f" | Min: ${data['price'].min():,.0f}"
            stats_text += f" | Max: ${data['price'].max():,.0f}"
            if self.show_forecast:
                #last forecasted value
                stats_text += f"\nForecasted Value (6 years): ${forecast_values[-1]:,.0f}"
            
            current_title = self.ax.get_title()
            self.ax.set_title(current_title + stats_text)
            
            if has_multiple_lines or self.show_forecast:
                self.ax.legend(loc='lower right')
                self.fig.subplots_adjust(bottom=0.2)
            else:
                self.fig.tight_layout()
            
        else:
            #if no plot is active of no data found
            self.ax.clear()
            self.ax.text(0.5, 0.5, 'No data found for the given criteria\nTry different search parameters', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes)
        
        self.canvas.draw()#display the canvas

    def show_error(self, message):
        """show error message on plot"""
        self.ax.clear()
        self.ax.text(0.5, 0.5, message, 
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.ax.transAxes,
                    color='red',
                    fontsize=12,
                    wrap=True)
        self.canvas.draw()
        
    def clear_plot(self):
        """Reset"""
        self.ax.clear()
        self.setup_initial_plot()