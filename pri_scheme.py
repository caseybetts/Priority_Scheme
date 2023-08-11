# This is a calulator for optimizing a priority scheme

import csv
import math
import random
from Order import *


weather_floor = .5

# Load the csv files
file = open("CloudandOrderSample.csv", "r")
primary_order = list(csv.reader(file, delimiter=","))
file.close
file = open("CloudandOrderSample2.csv", "r")
set_competing_order = list(csv.reader(file, delimiter=","))
file.close
primary_order[0][0] = 0.564961 # fix a formatting issue

def create_orders(spreadsheet):
    """ Creates all the order objects and returns them in a list"""
    orders = []

    for i in spreadsheet:
        order = Order(i[0],i[1],i[2])
        orders.append(order)

    return orders

# Create a new list to contain the results of competition
def find_weighted_dollar_total(primary, competing, floor):
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

def print_results(total_1, floor_1, total_2, floor_2):
    """ Paramerters:
        total_1: float dollar value
        model_1: float model type
        total_2: float dollar value
        model_2: float model type"""

    print(floor_1,"Total $:", round(total_1, 2), floor_2, "Total $:", round(total_2, 2))


def find_all_floor_totals():
    """ Returns a list of totals for all floor values from 0, .1, .2, ..., 1 """
    results = []

    for floor in range(0,11):
        floored_total = find_weighted_dollar_total(orderlist1, orderlist2, floor/10)
        results.append(floored_total)
        #print("For floor value:", floor/10, "Total $=", floored_total)

    return results

def run_combinations(orderlist1, orderlist2, num):
    """ Return a list of multiple combinations of order competition """
    results = []

    for i in range(num):
        random.shuffle(orderlist2)
        totals = find_all_floor_totals()
        results.append(totals)

    return results

def stats(table):
    """ Return the max, min and average of all the tests for each floor value """
    averages = []

    for i in range(len(table[0])):
        sum = 0

        for j in table:
            sum += j[i]

        averages.append(round(sum/len(table),2))

    return averages



# ##  Main program ## #


# Create list of order objects
orderlist1 = create_orders(primary_order)

# Create and shuffle the secondary list of order objects
orderlist2 = orderlist1.copy()

all_vals = run_combinations(orderlist1, orderlist2, 1000)

print(stats(all_vals))
