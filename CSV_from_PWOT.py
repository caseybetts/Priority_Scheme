# Author: Casey Betts, 2023
# The purpose of this file is to convert a PWOT geotiff file to a CSV with the latitude/longitude associated to each pixel

import rasterio
import numpy as np
import pandas as pd

from os import listdir
from sys import argv 

# Get orders .csv filename 
orders_filename = argv[1]

def PWOT_dataframe(PWOT_filename):
    """ Returns a dataframe of the raster values with their associated latitudes and longitudes"""

    with rasterio.open(PWOT_filename) as dataset:
        band = dataset.read(1)

        # PWOT files extend to the full globe
        lat_min = -90
        lat_max = 90
        lon_min = -180
        lon_max = 180  

        # Each pixel has height and width of a quarter degree
        step = 0.25

        # Calculate the number of rows and columns in the image
        rows = int((lat_max - lat_min) / step) 
        cols = int((lon_max - lon_min) / step)

        # Create lists of each latitude and longitude in the file
        lats = [lat_max - step * i for i in range(rows)]
        lons = [lon_min + step * j for j in range(cols)]
        
        # Create dataframe with values, latitude and longitude
        df = pd.DataFrame({'Value': band.flatten(),
                        'Latitude': np.repeat(lats, cols),
                        'Longitude': np.tile(lons, rows)})
            
    return df

def trim_PWOT_dataframe(dataframe):
    """ Remove PWOT values that do not intersect the longitudes of the active orders """

    # Open the .csv containing all the orders
    with open(orders_filename) as f:
        orders = pd.read_csv(f)

    
    active_longitudes = set(orders.Longitude)
    max_longitude = max(active_longitudes) + 1
    min_longitude = min(active_longitudes) - 1

    return dataframe[(dataframe.Longitude > min_longitude) & (dataframe.Longitude < max_longitude)]

def dataframe_to_csv(dataframe, filename):
    # Save the dataframe to a .csv file
    dataframe.to_csv(filename)


if __name__ == "__main__":

    cloud_file_names = [x for x in listdir('PWOT') if x[-1] == "f"]
    count = 0

    for file in cloud_file_names:
        dataframe_to_csv(trim_PWOT_dataframe(PWOT_dataframe('PWOT\\'+ file)),
                     'PWOT_CSV\\' + file[5:18] + ".csv")
        
        # Print out statusing on the progress
        count += 1
        if count in [50,100,150,200]:
            print(count, " complete")    