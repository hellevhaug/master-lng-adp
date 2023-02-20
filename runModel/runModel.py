from runModel.initModel import *


def run_model(group, filename, time_limit, description):
    model = initialize_model(group, filename)
    print(description)
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}.log')
    model.optimize()
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model
