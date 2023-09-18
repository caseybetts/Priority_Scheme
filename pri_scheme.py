# Author: Casey Betts, 2023
# This is a calulator for optimizing a priority scheme

import pandas as pd
from math import exp
from random import choice, random
from scipy.optimize import minimize 
from time import time
import matplotlib.pyplot as plt

zero_dollar_cust_dpsqkm = { 82: 1, 
                            306: 2,
                            326: 2, 
                            331: 10, 
                            361: 3, 
                            366: 4,
                            381: 2,
                            10250: 15, 
                            12620: 14, 
                            12711: 14, 
                            20583: 20,
                            35915: 11, 
                            44924: 4,
                            58480: 13,
                            60569: 10,
                            60603: 5, 
                            100069: 4}

test_cases = [
    [.007, .008, .008, .008, .008, .008, .008, .008, .008, .008, .008, .008, .008],
    [.007, .008, .008, .008, .008, .008, .008, .008, .008, .008, .008, .008, .008],
    [.007, .007, .008, .008, .008, .008, .008, .008, .008, .008, .008, .008, .008],
    [.007, .007, .007, .008, .008, .008, .008, .008, .008, .008, .008, .008, .008],
    [.007, .007, .007, .007, .008, .008, .008, .008, .008, .008, .008, .008, .008],
    [.007, .007, .007, .007, .007, .008, .008, .008, .008, .008, .008, .008, .008],
    [.007, .007, .007, .007, .007, .007, .008, .008, .008, .008, .008, .008, .008],
    [.007, .007, .007, .007, .007, .007, .007, .008, .008, .008, .008, .008, .008],
    [.007, .007, .007, .007, .007, .007, .007, .007, .008, .008, .008, .008, .008],
    [.007, .007, .007, .007, .007, .007, .007, .007, .007, .008, .008, .008, .008],
    [.007, .007, .007, .007, .007, .007, .007, .007, .007, .007, .008, .008, .008],
    [.007, .007, .007, .007, .007, .007, .007, .007, .007, .007, .007, .008, .008],
    [.007, .007, .007, .007, .007, .007, .007, .007, .007, .007, .007, .007, .008],
    [.007, .007, .007, .007, .007, .007, .007, .007, .007, .007, .007, .007, .007],
]

