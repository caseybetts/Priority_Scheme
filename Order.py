# This contains the Order class

import math

# Variables
coefficient = .47
powers = 10
rng = 100

class Order:
    """This is an instance of an order along with the weather preditction for a given access"""

    def __init__(self, weather, price, priority):
        self.weather = float(weather)
        self.price = float(price)
        self.priority = int(priority)

        self.score = self.score()
        self.weather_dollars = self.price * self.weather

    # Returns the score for a given priority
    def score(self):
        return math.exp(coefficient*(powers-(5*self.priority)/rng))
