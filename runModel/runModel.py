from runModel.initModel import *
from runModel.initModelRHH import *
from supportFiles.getVars import *
from supportFiles.plotTimeSpace import *

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

def run_basic_model_RHH(group, filename, time_limit, description, horizon_length, prediction_horizon):
    
    frozen_variables = {key: [] for key in ['x','s','g','z','q','y']}
    iteration_count = 0
    loading_days_length = 1000 # This is only an initialisation of length of loading days

    while horizon_length * iteration_count <= loading_days_length: # retrieve this
        model, loading_days_length = initialize_basic_model_RHH(group, filename, horizon_length, prediction_horizon, frozen_variables, iteration_count)
    # ^^HERE WE CAN EXPLICITLY EXPORT ALL THE NON-CHANGING PARAMETERS AND RUN ONLY THE OPTIMIZATION ALGORITHM IN A LOOP
        print("------------------------------------------------------")
        print(description) 
        print("Horizon interval: period", horizon_length*iteration_count, "-", horizon_length*(iteration_count+1)-1)
        print("Number of freezed variables: x:", len(frozen_variables['x']), "s:", len(frozen_variables['s']), "g:", len(frozen_variables['g']), "z:", len(frozen_variables['z']), "q:", len(frozen_variables['q']), "y:", len(frozen_variables['y']))
        print("------------------------------------------------------")
        model.setParam('TimeLimit', time_limit)
        model.setParam('LogFile', f'logFiles/{group}/{filename}-basic.log')
        model.optimize()

        #plot_time_space(model, loading_days_length)

        optimization_status = model.Status
        print("Optimization status:", optimization_status)

        if model.Status == GRB.Status.TIME_LIMIT:
            best_bound = model.ObjBound
            print("Best bound after time limit: ", best_bound)
        elif model.Status == GRB.Status.OPTIMAL:
            best_bound = model.ObjVal
            print("Optimal solution found: ", best_bound)
        elif model.Status == GRB.Status.INFEASIBLE:
            print("Model is infeasible.")
        elif model.Status == GRB.Status.UNBOUNDED:
            print("Model is unbounded.")
        else:
            print("Optimization status:", model.Status)
            print("Unexpected status. Check the Gurobi documentation for more information.")

        if model.Status == GRB.Status.TIME_LIMIT and horizon_length*(iteration_count+1) <= loading_days_length:
            if model.SolCount > 0:
                print("Time limit reached, but a feasible solution was found.")
                
                # Freeze the variables that start in the current horizon: 
                for var in model.getVars():
                    # x format: "x[AD-7,DESCON_1,28,ART_START,63]": 1.0, ...
                    if var.X != 0:
                        if var.varName[0]=='x':
                            varName_str = var.varName
                            varName_list = varName_str.split('[')[1].split(']')[0].split(',')
                            # now looks like this: ['AD-7', 'DESCON_1', '28', 'ART_START', '63']
                            if horizon_length*iteration_count <= int(varName_list[2]) < horizon_length*(iteration_count+1):
                                frozen_variables['x'].append(var)
                    # s format: {"s[FU,1]": 90000.0,
                        if var.varName[0]=='s':
                            varName_str = var.varName
                            varName_list = varName_str.split('[')[1].split(']')[0].split(',')
                            # now looks like this: [FU,1]
                            if horizon_length*iteration_count <= int(varName_list[1]) < horizon_length*(iteration_count+1):
                                frozen_variables['s'].append(var)
                    # g format: {"g[FU,56,DESCON_1]": 142289.22952803085,
                        if var.varName[0]=='g':
                            varName_str = var.varName
                            varName_list = varName_str.split('[')[1].split(']')[0].split(',')
                            # now looks like this: [FU,56,DESCON_1]
                            if horizon_length*iteration_count <= int(varName_list[1]) < horizon_length*(iteration_count+1):
                                frozen_variables['g'].append(var)
                    # z format: {"z[1001,6]": 1.0,
                        if var.varName[0]=='z':
                            varName_str = var.varName
                            varName_list = varName_str.split('[')[1].split(']')[0].split(',')
                            # now looks like this: [1001,6]
                            if horizon_length*iteration_count <= int(varName_list[1]) < horizon_length*(iteration_count+1):
                                frozen_variables['z'].append(var)
    
            else:
                print("Time limit reached, and no feasible solution found.")
        
        iteration_count += 1

        print("loading days length: ", loading_days_length)
    
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