class Revenue_Calculator:
    """ Contains the functions required to calculate revenu for multiple iterations of a given priority curve """

    def __init__(self) -> None:

        # File locations
        self.active_orders_location = "active_orders.csv"
        self.cloud_cover_values_location = "cloudcover.csv"

        # Set variables
        self.initial_priorities = [ 7.305e-03,  7.527e-03,  7.431e-03,  7.570e-03,  7.688e-03, 
                                   7.488e-03,  7.683e-03,  7.699e-03,  7.914e-03,  7.650e-03,
                                    7.576e-03,  7.815e-03]
        self.number_of_scenarios = 1
        self.bounds = [(.007,.008) for x in range(12)]
        self.cloud_cover_buckets = {}
        self.scale = 100000
        self.clear_columns = 3
        self.dollar_breaks = [20, 15, 12, 10, 8, 6, 4, 3, 2, 1, 0]

        # Score Curve Variables
        self.coefficient = .47
        self.powers = 10
        self.range = 100

        # Run initial functions
        self.load_data()
        self.add_columns()
        self.create_cloud_cover_buckets()
        self.populate_predicted_cc()
        self.set_clear_orders()
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
        self.active_orders["Predicted_CC"] = 0
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
    
    def populate_predicted_cc(self):

        self.active_orders.Predicted_CC = self.active_orders.apply( lambda x: choice(self.cloud_cover_buckets[x.Latitude]), axis=1)

    def set_clear_orders(self):
        """ Randomly create and populate clear columns with True based on their predicted CC """

        # several columns should be created so the average dollar total will very unlikely contain extreme cases (like all the high dollar ordres being cloudy)

        for i in range(self.clear_columns):
        # .loc function locates the "Clear" column for all orders
        # .apply function applies True if collect is 'actually' clear otherwise False
        # the 'Predicted_CC' is augmented by adding a random value between -.01 and .01 in order to make the chance of clear collect not equal to the predicted chance of clear collect
        # random.random() is used to choose a 'actual' CLEAR percentage
        # if the percent clear is greater than the augmented predicted percent, then the image is clear
        # therefore the chance of a collect being clear is close to the predicted chance
            self.active_orders[i] = self.active_orders.apply(lambda x: True
                                                                if (random() > (x.Predicted_CC + (random() - .5) * .2) )
                                                                else False, axis=1)     
        
    def populate_dollar_values(self):
        """ Populate DollarPerSquare column with dollar values based on existing dollar value or customer """

        # Use .loc to locate all orders with a customer in the zero dollar dictionary
        # Then set the dollar value equal to the corresponding value in the dictionary using the pandas mapping function based on the customer number
        self.active_orders.loc[self.active_orders.Cust_Num.isin(zero_dollar_cust_dpsqkm.keys()), 'DollarPerSquare'] = self.active_orders.Cust_Num.map(zero_dollar_cust_dpsqkm)

    def populate_priority(self, priority_list):
        """ Add a priority to each order based on the dollar value (and potentially other factors)"""

        # create a set of all unique dollar values 
        all_dollar_values = set(self.active_orders.DollarPerSquare)

        # create a dictionary for mapping dollar values to priorities 
        dollar_to_pri_map = dict.fromkeys(all_dollar_values, 0) 

        # change the dict values to the correct (starting) priorities
        for value in dollar_to_pri_map:
            if value >  self.dollar_breaks[0]: dollar_to_pri_map[value] = priority_list[0]
            if value <= self.dollar_breaks[0]: dollar_to_pri_map[value] = priority_list[1]  
            if value <  self.dollar_breaks[1]: dollar_to_pri_map[value] = priority_list[2]
            if value <  self.dollar_breaks[2]: dollar_to_pri_map[value] = priority_list[3]
            if value <  self.dollar_breaks[3]: dollar_to_pri_map[value] = priority_list[4]
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

    def populate_total_score(self):
        """ Populate a column for total score which is the score multiplied by the predicted cloud cover """

        # Set the total score
        self.active_orders.Total_Score = self.active_orders.apply( lambda x: (1 - x.Predicted_CC) * x.Score, axis=1)
    
    def schedule_orders(self):
        """ Return the list of orders that are have the maximum score within their respective 2 degree lat """

        latitude = self.min_latitude

        while latitude < self.max_latitude + 1:
            order_list = self.active_orders[(self.active_orders.Latitude == latitude) | (self.active_orders.Latitude == latitude + 1)]
            
            if not order_list.empty:
                max_index = order_list.Total_Score.idxmax()
                self.active_orders.iloc[max_index, 8 ] = True

            latitude += 2                                                                                         
    
    def total_dollars(self, clear_column):
        """ Returns the sum of all the dollars per square with a 'Clear' value of True for a given column"""

        return self.active_orders.DollarPerSquare[(self.active_orders.Scheduled == True) & (self.active_orders[clear_column] == True)].sum()

    def run_scenario(self, clear_column):
        """ This will reassign each order with a random weather prediction and then reschedule orders accordingly and return a total dollar amount """

        # Reset the schedule by setting all 'Scheduled' to False
        self.active_orders.Scheduled = False

        # Calculate the total score and which orders are scheduled
        self.populate_total_score()
        self.schedule_orders()

        return self.total_dollars(clear_column)

    def run_priority_scheme(self, priority_scheme, clear_column):
        """ Will run the set number of scenarios with a given prioritization scheme and return the average total dollar value """

        # Apply the given priority values to the orders
        self.populate_priority(priority_scheme)
        self.populate_score()

        return -self.run_scenario(clear_column)
    
    def optimal_priorities(self, clear_column):
        """ Uses the SciPy optimization tools to find the optimal prioritization scheme to maximize revenue for a given clear scenario """

        # Timing 
        start_time = time()

        result = minimize(self.run_priority_scheme, self.initial_priorities, args=clear_column, bounds=self.bounds, tol=.1, method='Nelder-Mead')

        # Timing 
        end_time = time()
        print("Time elapsed for scheme: ", end_time - start_time)
        print("----------------------------------------------------------------")

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


        print("Average Prioritization: ", average_prioritization)
        print("-----------------------------------------")

        x_axis = [30] + self.dollar_breaks
        plt.plot(x_axis, average_prioritization)
        plt.show()



    def run_test_cases(self):
        """ Will run the priority_scheme function for each test case priority set """

        for scheme in test_cases:
            self.run_priority_scheme(scheme)
        


if __name__ == "__main__":
    
    # Create calculator object
    revenue_calculator = Revenue_Calculator()
    revenue_calculator.run_clear_scenarios()
    revenue_calculator.active_orders.to_csv('output_from_pri_scheme.csv')



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

# 8 Create 3 Clear columns semi-randomly populated
# 9 Run the optimization function and save the result over each clear column values
# 9.1 Save the average of the three runs
# 10 Re-run the weather column values and repeat step 9 10 times
# 11 Average the averages for the final result