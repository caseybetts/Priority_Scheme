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
        
        self.df_list = self.load_dbf_to_dataframe()
        self.merged_df = self.merge_and_clean(self.df_list)

    def load_dbf_to_dataframe(self):
        """ Given one or more dbf files from the 90 day strips, 
        will return a pandas dataframe for each in a list"""

        dataframe_list = []

        for location in self.strip_file_locations:        
            # Create dataframes and add them to a list
            dataframe = gpd.read_file(location)
            dataframe_list.append(dataframe)

        return dataframe_list
    
    def merge_and_clean(self, dataframe_list):
        """ Given a list of one or more dataframes, this will merge them into one 
        and remove unnecessary fields"""
        
        result = pd.concat(dataframe_list)

        columns_to_drop = ['CATALOG_ID', 'DATA_LOCAT', 'END_TIME', 'ITERATION',
       'START_ONA', 'END_ONA', 'START_PANR', 'AVG_PANR', 'END_PANR',
       'START_MULR', 'AVG_MULR', 'END_MULR', 'START_TAZI', 'AVG_TAZI',
       'END_TAZI', 'AVG_SUN_EL', 'AVG_SUN_AZ', 'AREA', 'BEARING', 'CALIBRATIO',
       'IS_NOMINAL', 'PIXEL_ROW_', 'START_LINE', 'END_LINE', 'IS_TTLC_AV',
       'IS_FPE_AVA', 'RA_AVAIL', 'RE_AVAIL', 'IS_ADJ_EPH', 'PAN_PIXCNT',
       'MUL_PIXCNT', 'INGEST_PRI', 'SENSOR_VEH', 'GROUND_STA', 'QUALITY_CO',
       'ABSOLUTE_G', 'RELATIVE_G', 'BROWSE_UPD', 'IS_CENTER_', 'SCAN_DIREC',
       'DL_START', 'DL_END', 'CGS_ALONG', 'CGS_ACROSS', 'LGS_ALONG',
       'LGS_ACROSS', 'LINK', 'ACCESSLEVE', 'IMAGEBANDS',
       'geometry', 'VNIRASSOC', 'SWIRASSOC',
       'CAVISASSOC']
        
        result.drop(labels=columns_to_drop, axis=1, inplace=True)

        return result


if __name__ == "__main__":

    strips = Strips_dbf_to_csv()
    print(strips.merged_df)




