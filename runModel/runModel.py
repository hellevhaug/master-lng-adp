from runModel.initModel import *


# Function for running basic model
def run_basic_model(group, filename, time_limit, description):
    print(f'\n You are now running file {filename}, in group {group} with basic model')
    model = initialize_basic_model(group, filename, False)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-basic.log')
    model.optimize()
    #model.write(f'{filename}_basic.lp')
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model

# Function for running model with variable production
def run_variable_production_model(group, filename, time_limit, description):
    print(f'\n You are now running file {filename}, in group {group} with variable production')
    model = initialize_variable_production_model(group, filename, False)
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
    print(f'\n You are now running file {filename}, in group {group} with charter out model')
    model = initialize_charter_out_model(group, filename, False)
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
    print(f'\n You are now running file {filename}, in group {group} with combined model')
    model = initialize_combined_model(group, filename, False)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-combined.log')
    model.optimize()
    #model.write(f'{filename}_charter.lp')
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model

# Function for running model with possibility to both vary production and charter out 
def run_basic_model_heuristic(group, filename, time_limit, description):
    print(f'\n You are now running file {filename}, in group {group}, with a contruction heuristic')
    model = initialize_basic_model(group, filename, True)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-basic-heuristic.log')
    model.optimize()
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model

# Function for running model with possibility to both vary production, heuristic
def run_variable_production_model_heuristic(group, filename, time_limit, description):
    print(f'\n You are now running file {filename}, in group {group}, with a construction heuristic')
    model = initialize_variable_production_model(group, filename, True)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-varprod-heuristic.log')
    model.optimize()
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model

# Function for running model with possibility to both vary production and charter out, heuristic
def run_charter_out_model_heuristic(group, filename, time_limit, description):
    print(f'\n You are now running file {filename}, in group {group}, with a heuristic')
    model = initialize_charter_out_model(group, filename, True)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-charterout-heuristic.log')
    model.optimize()
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model

# Function for running model with possibility to both vary production and charter out, heuristic
def run_combined_model_heuristic(group, filename, time_limit, description):
    print(f'\n You are now running file {filename}, in group {group}, with a heuristic')
    model = initialize_combined_model(group, filename, True)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}-combined-heuristic.log')
    model.optimize()
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model