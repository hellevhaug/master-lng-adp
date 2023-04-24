from runModel.initModel import *
from runModel.initModelRHH import *
from supportFiles.getVars import *


# Function for running basic model
def run_basic_model(group, filename, time_limit, description):
    model = initialize_basic_model(group, filename)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-basic.log')
    model.optimize()
    #model.write(f'{filename}_basic.lp')
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model

def run_basic_model_RHH(group, filename, time_limit, description, horizon_length, prediction_horizon, frozen_variables):
    
    frozen_variables = {key: [] for key in ['x','s','g','z','q','y']}
    iteration_count = 0
    total_horizon = horizon_length * 2 # This is only an initialisation of length of loading days

    while horizon_length * iteration_count <= total_horizon: # retrieve this
        model, total_horizon = initialize_basic_model_RHH(group, filename, horizon_length, prediction_horizon, frozen_variables, iteration_count)
    # ^^HERE WE CAN EXPLICITLY EXPORT ALL THE NON-CHANGING PARAMETERS AND RUN ONLY THE OPTIMIZATION ALGORITHM IN A LOOP
        print(description, "Horizon interval: period", horizon_length*iteration_count, "-", horizon_length*(iteration_count+1)-1)
        model.setParam('TimeLimit', time_limit)
        model.setParam('LogFile', f'logFiles/{group}/{filename}-basic.log')
        model.optimize()

        # Freeze the variables that start in the current horizon: 
        
        for var in model.getVars():
            # x format: "x[AD-7,DESCON_1,28,ART_START,63]": 1.0, ...
            if var.x != 0:
                if var.varName[0]=='x':
                    varName_list = var.varName
                    varName_list.split('[')
                    varName_list.split(',')
                    # now looks like this: ['x', 'AD-7', 'DESCON_1', '28', 'ART_START', '63']
                    if varName_list.varName[3] <= horizon_length*(iteration_count+1)-1:
                        frozen_variables['x'].append(var)
            # s format: {"s[FU,1]": 90000.0,
                if var.varName[0]=='s':
                    varName_list = var.varName
                    varName_list.split('[')
                    varName_list.split(',')
                    # now looks like this: [s,FU,1]
                    if varName_list.varName[2] <= horizon_length*(iteration_count+1):
                        frozen_variables['s'].append(var)
            # g format: {"g[FU,56,DESCON_1]": 142289.22952803085,
                if var.varName[0]=='g':
                    varName_list = var.varName
                    varName_list.split('[')
                    varName_list.split(',')
                    # now looks like this: [g,FU,56,DESCON_1]
                    if varName_list.varName[2] <= horizon_length*(iteration_count+1):
                        frozen_variables['g'].append(var)
            # z format: {"z[1001,6]": 1.0,
                if var.varName[0]=='z':
                    varName_list = var.varName
                    varName_list.split('[')
                    varName_list.split(',')
                    # now looks like this: [z,1001,6]
                    if varName_list.varName[2] <= horizon_length*(iteration_count+1):
                        frozen_variables['z'].append(var)
        
        iteration_count += 1
    
    #model.write(f'{filename}_basic.lp')

    return model

# Function for running model with variable production
def run_variable_production_model(group, filename, time_limit, description):
    model = initialize_variable_production_model(group, filename)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-varprod.log')
    model.optimize()
    #model.write(f'{filename}_varprod.lp')
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model


# Function for running model with possibility to charter out 
def run_charter_out_model(group, filename, time_limit, description):
    model = initialize_charter_out_model(group, filename)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-charterout.log')
    model.optimize()
    #model.write(f'{filename}_charter.lp')
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model

# Function for running model with possibility to both vary production and charter out 
def run_combined_model(group, filename, time_limit, description):
    model = initialize_combined_model(group, filename)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-combined.log')
    model.optimize()
    #model.write(f'{filename}_charter.lp')
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model
