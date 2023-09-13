# Author: Casey Betts, 2023
# This is a calulator for optimizing a priority scheme

import csv
import pandas as pd
import geopandas as gpd
import math
import random
from Order import *

zero_dollar_cust_dpsqkm = { 82: 1, 
                            306: 2,
                            326: 2, 
                            331: 10, 
                            361: 5, 
                            366: 4,
                            381: 3,
                            10250: 15, 
                            12620: 14, 
                            12711: 14, 
                            20583: 20,
                            35915: 11, 
                            44924: 7,
                            58480: 13,
                            60569: 10,
                            60603: 9, 
                            100069: 8}

class Revenue_Calculator:
    """ Contains the functions required to calculate revenu for multiple iterations of a given priority curve """

    def __init__(self) -> None:

        # File locations
        self.active_orders_location = "active_orders.csv"
        self.cloud_cover_values_location = "cloudcover.csv"

        # Set variables
        self.weather_floor = .5
        self.variable_priorities = [700, 705, 710, 720, 730, 740, 750, 760, 770, 780, 790, 800]

        # Score Curve Variables
        self.coefficient = .47
        self.powers = 10
        self.range = 100

        # Run initial functions
        self.load_data()
        self.add_columns()
        self.populate_weather_predictions()
        self.populate_dollar_values()
        self.populate_priority()
        self.populate_score()
        self.populate_total_score()

    def load_data(self):
        """ Load the csv files into pandas dataframes """

        self.active_orders = pd.read_csv(self.active_orders_location)
        self.cloud_cover_values = pd.read_csv(self.cloud_cover_values_location)

        # Clean dataframes
        self.active_orders.drop(labels=["Unnamed: 0"], axis=1, inplace=True)

    def add_columns(self):
        """ Add the necessary columns and fill with a placeholder value"""

        self.active_orders["Predicted_CC"] = 0
        self.active_orders["New_Priority"] = 0
        self.active_orders["Score"] = 0
        self.active_orders["Total_Score"] = 0
        self.active_orders["Scheduled"] = False 
        self.active_orders["Clear"] = False

    def populate_weather_predictions(self):
        """ Populate a predicted cloud cover column in the active_orders dataframe with
            a randomly selected value from the cloud_cover dataframe with a similar latitude """
        
        self.active_latitudes = set(self.active_orders.Latitude)

        for latitude in self.active_latitudes:

            choices = list(self.cloud_cover_values[
                (self.cloud_cover_values.Latitude < latitude + 2) & 
                (self.cloud_cover_values.Latitude > latitude - 2)].CC)

            self.active_orders.Predicted_CC = self.active_orders.apply( lambda x: choice(choices) 
                                                                        if (x.Latitude == latitude) 
                                                                        else  x.Predicted_CC, axis=1)

    def populate_dollar_values(self):
        """ Populate DollarPerSquare column with dollar values based on existing dollar value or customer """

        # Use .loc to locate all orders with a customer in the zero dollar dictionary
        # Then set the dollar value equal to the corresponding value in the dictionary using the pandas mapping function based on the customer number
        self.active_orders.loc[self.active_orders.Cust_Num.isin(zero_dollar_cust_dpsqkm.keys()), 'DollarPerSquare'] = self.active_orders.Cust_Num.map(zero_dollar_cust_dpsqkm)

    def populate_priority(self):
        """ Add a priority to each order based on the dollar value (and potentially other factors)"""

        # create a set of all unique dollar values 
        all_dollar_values = set(self.active_orders.DollarPerSquare)

        # create a dictionary for mapping dollar values to priorities 
        dollar_to_pri_map = dict.fromkeys(all_dollar_values, 0) 

        # change the dict values to the correct (starting) priorities
        for value in dollar_to_pri_map:
            if value > 20: dollar_to_pri_map[value] = self.variable_priorities[0]
            if value <= 20: dollar_to_pri_map[value] = self.variable_priorities[1]  
            if value < 15: dollar_to_pri_map[value] = self.variable_priorities[2]
            if value < 12: dollar_to_pri_map[value] = self.variable_priorities[3]
            if value < 10: dollar_to_pri_map[value] = self.variable_priorities[4]
            if value < 8:  dollar_to_pri_map[value] = self.variable_priorities[5]
            if value < 6:  dollar_to_pri_map[value] = self.variable_priorities[6]
            if value < 4:  dollar_to_pri_map[value] = self.variable_priorities[7]
            if value < 3:  dollar_to_pri_map[value] = self.variable_priorities[8]
            if value < 2:  dollar_to_pri_map[value] = self.variable_priorities[9]
            if value < 1:  dollar_to_pri_map[value] = self.variable_priorities[10]      
            if value == 0: dollar_to_pri_map[value] = self.variable_priorities[11]

        # Set the priority value equal to the corresponding value in the dictionary using the pandas mapping function based on the dollar value
        self.active_orders['New_Priority'] = self.active_orders.DollarPerSquare.map(dollar_to_pri_map)

    def priority_to_score(self, priority):
        """ Given a priority will return a score based on the FOM curve"""

        # mathematical conversion from the priority to the score
        return math.exp(self.coefficient*(self.powers-(5*priority)/self.range))

    def populate_score(self):
        """ populate a score to each order based on the priority of the order """

        # Set the score
        self.active_orders.Score = self.active_orders.apply( lambda x: self.priority_to_score(x.New_Priority-700), axis=1)

    def populate_total_score(self):
        """ populate a column for total score which is the score multiplied by the predicted cloud cover """

        # Set the total score
        self.active_orders.Total_Score = self.active_orders.apply( lambda x: (1 - x.Predicted_CC) * x.Score, axis=1)

    def schedule_orders(self):
        """ Return the list of orders that are have the maximum score within their respective 2 degree lat """

        latitude = min(self.active_latitudes)
        scheduled_order_indexes = []

        while latitude < max(self.active_latitudes) + 1:
            order_list = self.active_orders[(self.active_orders.Latitude == latitude) | (self.active_orders.Latitude == latitude + 1)]
            
            if not order_list.empty:
                max_index = order_list.Total_Score.idxmax()
                self.active_orders.iloc[max_index, 8 ] = True

            latitude += 2

    def set_clear_orders(self):
        """ Randomly populate change the scheduled order's clear column with True based on their predicted CC"""

        # .loc function locates the "Clear" column for all orders that are activly scheduled 
        # .apply function applies True if collect is 'actually' clear otherwise False
        # the 'Predicted_CC' is augmented by adding a random value between -.01 and .01 in order to make the chance of clear collect not equal to the predicted chance of clear collect
        # random.random() is used to choose a 'actual' CLEAR percentage
        # if the percent clear is greater than the augmented predicted percent, then the image is clear
        # therefore the chance of a collect being clear is close to the predicted chance
        self.active_orders.loc[self.active_orders.Scheduled == True, "Clear"] = self.active_orders.apply(lambda x: True
                                                                                        if (random.random() > (x.Predicted_CC + (random.random() - .5) * .2) )
                                                                                        else False, axis=1)                                                                                                  
    def total_dollars(self):
        """ Returns the sum of all the dollars per square with a "Clear" value of True """

        return self.active_orders.loc[self.active_orders.Clear == True, 'DollarPerSquare'].sum()



