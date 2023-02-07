from runModel.initModel import *

def run_model(group, filename, time_limit):
    model = initialize_model(group, filename)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'solution/{group}/{filename}.log')
    model.optimize()
    vars = model.getVars

    # Will figure out something smart here
    return vars
    
