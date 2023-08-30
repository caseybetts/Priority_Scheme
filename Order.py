# This contains the Order class

import math
from random import choice

print("mychoice", choice([1,2,3]))

class Order:
    """This is an instance of an order along with the weather preditction for a given access"""

    def __init__(self, weather, price, priority):
        self.weather = float(weather)
        self.price = float(price)
        self.priority = int(priority)
        self.weather_dollars = self.price * self.weather
        self.predicted_cc = None

    # Returns the score for a given priority
    def set_score(self, coefficient, powers, _range):
        self.score = math.exp(coefficient*(powers-(5*self.priority)/_range))

    def assign_cloud_prediction(self, cc_list):
        """ Given a list of cloud cover scores will choose one at random"""

        self.predicted_cc = choice(cc_list)



if __name__ == "__main__":

    myOrder = Order(1,2,3)
    # myOrder.assign_cloud_prediction([22,33])

    print(myOrder.predicted_cc)