if __name__ == "__main__":
    
    # Create calculator object
    revenue_calculator = Revenue_Calculator()

    revenue_calculator.schedule_orders()
    revenue_calculator.set_clear_orders()
    print(revenue_calculator.total_dollars())

    revenue_calculator.active_orders.to_csv('output_from_pri_scheme.csv')

    # run all_vals
    #all_vals = revenue_calculator.run_combinations(orderlist1, orderlist2, 100)
    #print(revenue_calculator.stats(all_vals))



# To do
# 1.1 *Arc) Create a selection of orders that would be accessable on one rev
# 1.2 *Arc) Create a cloud cover list. A list of possible cloud cover values that is proportionate to global cc values
# 2. For each order assign a random cloud cover
# 3.1 Apply a dollar value to each order
# 3.2 Assign a priority to each order based on dollar value
# 3.3 Assign a score to each order based on the priority
# 4. For each order the Order score and Cloud Cover score are multiplied to give the total score
# 5.1 For every 2 degrees of latitude compare total scores for each order and select the highest value for all orders that fall within the lat bucket
# 5.3 Randomly decide if the order is clear where the chance of being clear is (1 - the cloud cover score + (random(1,-1) * uncertainty))
# 6.1 Sum the $ made for all the lat buckets
# 6.2 Return the total $ for this particular prioritization scheme
# 6.3 Run model 100 times to simulate different cloud cover possibilities
# 7 Use gradient decent to determine best prioritization using each pri value as a dimension  