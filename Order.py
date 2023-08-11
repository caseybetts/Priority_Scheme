# This contains the Order class

import math



class Order:
    """This is an instance of an order along with the weather preditction for a given access"""

    def __init__(self, weather, price, priority):
        self.weather = float(weather)
        self.price = float(price)
        self.priority = int(priority)

        # Variables
        self.coefficient = .47
        self.powers = 10
        self.rng = 100

        self.score = self.score()
        self.weather_dollars = self.price * self.weather

    # Returns the score for a given priority
    def score(self):
        return math.exp(self.coefficient*(self.powers-(5*self.priority)/self.rng))
