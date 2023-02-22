from runModel.initModel import *


# Function for running basic model
def run_basic_model(group, filename, time_limit, description):
    model = initialize_basic_model(group, filename)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-basic.log')
     
    model.optimize()
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model

# Function for running model with variable production
def run_variable_production_model(group, filename, time_limit, description):
    model = initialize_variable_production_model(group, filename)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-varprod.log')
    model.optimize()
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
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model
