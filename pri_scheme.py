# Author: Casey Betts, 2023
# This tool models earth-imaging satellite capabilities and uses gradient descent to optimize how the satellite will choose imaging targets. 
# The prioritization scheme is considered optimized when the revenu generated by the model is maximized. The model is supplied with a list of orders
# all having specific location data and dollar amounts associated to them.

import json
import matplotlib.pyplot as plt
import pandas as pd

from datetime import datetime
from math import exp, sin, cos
from numpy import random, count_nonzero, isnan
from os import listdir
from scipy.optimize import minimize
from sys import argv 
from time import time

# Applicable json file name with parameters
loc_parameter_inputs = argv[1]
loc_case_inputs = argv[2]

# Initialize the random number generator
rng = random.default_rng()

# Read in the input parameters
with open(loc_parameter_inputs, 'r') as input:
    parameters = json.load(input)


class Priority_Optimizer:
    """ Contains the functions required to produce an optimal set of priorities for a given set of orders and cloud values """

    def __init__(self) -> None:

        # File locations
        self.active_orders_location = parameters["orders_csv"]
        self.cloud_cover_folder = parameters["clouds_folder"]

        # Optimization related variables
        self.optimization_method = parameters["optimization method"]
        self.optimization_tolerance = parameters["optimization tolerance"]
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
        self.test_coefficients = parameters["test coefficients"]
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
        self.prepare_dataframes()
        self.startup_readout()

        
    def load_data(self):
        """ Load the csv files into pandas dataframes """

        # Load orders and image strips .csv files into pandas dataframes
        self.active_orders = pd.read_csv(self.active_orders_location)
        self.case_inputs = pd.read_csv(loc_case_inputs)

        # Create variable to contain the latitudes that have orders in them
        self.active_latitudes = set(self.active_orders.Latitude)

        # Store the min and max of the active latitudes
        self.min_latitude = min(self.active_latitudes)
        self.max_latitude = max(self.active_latitudes)

    def prepare_dataframes(self):
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

        # Add Total column to the cases dataframe
        self.case_inputs["Total"] = 0

        # Save the index of new columns
        self.scheduled_column_index = self.active_orders.columns.get_loc("Scheduled")
        self.total_column_index = self.case_inputs.columns.get_loc("Total")
            
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
        
        # Return the value of a trig function with 2 variables
        a,b,c,d,e,f,g = coefficients

        return a + (b * .01 * (x-10)) + (c * .0011 * (x-10)**2) + (d * .000037 * (x-10)**3) + (e * .0000001 * (x - 10)**4) + (f * sin(x-10)) + (g * cos(x-10))
 
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
        """ Returns the sum of the dollars per square value of the schedule orders where actual CC value less than the max cc """

        # Get a sum of the dollars per square of the slice of orders that are scheduled and within cloud spec
        total_dollars = self.active_orders.DollarPerSquare[  (self.active_orders.Scheduled == True) & 
                                                    (self.active_orders.MAX_CC > self.active_orders["Actual_" + str(weather_column)])].sum()
        
        # Append the total dollars to the master list
        self.pri_scheme_total_dollars.append(total_dollars)

        return total_dollars

    def cost_function(self,coefficients):
        """ Returns the average dollar amount produced by all weather scenarios """
        
        # Replace the NaN values with 0
        coefficients = [0 if isnan(x) else x for x in coefficients]

        # Populate the priority values and therefore the order scores in the dataframe according to the new coefficients
        self.populate_priority(coefficients)
        self.populate_score()

        average_dollar_total = 0

        # Populate the total score and schedule the orders accordingly for each weather scenario
        for weather_column in range(self.weather_scenarios):

            self.populate_total_score(weather_column)
            self.schedule_orders()

            # Add the resulting total dollars for the current weather scenario
            average_dollar_total += self.total_dollars(weather_column)

        # Get the average dollar amounts for all the weather scenarios
        average_dollar_total = average_dollar_total / self.weather_scenarios

        # Return the average with a small perterbation to keep the optimizer from getting stuck
        return -average_dollar_total + rng.normal()
    
    def run_optimizations(self):
        """ Runs the optimizer for each row of initial coefficients in the dataframe """

        for starting_point in range(self.case_inputs.index.size):

            print("starting point :", starting_point)
            print(list(self.case_inputs.iloc[starting_point,:self.total_column_index]))

            # Uses the SciPy minimize function to find the optimal prioritization curve to maximize revenue
            result = minimize(self.cost_function, 
                            self.case_inputs.iloc[starting_point,:self.total_column_index],
                            tol=self.optimization_tolerance, 
                            method=self.optimization_method,
                            options={"maxiter":150})
            
            # Check for success or raise an error
            if not result.success:
                raise ValueError(result.message)

            # Update the Total column with the final dollar value result 
            self.case_inputs.iat[starting_point,self.total_column_index] = result.fun

            # Update the coefficient columns with the final coefficients
            for column in range(self.total_column_index):
                self.case_inputs.iat[starting_point, column] = result.x[column]

        print(self.case_inputs)

        # Create a .csv file of the resulting dataframe
        timestamp = str(datetime.now())[:19]
        timestamp = timestamp.replace(':','-')
        self.case_inputs.to_csv(r'Test_Case_Outputs\optimization_case_results_' + timestamp + '.csv')
        
    def run_simple_cases(self):
        """ Will run the cost funciton for all the given test cases """

        for test_case in range(self.case_inputs.index.size):

            # Produce a total dollar value for the current test case
            self.case_inputs.iat[test_case, self.total_column_index] = self.cost_function(self.case_inputs.iloc[test_case, :self.total_column_index])

        print(self.case_inputs)

        # Create a .csv file of the resulting dataframe
        timestamp = str(datetime.now())[:19]
        timestamp = timestamp.replace(':','-')
        self.case_inputs.to_csv(r'Test_Case_Outputs\simple_case_results_' + timestamp + '.csv')

    def startup_readout(self):
        """ Prints out useful information prior to running the program """

        print("Running ", self.weather_scenarios," weather scenarios")
        print("Optimization Method: ", self.optimization_method)

        # Timing 
        self.start_time = time()

    def display_results(self):
        """ Will print the resulting optimal priority function as well as display a graph of the all the results and the average result """

        # Timing and readout
        print("\n----------------------------------------------------------------")
        print("Time elapsed for coefficient run: ", time() - self.start_time)
        # print("Prioritization: ", self.coefficients[-1])
        # print("Average $ value: $", sum(self.pri_scheme_total_dollars)/len(self.pri_scheme_total_dollars))
        # print("Scenarios tried: ", len(self.pri_scheme_total_dollars))
        # print("Final $ value: $", -optimization_result.fun)
        print("----------------------------------------------------------------")

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
    priority_optimizer.run_optimizations()
    # priority_optimizer.run_simple_cases()
    # priority_optimizer.active_orders.to_csv('output_from_pri_scheme.csv')
    # priority_optimizer.display_results()





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
+ Plot each iteration of the optimization function
- Create a regimen of functions to manually test a variety of funcitons/coefficients
- Try a version that updates the score directly based on dollar value

"""