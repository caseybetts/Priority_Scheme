# This file will create a .json file out of the given python dict

import json


data = {
    "orders_csv" : "active_orders.csv",
    "clouds_csv" : "cloudcover.csv",
    "zero_dollar_cust_dpsqkm" : {   82: 1, 
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
                                    100069: 4},

    "initial_priorities" : [    7.305e-03,  
                                7.527e-03,  
                                7.431e-03,  
                                7.570e-03,  
                                7.688e-03, 
                                7.488e-03,  
                                7.683e-03,  
                                7.699e-03,  
                                7.914e-03,  
                                7.650e-03,
                                7.576e-03,  
                                7.815e-03],

    "test_case" : [ 7.305e-03,  
                    7.527e-03,  
                    7.55e-03,  
                    7.570e-03,  
                    7.688e-03, 
                    7.688e-03,  
                    7.683e-03,  
                    7.699e-03,  
                    7.914e-03,  
                    7.650e-03,
                    7.576e-03,  
                    7.815e-03],
    
    "priority_upper_bound" : 800,
    "priority_lower_bound" : 700

}

json_object = json.dumps(data, indent=4)

with open('run_input_parameters.json', 'w') as outfile:
    outfile.write(json_object)


