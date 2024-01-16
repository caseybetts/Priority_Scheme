# Author: Casey Betts, 2023
# This file holds the needed functions to receive a multisensor_active_orders_ufp .dbf file and output a cleaned .csv

import pandas as pd
import geopandas as gpd 

def get_user_info():
    """ Collects needed info from the user via the console """
    # Gather the file location
    file_location = input("Enter Folder Location: ")
    filename = input("Enter File Name: ")

    # Gather the data source so we know which column names to drop
    while True:
        source = input("Enter data source ('DRIFS' or 'PROD') or 'Q' to quit: ")
        if not source in ['DRIFS', 'PROD', 'Q', 'q']:
            print("Please input 'DRIF', 'PROD' or 'Q'")
        else: break

    return [file_location, filename, source]
    
def load_dbf_to_dataframe(file_location):
    """ Using the dbf file location of the multisensor_active_orders_ufp, 
    will return a pandas dataframe """

    if not file_location[-4:-3] == '.': 
        file_location += ".dbf"

    return pd.DataFrame(gpd.read_file(file_location))

def clean_df(df, source):
    """ Removes unnecessary fields given a dataframe (DRIF or PROD) """

    if source == 'DRIFS':
        columns_to_drop = [ 'SOLI', 'ORDER_NUMB', 'LINE_NUMBE', 'PROD_LEVEL',
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
        columns_to_rename = {"SAP_CUS": "Cust_Num", "TASK_PRIOR": 'Task_Pri',"DOLPERSQKM": "DollarPerSquare"}
    elif source == 'PROD':
        columns_to_drop = [ 'classifica','data_acces','demand_typ','standing_t','order_numb',
                            'line_numbe','order_iden','external_i','sap_custom','order_desc',
                            'area_remai','product_le','order_stat','active_tim','start_date',
                            'end_date','area','pricing','sap_con','tasking_pr','ssr_priori',
                            'backhaul_p','responsive','min_ona','max_ona','min_sun_az',
                            'max_sun_az','min_sun_el','max_sun_el','min_tar_az','max_tar_az',
                            'max_cloud_','purchase_o','purchase_1','country','stereoprod',
                            'vehicle','ge01','wv01','wv03','lg01','lg02','imagebands',
                            'percent_co','type','max_asymme','min_asymme','max_bisect',
                            'min_bisect','max_conver','min_conver','consider_f','consider_1',
                            'lg01_sched','lg02_sched','scan_direc','line_rate','tdi_flag','tdi_offset',]
        columns_to_rename = { 'sap_custom': 'Cust_Num', 'tasking_pr': 'Task_Pri', 'price_per_': 'DollarPerSquare' }
   
    df.drop(labels=columns_to_drop, axis=1, inplace=True)
    df.rename(columns=columns_to_rename, inplace=True)

    return df

def dataframe_to_csv(dataframe, filename):
    """ Given a dataframe this will save it to a csv file of the given name"""

    dataframe.to_csv( filename + '.csv')



if __name__ == "__main__":

    # Get the user info
    user_info = get_user_info()

    # Load in the .dbf to a pandas dataframe
    df = load_dbf_to_dataframe(user_info[0] + '\\' + user_info[1])

    # Clean the dataframe 
    cleaned_df = clean_df(df, user_info[2])
    
    # Save dataframe to a .csv file
    dataframe_to_csv(cleaned_df, user_info[1])




