# Author: Casey Betts, 2024
# This file contains the Optimizer class which will optimize a curve used to prioritize the given orders set

import matplotlib.pyplot as plt
import json
import pandas as pd 
from Orders import Orders

from datetime import datetime
from math import ceil, exp, sin, cos, exp
from numpy import random, isnan
from scipy.optimize import minimize
from time import time


class Optimizer:
    """ Object which can use a dataframe of orders and manually or algorithmically produce a maximum dollar value priority curve. """

    def __init__(self, parameters_location, cases_location) -> None:

        # Read in the input parameters
        self.cases_location = cases_location
        with open(parameters_location, 'r') as input:
            parameters = json.load(input)

        # Random number generator
        self.rng = random.default_rng()

        # Optimization related variables
        self.optimization_method = parameters["optimization method"]
        self.optimization_tolerance = parameters["optimization tolerance"]
        self.max_iterations = 150
        self.run_coefficients = []
        self.iterated_coefficients = []
        self.weather_scenarios = parameters["number of weather scenarios"]
        self.weather_type = parameters["weather_type"]
        self.x_axis = parameters["plot x-axis"]
        
        # Dataframe
        self.orders = Orders(parameters)

        # Functions
        self.load_data()
        self.startup_readout()

    def load_data(self):
        """ Loads the .csv file with the starting functions into a pandas dataframe """

        # load the initial cases into a pandas df, save the number of cases and create a copy for the results df
        self.case_inputs = pd.read_csv(self.cases_location)
        self.initial_case_count = self.case_inputs.index.size
        self.case_results = self.case_inputs.copy()

        # Add 'Total' column to the cases dataframe
        self.case_results["Total"] = 0

        # Save the index of new column
        self.total_column_index = self.case_results.columns.get_loc("Total")

    def startup_readout(self):
        """ Prints out useful information prior to running the program """

        print("Running ", self.weather_scenarios," weather scenarios")
        print("Optimization Method: ", self.optimization_method)
        print("Weather Type: ", self.weather_type)

        # Timing 
        self.start_time = time()

    def produce_optimized_curves(self):
        """ Runs the optimizer for each row of initial coefficients in the dataframe """

        # for each row of the input spreadsheet find the optimized coefficients and add the results to the df
        for starting_point in range(self.initial_case_count):

            # Get the coefficients
            coefficients = self.case_inputs.iloc[starting_point,:]
            print("case number :", starting_point)

            # Generate the initial curve in order to perform the curve check on the starting curve
            curve = self.produce_curve(coefficients)

            # Make sure the starting function is valid
            if self.curve_check(curve) == 1:
                
                # Uses the SciPy minimize function to find the optimal prioritization curve to maximize revenue
                result = minimize(self.cost_function, 
                                coefficients,
                                tol=self.optimization_tolerance, 
                                method=self.optimization_method,
                                options={"maxiter":self.max_iterations})
                
                # Raise an error if not successful
                if not result.success:
                    if result.message != "Maximum number of function evaluations has been exceeded.":
                        raise ValueError("Optimization Failed for starting point: "+ str(starting_point) + "\n\t\t" + result.message)

                # Update the Total column of the results dataframe with the final dollar value result 
                self.case_results.iat[starting_point,self.total_column_index] = round(result.fun,2)

                # Update the coefficient columns with the final coefficients
                for column in range(self.total_column_index):
                    self.case_results.iat[starting_point, column] = result.x[column]
            
            else: 
                # Print the coefficients and the curve values if the starting curve is not within bounds
                print("This starting point is not within the required bounds: \n\t", coefficients)
                print("Curve values:", [curve(x) for x in range(50)])     

            # Print the time elapsed for each optimization run
            print("\n----------------------------------------------------------------")
            print("\n----------------------------------------------------------------")
            print("Time elapsed for case: ", time() - self.start_time)

        # Repeat the above step with the best case as the initial parameters
        best_row = self.case_results.Total.idxmin()
        coefficients = self.case_results.iloc[best_row,:-1]
        # Add the coefficients with the best result to the initial cases df
        self.case_inputs.loc[self.initial_case_count] = coefficients
        curve = self.produce_curve(coefficients)
        # Run the optimizer on the new found coefficient list and save to a class var
        self.iterative_result = minimize(self.cost_function, 
                coefficients,
                tol=self.optimization_tolerance, 
                method=self.optimization_method,
                options={"maxiter":self.max_iterations})
        if not self.iterative_result.success:
            if self.iterative_result.message != "Maximum number of function evaluations has been exceeded.":
                raise ValueError("Optimization Failed for starting point: "+ str(starting_point) + "\n\t\t" + self.iterative_result.message)
        # Append the resulting coefficients and total value to the results df
        self.case_results.loc[self.initial_case_count] = (list(self.iterative_result.x) + [0])
        self.case_results.iat[self.initial_case_count, self.total_column_index] = round(self.iterative_result.fun,2)

    def curve_check(self, func):
        """ Checks that the given coefficients create a curve that adheres to the priority value requirements """
        
        pri_max = 100
        max_multiplyer = 1
        min_multiplyer = 1
        all_values = []

        # Get all values in a list
        for i in range(50):
            all_values.append(func(i))
        
        # Find the max and min values
        max_val = max(all_values)
        min_val = min(all_values)

        # If the max value is too large then increase the multiplyer accordingly
        if max_val > pri_max:
            max_multiplyer = max_val - pri_max
        
        # Note: min priority must be 0 to make the multiplyer positive
        if min_val < 0:
            min_multiplyer = -min_val
        
        return ceil((max_multiplyer**2 + min_multiplyer**2)/2)
    
    def cost_function(self, coefficients):
        """ First applies the given coefficients to the pri curve and changes the priority, score and total score.
            Then reschedules the order deck.
            And finally returns the average dollar amount produced by all weather scenarios """

        # Timing 
        start_time = time()

        # Generate curve
        curve = self.produce_curve(coefficients)

        # Check to see if the curve is within acceptable range and update the result multiplier
        multiplyer = self.curve_check(curve)

        # Populate the priority values and therefore the order scores in the dataframe according to the new coefficients
        self.orders.populate_priority(curve)
        self.orders.populate_score()

        average_dollar_total = 0

        # Populate the total score and schedule the orders accordingly for each weather scenario
        for weather_column in range(self.weather_scenarios):

            # Reset the Scheduled column
            self.orders.active_orders.Scheduled = False

            # Populate total score based on the current weather file and scheduled the orders
            self.orders.populate_total_score(weather_column)
            self.orders.schedule_orders()

            # Add the resulting total dollars for the current weather scenario
            average_dollar_total += self.orders.total_dollars(weather_column)

        # Get the average dollar amounts for all the weather scenarios
        average_dollar_total = average_dollar_total / self.weather_scenarios
        # Multiply by the 'out of bounds' multiplyer and add a small random value
        average_dollar_total = -(average_dollar_total / multiplyer) + (self.rng.normal() * .1)

        # Timing
        print("\n----------------------------------------------------------------")
        print("Time elapsed for cost function: ", time() - start_time)
        print("Average dollar total: ", average_dollar_total)
        print("multiplyer:", multiplyer)
        print("Coefficients:", coefficients)

        # Return the average with a small perterbation to keep the optimizer from getting stuck
        return average_dollar_total
    
    def produce_curve(self, coefficients):
        """ Returns a function representing a priority curve using the given coefficients """

        a,b,c,d,e,f,g = [0 if isnan(x) else x for x in coefficients]
        return lambda x: a + (b * x) + (c * exp(0.04*x)) + (d * x**(1/2)) + (e * (x - 15)**2) + (f * sin(.2*(x-10))) + (g * cos(.2 * (x-10)))

    def run_simple_cases(self):
        """ Runs the cost funciton for all the given test cases """

        for test_case in range(self.case_inputs.index.size):

            # Produce a total dollar value for the current test case
            self.case_results.iat[test_case, self.total_column_index] = self.cost_function(self.case_inputs.iloc[test_case, :])

        print(self.case_results)

        # Create a .csv file of the resulting dataframe
        timestamp = str(datetime.now())[:19]
        timestamp = timestamp.replace(':','-')
        self.case_results.to_csv(r'Test_Case_Outputs\simple_case_results_' + timestamp + '.csv')

    def display_results(self):
        """ Creates .csv file, print out and plots with the resulting data """

        # print the results of all starting function
        print(self.case_results)
        print("------------------")
        print(self.case_inputs)

        # Create a .csv file of the resulting dataframe
        timestamp = str(datetime.now())[:19]
        timestamp = timestamp.replace(':','-')
        self.case_results.to_csv(r'Test_Case_Outputs\optimization_case_results_' + timestamp + '.csv')

        # plot the initial and final curve for each test case

        case_count = self.case_results.shape[0]
        x_axis = range(self.x_axis)
        initial_values = []
        result_values = []

        # Create a figure with several subplots (axs). Number of cases divided by 3 as the number of row and 3 columns
        fig, axs = plt.subplots(ceil(case_count/3), 3, figsize=(9, 9))
        fig.tight_layout(pad=3.0)

        # Iterate over the rows of the initial cases and append the lists of values to the lists
        for row in self.case_inputs.itertuples(index=False, name=None):
            initial_values.append([self.produce_curve(row)(x) for x in x_axis])

        # Iterate over the rows of the resulting cases and append the lists of values to the lists
        for row in self.case_results.itertuples(index=False, name=None):
            result_values.append([self.produce_curve(row[:-1])(x) for x in x_axis])

        # Iterate over the subplots and apply the two curves to them 
        for count, ax in enumerate(axs.flat):
            
            if count < case_count:
                ax.plot(x_axis, result_values[count], color='cornflowerblue', linestyle='solid', linewidth=7.0)
                ax.plot(x_axis, initial_values[count], color='lavender', linestyle='solid')
                ax.set_title("$" + str(-self.case_results.Total[count]))
                ax.set_xlabel('Dollar Value', fontsize = 8) 
                ax.set_ylabel('Priority', fontsize = 8) 
                ax.set_ylim([0, 100])

        ax = plt.gca()
        ax.set_ylim([0, 100])
        plt.show()


