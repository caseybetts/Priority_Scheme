# Author: Casey Betts, 2023
# This is a calulator for optimizing a priority scheme

import csv
import pandas as pd
import geopandas as gpd
import random
from Order import *

class Revenue_Calculator:
    """ Contains the functions required to calculate revenu for multiple iterations of a given priority curve """

    def __init__(self) -> None:

        # Set variables
        self.weather_floor = .5

        # Score Curve Variables
        self.coefficient = .47
        self.powers = 10
        self.range = 100

        # Run initial functions
        self.load_data()

    def load_data(self):
        """ Load the csv files """

        with open("CloudandOrderSample.csv", "r") as f:
            self.primary_order = list(csv.reader(f, delimiter=","))
        
        self.primary_order[0][0] = 0.564961 # fix a formatting issue

    def create_orders(self):
        """ Creates all the order objects and returns them in a list"""
        orders = []

        for i in self.primary_order:
            order = Order(i[0],i[1],i[2])
            order.set_score(self.coefficient, self.powers, self.range)
            orders.append(order)

        return orders

    # Create a new list to contain the results of competition
    def find_weighted_dollar_total(self, primary, competing, floor):
        """ Given two order tables and a pri-score model, this returns the sum of the
        weighted value of the winning orders"""

        results = []

        for i in range(len(primary)):

            # Calculate final score for both orders
            primary_score = primary[i].score*max(primary[i].weather, floor)
            competing_score = competing[i].score*max(competing[i].weather, floor)

            if primary_score > competing_score:
                results.append([1, primary[i].price , primary[i].weather, primary[i].weather_dollars ])
            else:
                results.append([1, competing[i].price , competing[i].weather, competing[i].weather_dollars ])

        # Calculate sum total of the weighted dollar value
        results_weighted_dollar_sum = 0
        for i in results:
            results_weighted_dollar_sum += i[3]

        return round(results_weighted_dollar_sum, 2)

    def print_results(self, total_1, floor_1, total_2, floor_2):
        """ Paramerters:
            total_1: float dollar value
            model_1: float model type
            total_2: float dollar value
            model_2: float model type"""

        print(floor_1,"Total $:", round(total_1, 2), floor_2, "Total $:", round(total_2, 2))

    def find_all_floor_totals(self):
        """ Returns a list of totals for all floor values from 0, .1, .2, ..., 1 """
        results = []

        for floor in range(0,11):
            floored_total = self.find_weighted_dollar_total(orderlist1, orderlist2, floor/10)
            results.append(floored_total)
            #print("For floor value:", floor/10, "Total $=", floored_total)

        return results

    def run_combinations(self, orderlist1, orderlist2, num):
        """ Return a list of multiple combinations of order competition """
        results = []

        for i in range(num):
            random.shuffle(orderlist2)
            totals = self.find_all_floor_totals()
            results.append(totals)

        return results

    def stats(self, table):
        """ Return the max, min and average of all the tests for each floor value """
        averages = []

        for i in range(len(table[0])):
            sum = 0

            for j in table:
                sum += j[i]

            averages.append(round(sum/len(table),2))

        return averages



if __name__ == "__main__":
    
    # Create calculator object
    revenue_calculator = Revenue_Calculator()

    # Create list of order objects
    orderlist1 = revenue_calculator.create_orders()

    # Create and shuffle the secondary list of order objects
    orderlist2 = orderlist1.copy()

    # run all_vals
    #all_vals = revenue_calculator.run_combinations(orderlist1, orderlist2, 100)
    #print(revenue_calculator.stats(all_vals))



# To do
# 1.1 *Arc) Create a selection of orders that would be accessable on one rev
# 1.2 *Arc) Create a cloud cover list. A list of possible cloud cover values that is proportionate to global cc values
# 2. For each order assign a random cloud cover
# 3. Each order will have a priority applied and then can be mapped to the score
# 4. For each order the Order score and Cloud Cover score are multiplied to give the total score
# 5.1 For every 2 degrees of latitude find all orders that fall within the lat bucket
# 5.2 Compare total scores for each order and select the highest value
# 5.3 Randomly decide if the order is clear where the chance of being clear is (1 - the cloud cover score + (random(1,-1) * uncertainty))
# 5.4 Update the $ made for the lat bucket
# 6.1 Sum the $ made for all the lat buckets
# 6.2 Return the total $ for this particular prioritization scheme
# 7 Use gradient decent to determine best prioritization using each pri value as a dimension  