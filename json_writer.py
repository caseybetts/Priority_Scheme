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

    "initial priorities" : [    710,  
                                752,  
                                755,  
                                757,  
                                768, 
                                768,  
                                768,  
                                769,  
                                791,  
                                780,
                                790,  
                                799],

    "test case priorities" : [  730,  
                                752,  
                                755,  
                                757,  
                                768, 
                                768,  
                                768,  
                                769,  
                                791,  
                                765,
                                757,  
                                781],
    
    "priority bounds" : [(700, 720),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (780, 800),
                         (790, 800),
                         (799, 800)],

    "number of weather scenarios" : 10,
    "dollar bin breakpoints" : [20, 15, 12, 10, 8, 6, 4, 3, 2, 1, 0],
    "optimization method" : 'Nelder-Mead',
    "optimization tolerance" : .01,
    "predicted cloud cover uncertainty" : .1

}

json_object = json.dumps(data, indent=4)

with open('run_input_parameters.json', 'w') as outfile:
    outfile.write(json_object)


