# This contains the Order class

import math



class Order:
    """This is an instance of an order along with the weather preditction for a given access"""

    def __init__(self, weather, price, priority):
        self.weather = float(weather)
        self.price = float(price)
        self.priority = int(priority)

        self.weather_dollars = self.price * self.weather

    # Returns the score for a given priority
    def set_score(self, coefficient, powers, _range):
        self.score = math.exp(coefficient*(powers-(5*self.priority)/_range))
