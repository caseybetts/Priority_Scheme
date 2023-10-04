# Author: Casey Betts, 2023
# This tool models earth-imaging satellite capabilities and uses gradient descent to optimize how the satellite will choose imaging targets. 
#The prioritization scheme is considered optimized when the revenu generated by the model is maximized. The model is supplied with a list of orders
#all having specific location data and dollar amounts associated to them.

import json
import matplotlib.pyplot as plt
import pandas as pd

from math import exp
from random import choice, random
from scipy.optimize import minimize
from sys import argv 
from time import time

# Applicable json file name with parameters
input_parameters_file_name = argv[1]

# Reads in the 
with open(input_parameters_file_name, 'r') as input:
    parameters = json.load(input)


class Priority_Optimizer:
    """ Contains the functions required to produce an optimal set of priorities for a given set of orders and cloud values """

    def __init__(self) -> None:

        # File locations
        self.active_orders_location = parameters["orders_csv"]
        self.cloud_cover_values_location = parameters["clouds_csv"]

        # Optimization related variables
        self.scale = 1e-5
        self.optimization_method = parameters["optimization method"]
        self.optimization_tolerance = parameters["optimization tolerance"]
        self.initial_priorities = [x * self.scale for x in parameters["initial priorities"] ]
        self.bounds =  [ (x * self.scale, y * self.scale) for x, y in parameters["priority bounds"] ]
        self.average_prioritizations = []
        self.final_optimal_priorities = []


        # Dataframe related variables
        self.zero_dollar_customer_values = parameters["zero_dollar_cust_dpsqkm"]
        self.dollar_breaks = parameters["dollar bin breakpoints"]
        self.weather_scenarios = parameters["number of weather scenarios"]
        self.test_priorities = [x * self.scale for x in parameters["test case priorities"] ]
        self.predicted_cc_uncertainty = parameters["predicted cloud cover uncertainty"] * 2
        self.cloud_cover_buckets = {}

        # Score Curve Variables
        self.coefficient = .47
        self.powers = 10
        self.range = 100

        # Run initial functions
        self.load_data()
        self.add_columns()
        self.create_cloud_cover_buckets()
        self.populate_actual_cc()
        self.populate_predicted_cc()
        self.populate_dollar_values()
        
    def load_data(self):
        """ Load the csv files into pandas dataframes """

        # Load orders and image strips .csv files into pandas dataframes
        self.active_orders = pd.read_csv(self.active_orders_location)
        self.cloud_cover_values = pd.read_csv(self.cloud_cover_values_location)

        # Create variable to contain the latitudes that have orders in them
        self.active_latitudes = set(self.active_orders.Latitude)

        # Store the min and max of the active latitudes
        self.min_latitude = min(self.active_latitudes)
        self.max_latitude = max(self.active_latitudes)

    def add_columns(self):
        """ Add/remove the necessary columns and fill with a placeholder value"""

        # Remove unnecessary column
        self.active_orders.drop(labels=["Unnamed: 0"], axis=1, inplace=True)

        # Add needed columns
        self.active_orders["New_Priority"] = 0
        self.active_orders["Score"] = 0
        self.active_orders["Total_Score"] = 0
        self.active_orders["Scheduled"] = False 
    
    def create_cloud_cover_buckets(self):
        """ Populates a dictionary where the keys are each active latitude and the values are lists of possible cloud cover values """

        for latitude in self.active_latitudes:
            self.cloud_cover_buckets[latitude] = list(self.cloud_cover_values[
                                                (self.cloud_cover_values.Latitude < latitude + 2) & 
                                                (self.cloud_cover_values.Latitude > latitude - 2)].CC)
    
    def populate_actual_cc(self):
        """ Choose an actual cloud cover score for each order """
        
        # Create list of column names
        for column_number in range(self.weather_scenarios):
            self.active_orders["Actual_" + str(column_number)] = self.active_orders.apply( lambda x: choice(self.cloud_cover_buckets[x.Latitude]), axis=1)

    def populate_predicted_cc(self):
        """ Populate the predicted cc column with an estimated amount of cloud cover based on the actual cc """

        # Create list of column names
        for column_number in range(self.weather_scenarios):

            # predicted cc is a random variation (+/- uncertanty) of the actual cc
            self.active_orders["Predicted_" + str(column_number)] = self.active_orders.apply( lambda x: x["Actual_" + str(column_number)] + (random() - .5) * self.predicted_cc_uncertainty, axis=1 )

            # predicted cc must be between 0 and 1
            self.active_orders["Predicted_" + str(column_number)].clip(lower=0, upper=1, inplace=True)

    def set_clear_orders(self):
        """ Randomly create and populate clear columns with True based on their predicted CC and CC tolerance"""

        for i in range(self.clear_columns):
            self.active_orders[i] = self.active_orders.apply(   lambda x: True
                                                                if x.Actual_CC > x.MAX_CC 
                                                                else False, axis=1)     
        
    def populate_dollar_values(self):
        """ Populate DollarPerSquare column with dollar values based on existing dollar value or customer """

        # Use .loc to locate all orders with a customer in the zero dollar dictionary
        # Then set the dollar value equal to the corresponding value in the dictionary using the pandas mapping function based on the customer number
        self.active_orders.loc[self.active_orders.Cust_Num.isin(self.zero_dollar_customer_values.keys()), 'DollarPerSquare'] = self.active_orders.Cust_Num.map(self.zero_dollar_customer_values)

    def populate_priority(self, priority_list):
        """ Add a priority to each order based on the dollar value (and potentially other factors)"""

        # create a set of all unique dollar values 
        all_dollar_values = set(self.active_orders.DollarPerSquare)

        # create a dictionary for mapping dollar values to priorities 
        dollar_to_pri_map = dict.fromkeys(all_dollar_values, 0) 

        # change the dict values to the correct (starting) priorities
        for value in dollar_to_pri_map:
            if value >  self.dollar_breaks[0]:  dollar_to_pri_map[value] = priority_list[0]
            if value <= self.dollar_breaks[0]:  dollar_to_pri_map[value] = priority_list[1]
            if value <  self.dollar_breaks[1]:  dollar_to_pri_map[value] = priority_list[2]
            if value <  self.dollar_breaks[2]:  dollar_to_pri_map[value] = priority_list[3]
            if value <  self.dollar_breaks[3]:  dollar_to_pri_map[value] = priority_list[4]
            if value <  self.dollar_breaks[4]:  dollar_to_pri_map[value] = priority_list[5]
            if value <  self.dollar_breaks[5]:  dollar_to_pri_map[value] = priority_list[6]
            if value <  self.dollar_breaks[6]:  dollar_to_pri_map[value] = priority_list[7]
            if value <  self.dollar_breaks[7]:  dollar_to_pri_map[value] = priority_list[8]
            if value <  self.dollar_breaks[8]:  dollar_to_pri_map[value] = priority_list[9]
            if value <  self.dollar_breaks[9]:  dollar_to_pri_map[value] = priority_list[10]
            if value == self.dollar_breaks[10]: dollar_to_pri_map[value] = priority_list[11]

        # Set the priority value equal to the corresponding value in the dictionary using the pandas mapping function based on the dollar value
        self.active_orders['New_Priority'] = self.active_orders.DollarPerSquare.map(dollar_to_pri_map)
        
        # Scale up from minimize function friendly to actual priority value
        self.active_orders['New_Priority'] = self.active_orders['New_Priority'] * self.scale

    def priority_to_score(self, priority):
        """ Given a priority will return a score based on the FOM curve"""

        # mathematical conversion from the priority to the score
        return exp(self.coefficient*(self.powers-(5*priority)/self.range))

    def populate_score(self):
        """ populate a score to each order based on the priority of the order """

        # Set the score
        self.active_orders.Score = self.active_orders.apply( lambda x: self.priority_to_score((x.New_Priority)-700), axis=1)

    def populate_total_score(self, weather_column):
        """ Populate a column for total score which is the score multiplied by the predicted cloud cover """

        # Set the total score
        self.active_orders.Total_Score = self.active_orders.apply( lambda x: (1 - x["Predicted_" + str(weather_column)]) * x.Score, axis=1)
    
    def schedule_orders(self):
        """ Return the list of orders that are have the maximum score within their respective 2 degree lat """

        latitude = self.min_latitude

        while latitude < self.max_latitude + 1:
            order_list = self.active_orders[(self.active_orders.Latitude == latitude) | (self.active_orders.Latitude == latitude + 1)]
            
            if not order_list.empty:
                max_index = order_list.Total_Score.idxmax()
                self.active_orders.iloc[max_index, 8 ] = True

            latitude += 2                                                                                         
    
    def total_dollars(self):
        """ Returns the sum of all the dollars per square with a 'Clear' value of True for a given column"""

        return self.active_orders.DollarPerSquare[self.active_orders.Scheduled == True].sum()

    def run_scenario(self, weather_column):
        """ This will reassign each order with a random weather prediction and then reschedule orders accordingly and return a total dollar amount """

        # Reset the schedule by setting all 'Scheduled' to False
        self.active_orders.Scheduled = False

        # Calculate the total score and which orders are scheduled
        self.populate_total_score(weather_column)
        self.schedule_orders()

        return self.total_dollars()

    def run_priority_scheme(self, priority_scheme, weather_column):
        """ Will run the set number of scenarios with a given prioritization scheme and return the average total dollar value """

        # Apply the given priority values to the orders
        self.populate_priority(priority_scheme)
        self.populate_score()

        return -self.run_scenario(weather_column)
    
    def optimal_priorities(self, weather_column):
        """ Uses the SciPy optimization tools to find the optimal prioritization scheme to maximize revenue for a given clear scenario """

        result = minimize(self.run_priority_scheme, 
                          self.initial_priorities, 
                          args=weather_column, 
                          bounds=self.bounds, 
                          tol=self.optimization_tolerance, 
                          method=self.optimization_method)

        if result.success:
            return result.x
        else:
            raise ValueError(result.message)
        
    def run_clear_scenarios(self):
        """ This will run the optimization function for each clear scenario for the current weather scenario """



        prioritizations = []

        for clear_column in range(self.clear_columns):
            prioritization = self.optimal_priorities(clear_column)
            prioritizations.append(prioritization)

        average_prioritization = [sum(x)/len(x) for x in zip(*prioritizations)]



        return average_prioritization

    def run_weather_scenarios(self):
        """ This will run the 'run clear scenarios' function for multiple weather scenarios and return an average prioritization from the results"""

        prioritizations = []

        for weather_column in range(self.weather_scenarios):

            # Timing 
            start_time = time()

            prioritization = self.optimal_priorities(weather_column)
            prioritizations.append(prioritization)

            print("Prioritization: ", prioritization)
            print("-----------------------------------------")

            # Timing 
            end_time = time()
            print("Time elapsed for a weather scenario: ", end_time - start_time)
            print("----------------------------------------------------------------")

        # Save the average of the prioritization sets found as the final result
        self.final_optimal_priorities = [sum(x)/len(x) for x in zip(*prioritizations)]

    def run_test_cases(self):
        """ Will run the priority_scheme function for each test case priority set """

        for scheme in test_cases:
            self.run_priority_scheme(scheme)

    def display_results(self):
        """ Will print the resulting optimal priority set as well as display a graph of the same """

        print("The final prioritization is: ", self.final_optimal_priorities)

        x_axis = [30] + self.dollar_breaks
        plt.plot(x_axis, self.final_optimal_priorities, 'o-r')
        plt.show()


if __name__ == "__main__":
    
    # Create calculator object
    priority_optimizer = Priority_Optimizer()
    priority_optimizer.active_orders.to_csv('output_from_pri_scheme.csv')
    priority_optimizer.run_weather_scenarios()
    priority_optimizer.display_results()






# Ideas
"""
- Make the curve easy to change
- Make the dollar value bins easy to change
- Vet the current output and investigate
- Make easy to submit a specific pri scheme
- Make easy to change the number of pri bins
+ Allow to accept a JSON file with all the necessary info
- Add in the cc tolerance to each order and factor into clear result
"""