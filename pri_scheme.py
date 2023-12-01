# Author: Casey Betts, 2023
# This tool models earth-imaging satellite capabilities and uses gradient descent to optimize how the satellite will choose imaging targets. 
# The prioritization scheme is considered optimized when the revenu generated by the model is maximized. The model is supplied with a list of orders
# all having specific location data and dollar amounts associated to them.

import json
import matplotlib.pyplot as plt
import pandas as pd

from math import exp, cos
from numpy import random, count_nonzero
from os import listdir
from scipy.optimize import minimize
from sys import argv 
from time import time

# Applicable json file name with parameters
input_parameters_file_name = argv[1]

# Initialize the random number generator
rng = random.default_rng()

# Reads in the input parameters
with open(input_parameters_file_name, 'r') as input:
    parameters = json.load(input)


class Priority_Optimizer:
    """ Contains the functions required to produce an optimal set of priorities for a given set of orders and cloud values """

    def __init__(self) -> None:

        # File locations
        self.active_orders_location = parameters["orders_csv"]
        self.cloud_cover_folder = parameters["clouds_folder"]

        # Optimization related variables
        self.poly_degree = parameters["polynomial_degree"]
        self.scale = 1
        self.optimization_method = parameters["optimization method"]
        self.optimization_tolerance = parameters["optimization tolerance"]
        self.initial_coefficients = parameters["initial_coefficients"][-(self.poly_degree + 1):]
        self.bounds = parameters["priority bounds"][-(self.poly_degree + 1):]
        self.average_prioritizations = []
        self.final_optimal_coefficients = []
        self.pri_scheme_total_dollars = []
        self.coefficients = []
        self.run_coefficients = []
        self.iterated_coefficients = []

        # Dataframe related variables
        self.cloud_file_names = [x for x in listdir(self.cloud_cover_folder)]
        self.zero_dollar_customer_values = {int(k): v for k,v in parameters["zero_dollar_cust_dpsqkm"].items()}
        self.MCP_priority_to_dollar_map = {int(k): v for k,v in parameters["MCP_dollar_values"].items()}
        self.weather_scenarios = parameters["number of weather scenarios"]
        self.test_priorities = parameters["test case priorities"]
        self.predicted_cc_uncertainty = parameters["predicted cloud cover uncertainty"] * 2                     # Standard Deviation of the normal distribution  
        self.cloud_cover_buckets = {}
        self.weather_type = parameters["weather_type"]
        self.scheduled_column_index = 0

        # Score Curve Variables
        self.coefficient = .47
        self.powers = 10
        self.range = 100

        # Run initial functions
        self.load_data()
        self.prepare_dataframe()
        self.startup_readout()

        
    def load_data(self):
        """ Load the csv files into pandas dataframes """

        # Load orders and image strips .csv files into pandas dataframes
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

        # Update the schedule column index accordingly
        self.scheduled_column_index = self.active_orders.columns.get_loc("Scheduled")
            
    def find_cloud_cover(self, lat, lon):
        """ Given a latitude and longitude this will return the nearest cloud cover value from the PWOT .csv """

        if self.weather_type == "clear":
            return 0
        elif self.weather_type == "cloudy":
            return 90
        elif self.weather_type == "random":
            return rng.random()*90
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
                self.active_orders["Predicted_" + str(column_number)] = self.active_orders.apply( lambda x: x["Actual_" + str(column_number)] + (rng.standard_normal() * self.predicted_cc_uncertainty), axis=1 )

                # predicted cc must be between 0 and 1
                self.active_orders["Predicted_" + str(column_number)].clip(lower=0, upper=1, inplace=True) 

    def populate_MCP_dollar_value(self, x):
        """ Returns a random dollar value normally distributed with a mean of the dollar value associated with the given MCP priority """

        if x in self.MCP_priority_to_dollar_map.keys():

            return self.MCP_priority_to_dollar_map[x] + rng.standard_normal()*.1 + .6
        
    def populate_dollar_values(self):
        """ Populate DollarPerSquare column with dollar values based on existing dollar value or customer """

        # Use .loc to locate all orders with a customer in the zero dollar dictionary
        # Then set the dollar value equal to the corresponding value in the dictionary using the pandas mapping function based on the customer number
        self.active_orders.loc[self.active_orders.Cust_Num.isin(self.zero_dollar_customer_values.keys()), 'DollarPerSquare'] = self.active_orders.Cust_Num.map(self.zero_dollar_customer_values)

        # There is a very large number of cust 306 orders so changing these based on priority will provide a much better model
        # For cust 306 change the dollar value based on priority using the MCP dollar mapping
        self.active_orders.loc[self.active_orders.Cust_Num == 306, 'DollarPerSquare'] = self.active_orders.Task_Pri.map(lambda x: self.populate_MCP_dollar_value(x)) 

    def priority_function(self, coefficients, x):
        """ Defines the function for priority as a function of dollar value """

        # Return the value of a polynomial function based on the number of non-zero coefficients
        # if self.poly_degree == 1:
        #     d,e = coefficients
        #     return d*(x-10) + e
        # elif self.poly_degree == 2:
        #     c,d,e = coefficients
        #     return c*(x-10)**2 + d*(x-10) + e 
        # elif self.poly_degree == 3:
        #     b,c,d,e = coefficients
        #     return b*(x-10)**3 + c*(x-10)**2 + d*(x-10) + e
        # elif self.poly_degree == 4:
        #     a,b,c,d,e = coefficients
        #     return a*(x-10)**4 + b*(x-10)**3 + c*(x-10)**2 + d*(x-10) + e
        
        # Return the value of a trig function with 2 variables
        a,b,c,d = coefficients

        return a + b * (x-10) + c * (x-10)**2 + d * (x-10)**3

    def populate_priority(self, coefficients):
        """ Add a priority to each order based on the dollar value """
        
        # Set the priority value based on the current dollar to priority funciton
        self.active_orders.New_Priority = self.active_orders.apply(lambda x: self.priority_function(coefficients, x.DollarPerSquare), axis=1)

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
        """ Return the list of orders that have the maximum score within their respective 2 degree lat """

        latitude = self.min_latitude

        while latitude < self.max_latitude + 1:
            
            # Create the list of orders within the current latitude band
            order_list = self.active_orders[(self.active_orders.Latitude > latitude) & (self.active_orders.Latitude < latitude + 1)]
            
            if not order_list.empty:
                max_index = order_list.Total_Score.idxmax()
                self.active_orders.iloc[max_index, self.scheduled_column_index ] = True

            latitude += 2                                                                                         
    
    def total_dollars(self, weather_column):
        """ Returns the sum of all the dollars per square with actual CC value less than the max cc """

        total_dollars = self.active_orders.DollarPerSquare[  (self.active_orders.Scheduled == True) & 
                                                    (self.active_orders.MAX_CC > self.active_orders["Actual_" + str(weather_column)])].sum()
        
        self.pri_scheme_total_dollars.append(total_dollars)

        return total_dollars + rng.standard_normal()

    def run_scenario(self, weather_column):
        """ This will reassign each order with a random weather prediction and then reschedule orders accordingly and return a total dollar amount """

        # Reset the schedule by setting all 'Scheduled' to False
        self.active_orders.Scheduled = False

        # Calculate the total score and which orders are scheduled
        self.populate_total_score(weather_column)
        self.schedule_orders()

        return self.total_dollars(weather_column)

    def run_priority_scheme(self, coefficients, weather_column):
        """ Will run the set number of scenarios with a given prioritization scheme and return the average total dollar value """
                
        # Unscale priorities
        coefficients = [x / self.scale for x in coefficients ]

    
        # Apply the given priority values to the orders
        self.populate_priority(coefficients)
        self.populate_score()

        total = self.run_scenario(weather_column)
        self.run_coefficients.append(coefficients)

        print("Coefficients: ", coefficients, " yeilded : $", -total)
        
        return -total
    
    def optimal_priorities(self, weather_column):
        """ Uses the SciPy optimization tools to find the optimal prioritization scheme to maximize revenue for a given clear scenario """

        scaled_bounds = [ (x * self.scale, y * self.scale) for x, y in self.bounds ]        # Note: Can't be used with BFGS method (bounds=scaled_bounds,)
        scaled_initial_coefficients = [x * self.scale for x in self.initial_coefficients]

        result = minimize(self.run_priority_scheme, 
                          scaled_initial_coefficients, 
                          args=weather_column, 
                          bounds=scaled_bounds,
                          tol=self.optimization_tolerance, 
                          method=self.optimization_method,
                          options={"maxiter":150})
        
        self.iterated_coefficients.append(self.run_coefficients)
        self.run_coefficients = []

        if result.success:
            return result
        else:
            raise ValueError(result.message)

    def run_weather_scenarios(self):
        """ This will run the 'run clear scenarios' function for multiple weather scenarios and return an average prioritization from the results"""

        for weather_column in range(self.weather_scenarios):

            # Timing 
            start_time = time()

            # Reset the list of total dollar values
            self.pri_scheme_total_dollars = []

            optimization_result = self.optimal_priorities(weather_column)
            self.coefficients.append([x / self.scale for x in optimization_result.x])
            print(optimization_result)

            # Timing and readout
            end_time = time()
            print("\n----------------------------------------------------------------")
            print("Time elapsed for a weather scenario: ", end_time - start_time)
            print("Prioritization: ", self.coefficients[-1])
            print("Average $ value: $", sum(self.pri_scheme_total_dollars)/len(self.pri_scheme_total_dollars))
            print("Scenarios tried: ", len(self.pri_scheme_total_dollars))
            print("Final $ value: $", -optimization_result.fun)
            print("----------------------------------------------------------------")



        # Save the average of the prioritization sets found as the final result
        self.final_optimal_coefficients = [(sum(x)/len(x)) for x in zip(*self.coefficients)]

    def run_test_case(self):
        """ Will run the priority_scheme function for the test case priority set """

        total_dollars_for_each_weather_scenario = []

        for weather_column in range(self.weather_scenarios):
            # Produce a total dollar value for a given weather scenario (column) and append to a list
            total_dollars_for_each_weather_scenario.append(self.run_priority_scheme(self.test_priorities, weather_column))

        # Return the average total dollar value
        return sum(total_dollars_for_each_weather_scenario)/len(total_dollars_for_each_weather_scenario)

    def startup_readout(self):
        """ Prints out useful information prior to running the program """

        print("Running ", self.weather_scenarios," weather scenarios")
        print("Method: ", self.optimization_method)
        print("self.scheduled_column_index :", self.scheduled_column_index)
        print("Initial Coefficients: ", self.initial_coefficients)
        
        if count_nonzero(self.initial_coefficients) != self.poly_degree + 1:
            print("WARNING: You will have unused coefficients since your polynomial degree is ", self.poly_degree)

    def display_results(self):
        """ Will print the resulting optimal priority function as well as display a graph of the all the results and the average result """

        print("\n\nThe final prioritization is: ", self.final_optimal_coefficients)

        x_axis = range(30)
        i=0
        result_colors = ['cornflowerblue', 'tan', 'lightgreen']
        iter_colors = ['lavender', 'navajowhite', 'palegreen']

        for coefficients in self.coefficients:
            result_color = result_colors[i]
            iter_color = iter_colors[i]

            # Plot a line for each iteration of the optimization run
            for coefficients in self.iterated_coefficients[i]:
                plt.plot(x_axis, [self.priority_function(coefficients, x) for x in x_axis], color=iter_color, linestyle='solid')

            # Plot the final result from each optimization run
            plt.plot(x_axis, [self.priority_function(coefficients, x) for x in x_axis], color=result_color, linestyle='solid')

            i+=1
    
        # Plot the final total avreage from the results of all optimization runs
        plt.plot(x_axis, [self.priority_function(self.final_optimal_coefficients, x) for x in x_axis], '--r')
        plt.show()


if __name__ == "__main__":
    
    # Create calculator object
    priority_optimizer = Priority_Optimizer()
    priority_optimizer.run_weather_scenarios()
    # print(priority_optimizer.run_test_case())
    priority_optimizer.active_orders.to_csv('output_from_pri_scheme.csv')
    priority_optimizer.display_results()





# Ideas
"""
- Make the curve easy to change
- Vet the current output and investigate

- Incoperate the max_cc into the scheduling logic
    - Use max_cc_weather_multiplyer =1/(Weather_Prediction - Max_CC + 1)
    - Cap the max_cc value at .8 (max_cc values close to 1 will cause the multiplyer to skyrocket)
- Add weather file name to readout
- Add a try block before creating the final .csv

- Break code into multiple classes
    - One class to initialize with the parameteres for the pri function (0 meaning that the term will not be used)
    - One to run the optimization function 
+ add a bit of variance in dollar value between like orders so all $ values are different
- Plot each iteration of the optimization function

"""