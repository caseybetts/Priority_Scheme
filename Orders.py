# Author: Casey Betts, 2024
# This file contains the Orders class which holds the dataframe of order, weather and schedule information

import pandas as pd 

from numpy import random
from os import listdir

class Orders:
    """ Contains the functions required to import and set up a dataframe ready for use in the priority optimization class """

    def __init__(self, parameters) -> None:

        # File locations
        self.active_orders_location = parameters["orders_csv"]
        self.cloud_cover_folder = parameters["clouds_folder"]

        # Random number generator
        self.rng = random.default_rng()

        # Dataframe related variables
        self.cloud_file_names = [x for x in listdir(self.cloud_cover_folder)]
        self.zero_dollar_customer_values = {int(k): v for k,v in parameters["zero_dollar_cust_dpsqkm"].items()}
        self.MCP_priority_to_dollar_map = {int(k): v for k,v in parameters["MCP_dollar_values"].items()}
        self.test_coefficients = parameters["test coefficients"]
        self.predicted_cc_uncertainty = parameters["predicted cloud cover uncertainty"] * 2                     # Standard Deviation of the normal distribution  
        self.cloud_cover_buckets = {}
        self.weather_scenarios = parameters["number of weather scenarios"]
        self.weather_type = parameters["weather_type"]
        self.scheduled_column_index = 0

        # Score Curve Variables
        self.coefficient = .47
        self.powers = 10
        self.range = 100

        # Run initial functions
        self.load_data()
        self.prepare_dataframe()
        
    def load_data(self):
        """ Load the csv files into pandas dataframes """

        # Load orders .csv files into a pandas dataframe
        self.active_orders = pd.read_csv(self.active_orders_location)

        # Create variable to contain the latitudes that have orders in them
        self.active_latitudes = set(self.active_orders.Latitude)

        # Store the min and max of the active latitudes
        self.min_latitude = min(self.active_latitudes)
        self.max_latitude = max(self.active_latitudes)

    def prepare_dataframe(self):
        """ Create and populate all columns required prior to starting the optimization process """

        self.add_columns()
        self.populate_actual_cc()
        self.populate_predicted_cc()
        self.populate_dollar_values()

        # Create dictionary template for mapping dollar values to priorities 
        self.dollar_to_pri_map = dict.fromkeys(set(self.active_orders.DollarPerSquare), 0) 

    def add_columns(self):
        """ Add/remove the necessary columns and fill with a placeholder value"""

        # Remove unnecessary column
        self.active_orders.drop(labels=["Unnamed: 0"], axis=1, inplace=True)

        # Add needed columns
        self.active_orders["New_Priority"] = 0
        self.active_orders["Score"] = 0
        self.active_orders["Total_Score"] = 0
        self.active_orders["Scheduled"] = False 

        # Save the index of new columns
        self.scheduled_column_index = self.active_orders.columns.get_loc("Scheduled")
            
    def find_cloud_cover(self, lat, lon):
        """ Given a latitude and longitude this will return the nearest cloud cover value from the PWOT .csv """

        if self.weather_type == "clear":
            return 0
        elif self.weather_type == "cloudy":
            return 90
        elif self.weather_type == "random":
            return self.rng.random()*90
        elif self.weather_type == "PWOT":

            # round the lat and lon to the nearest .25
            lat = round(lat * 4) / 4
            lon = round(lon * 4) / 4

            try:
                # return the single cloud cover value associated with the given lat and lon 
                return self.cloud_cover[(self.cloud_cover.Latitude == lat) & (self.cloud_cover.Longitude == lon)].Value.iloc[0]
            except:
                print("Lat: ", lat, "Lon: ", lon)
    
    def populate_actual_cc(self):
        """ Choose an actual cloud cover score for each order """
        
        # Create acutal cloud value columns
        for column_number in range(self.weather_scenarios):

            # Load the current PWOT .csv into the cloud cover dataframe
            self.cloud_cover = pd.read_csv('PWOT_CSV\\'+ self.cloud_file_names[column_number])

            # Create a column with the current number in the name and populate with the appropriate cloud cover value for each order based on the cloud cover dataframe
            self.active_orders["Actual_" + str(column_number)] = self.active_orders.apply( lambda x: self.find_cloud_cover(x.Latitude, x.Longitude)/100, axis=1)

    def populate_predicted_cc(self):
        """ Populate the predicted cc column with an estimated amount of cloud cover based on the actual cc """

        # Create list of column names
        for column_number in range(self.weather_scenarios):

            if self.weather_type == "clear":
                self.active_orders["Predicted_" + str(column_number)] = self.active_orders.apply( lambda x: 0, axis=1)
            else:
                # predicted cc is a random variation (+/- uncertanty) of the actual cc
                self.active_orders["Predicted_" + str(column_number)] = self.active_orders.apply( lambda x: x["Actual_" + str(column_number)] + (self.rng.standard_normal() * self.predicted_cc_uncertainty), axis=1 )

                # predicted cc must be between 0 and 1
                self.active_orders["Predicted_" + str(column_number)].clip(lower=0, upper=1, inplace=True) 

    def populate_MCP_dollar_value(self, x):
        """ Returns a random dollar value normally distributed with a mean of the dollar value associated with the given MCP priority """

        if x in self.MCP_priority_to_dollar_map.keys():

            return self.MCP_priority_to_dollar_map[x]
        
    def populate_dollar_values(self):
        """ Populate DollarPerSquare column with dollar values based on existing dollar value or customer """

        # Use .loc to locate all orders with a customer in the zero dollar dictionary
        # Then set the dollar value equal to the corresponding value in the dictionary using the pandas mapping function based on the customer number
        self.active_orders.loc[self.active_orders.Cust_Num.isin(self.zero_dollar_customer_values.keys()), 'DollarPerSquare'] = self.active_orders.Cust_Num.map(self.zero_dollar_customer_values)

        # There is a very large number of cust 306 orders so changing these based on priority will provide a much better model
        # For cust 306 change the dollar value based on priority using the MCP dollar mapping
        self.active_orders.loc[self.active_orders.Cust_Num == 306, 'DollarPerSquare'] = self.active_orders.Task_Pri.map(lambda x: self.populate_MCP_dollar_value(x)) 

        # Once dollar values are set save the maximum dollar value in a variable
        self.max_dollar_value = self.active_orders.loc[self.active_orders['DollarPerSquare'].idxmax()]['DollarPerSquare']

    def populate_priority(self, func):
        """ Add a priority to each order based on the dollar value """
        
        # Set the priority value based on the current dollar to priority funciton
        self.active_orders.New_Priority = self.active_orders.apply(lambda x: func(x.DollarPerSquare), axis=1)

    def priority_to_score(self, priority):
        """ Given a priority will return a score based on the FOM curve"""

        # mathematical conversion from the priority to the score
        # Priority range should be 0-100
        # return exp(self.coefficient*(self.powers-(5*(priority+700))/self.range))

        # Reverse the priority values so that the lower pri values map to higher score values
        return 100 - priority

    def populate_score(self):
        """ populate a score to each order based on the priority of the order """

        # Set the score
        self.active_orders.Score = self.active_orders.apply( lambda x: self.priority_to_score(x.New_Priority), axis=1)

    def populate_total_score(self, weather_column):
        """ Populate a column for total score which is the score multiplied by the predicted cloud cover """

        # Set the total score
        self.active_orders.Total_Score = self.active_orders.apply( lambda x: (1 - x["Predicted_" + str(weather_column)]) * x.Score, axis=1)
    
    def schedule_orders(self):
        """ Return the list of orders that have the maximum score within their respective 2 degree lat """

        latitude = self.min_latitude

        while latitude < self.max_latitude + 1:
            
            # Create the list of orders within the current latitude band
            order_list = self.active_orders[(self.active_orders.Latitude > latitude) & (self.active_orders.Latitude < latitude + 1)]
            
            if not order_list.empty:
                # Find the index of the row with the max Total_Score
                max_index = order_list.Total_Score.idxmax()
                # Change the Scheduled value of this column to True
                self.active_orders.iloc[max_index, self.scheduled_column_index ] = True

            latitude += 2                                                                                         
    
    def total_dollars(self, weather_column):
        """ Returns the sum of the dollars per square value of the schedule orders where actual CC value less than the max cc """

        # Get a sum of the dollars per square of the slice of orders that are scheduled and within cloud spec
        total_dollars = self.active_orders.DollarPerSquare[  (self.active_orders.Scheduled == True) & 
                                                    (self.active_orders.MAX_CC > self.active_orders["Actual_" + str(weather_column)])].sum()

        return total_dollars

