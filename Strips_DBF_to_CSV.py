# Author: Casey Betts, 2023
# This file holds a class to receive 90 day strip .dbf files and output a .csv

import pandas as pd
import geopandas as gpd 

class Strips_dbf_to_csv:
    """ This class will create a new .csv file that combines all the 90 day strips files
    and remove the unnecessary fields"""

    def __init__(self) -> None:
        
        # File locations
        self.strip_file_locations = ["Rev11413\GE01_90dayStrips_11413.dbf", 
                                    "Rev11413\WV01_90dayStrips_11413.dbf",
                                    "Rev11413\WV02_90dayStrips_11413.dbf",
                                    "Rev11413\WV03_90dayStrips_11413.dbf"]

    def load_dbf_to_dataframe(self):
        """ Given one or more dbf files from the 90 day strips, 
        will return a pandas dataframe for each in a list"""

        dataframe_list = []

        for location in self.strip_file_locations:        
            # Create dataframes and add them to a list
            dataframe = gpd.read_file(location)
            dataframe_list.append(dataframe)

        return dataframe_list
    
    def merge_and_clean(self):
        """ Given one or more dataframes, this will merge them into one 
        and remove unnecessary fields"""
        pass 




if __name__ == "__main__":

    strips = Strips_dbf_to_csv()
    print(strips.load_dbf_to_dataframe())




