# Author: Casey Betts, 2023
# This file holds the needed functions to receive a multisensor_active_orders_ufp .dbf file and output a cleaned .csv

import pandas as pd
import geopandas as gpd 

msof_file_location = "Rev11413\multisensor_active_orders_ufp_rev11413.shx"
    
def load_dbf_to_dataframe():
    """ Using the dbf file location of the multisensor_active_orders_ufp, 
    will return a pandas dataframe """

    return pd.DataFrame(gpd.read_file(msof_file_location))

def clean_msof_df(msof_dataframe):
    """ Given a multisensor_active_orders_ufp dataframe, this will remove unnecessary fields"""

    columns_to_drop = ['SOLI', 'ORDER_NUMB', 'LINE_NUMBE', 'PROD_LEVEL',
       'START_DATE', 'END_DATE', 'SUBMITTED', 'CHANGE_DAT', 'ACTIVEDATE','SAP_CON', 
       'DESCRIPTI', 'PURCHASE_O', 'SAP_LIC', 'V_MARKET',
       'SALES_ORG', 'RESP_LEVEL', 'WV01', 'WV02', 'WV03',       
       'WV03_VNIR', 'WV03_SWIR', 'WV03_CAVIS', 'GE01', 'QB02', 'BCKHL_PRIO',  
       'WV1_TIER', 'WV2_TIER', 'WV3_V_TIER', 'WV3_S_TIER', 'WV3_C_TIER',      
       'GE1_TIER', 'QB2_TIER', 'SSR_PRIORI', 'PP_PRIORIT',
       'MIN_SUN_EL', 'MAX_SUN_EL', 'MIN_SUN_AZ', 'MAX_SUN_AZ', 'MIN_TAR_AZ',  
       'MAX_TAR_AZ', 'MIN_TAR_EL', 'MAX_TAR_EL', 'AREA', 'TIMELINE',
       'BONUSING', 'AGGREGATN', 'PERIODICIT', 'CALIB_TYPE', 'ACC_CONTRL',     
       'MAX_REQGSD', 'COUNTRY', 'COLLPERFDT', 'COLLPERFRS', 'AREATOGO',       
       'PERC_COMP', 'TOTALDOL', 'DOLTOGO', 'INC_TYPE',
       'INC_VALUE', 'ORDERSTAT', 'STEREOTYPE', 'MIN_CONV', 'MAX_CONV',        
       'MIN_ASYM', 'MAX_ASYM', 'MIN_BISECT', 'MAX_BISECT', 'WV01_BAND',       
       'WV1TDIPAN', 'WV1TDIOPN', 'WV02_BAND', 'WV2TDIPAN', 'WV2TDIOPN',       
       'WV2TDIM12', 'WV2TDIOM12', 'WV2TDIM34', 'WV2TDIOM34', 'WV2TDIM56',     
       'WV2TDIOM56', 'WV2TDIM78', 'WV2TDIOM78', 'WV03_BAND', 'WV3TDIPAN',     
       'WV3TDIOPN', 'WV3TDIM12', 'WV3TDIOM12', 'WV3TDIM34', 'WV3TDIOM34',     
       'WV3TDIM56', 'WV3TDIOM56', 'WV3TDIM78', 'WV3TDIOM78', 'WV3EXPSWA',    
       'WV3EXPOSWA', 'WV3EXPSWB', 'WV3EXPOSWB', 'WV3EXPCVS', 'WV3EXPOCVS',
       'GE1TDIM1_3', 'GE1TDIOM13', 'GE1TDIM2_4', 'GE1TDIOM24', 'QB02_BAND',
       'QB2TDIPM1', 'QB2TDIOPM1', 'GE01_BAND', 'GE1TDIPAN', 'GE1TDIOPN',
       'Test_Pri', 'geometry']
   
    msof_dataframe.drop(labels=columns_to_drop, axis=1, inplace=True)

    msof_dataframe.rename(columns={"SAP_CUS": "Cust_Num", "TASK_PRIOR": 'Task_Pri',"DOLPERSQKM": "DollarPerSquare"}, inplace=True)

    return msof_dataframe

def dataframe_to_csv(dataframe):
    """ Given a dataframe this will save it to a csv file of the given name"""

    dataframe.to_csv('active_orders.csv')



if __name__ == "__main__":

    # Load in the .dbf to a pandas dataframe
    msof_df = load_dbf_to_dataframe()

    # Clean the dataframe 
    cleaned_df = clean_msof_df(msof_df)
    
    # Save dataframe to a .csv file
    dataframe_to_csv(cleaned_df)




