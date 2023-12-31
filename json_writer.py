# This file will create a .json file out of the given python dict

""" Note:   A predicted cloud cover uncertainty (standard deviation) of .30 will produce the following distribution 
            of the difference bewteen the predicted cc and the actual cc.
    
            Actual vs Predicted difference with .30 standard deviation:
            < .20 (Good):       58%	
            < .40 (Fair):       74%	
            < .60 (Bad):        85%	
            < .80 (Terrible):   92% 
"""


import json


data = {
    "orders_csv" : "active_orders.csv",
    "clouds_folder" : "PWOT_CSV",
    "zero_dollar_cust_dpsqkm" : {   82: 1, 
                                    306: 2,
                                    326: 2, 
                                    331: 10, 
                                    361: 5, 
                                    366: 4,
                                    381: 3,
                                    10250: 15, 
                                    12620: 14, 
                                    12711: 14, 
                                    20583: 20,
                                    35915: 11, 
                                    44924: 7,
                                    58480: 13,
                                    60569: 10,
                                    60603: 9, 
                                    100069: 8},
    
    "MCP_dollar_values": {
        698: 3,
        708: 2.75,
        718: 2.25,
        738: 1.75,
        748: 1.25,
        758: 1,
        768: .75,
        778: .5,
        788: .3
    },

    "initial priorities" : [    750,
                                750,
                                750,
                                750,
                                750,
                                750,
                                750,
                                750,
                                750,
                                750,
                                750,
                                750],

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
    
    "priority bounds" : [(700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800),
                         (700, 800)],

    "number of weather scenarios" : 5,
    "dollar bin breakpoints" : [20, 15, 12, 10, 7, 5, 3, 2, 1, .5, 0],
    "optimization method" : 'Nelder-Mead',
    "optimization tolerance" : .01,
    "predicted cloud cover uncertainty" : .3            # See note above

}

json_object = json.dumps(data, indent=4)

with open('run_input_parameters.json', 'w') as outfile:
    outfile.write(json_object)


