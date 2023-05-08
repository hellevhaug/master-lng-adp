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

def run_basic_model_RHH(gap_limit, group, filename, time_limit, description, horizon_length, prediction_horizon):
    
    #frozen_variables = {key: [] for key in ['x','s','g','z','q','y']}
    frozen_variables = []
    frozen_variables_values = []
    iteration_count = 0
    last_inventory = {}

    total_feasible_arcs,fob_ids,fob_days,loading_port_ids,\
    loading_days,des_contract_ids,spot_port_ids,production_quantities,\
    fob_revenues,fob_demands,des_contract_revenues,\
    vessel_capacities,vessel_boil_off_rate,vessel_ids,all_days,\
    sailing_time_charter,unloading_days,charter_boil_off,\
    tank_leftover_value,vessel_available_days,sailing_costs,\
    charter_total_cost,des_spot_ids,initial_inventory,max_inventory,\
    min_inventory,maintenance_vessel_ports,maintenance_vessels,port_ids,\
    vessel_start_ports,partition_days,upper_partition_demand,\
    des_contract_partitions,lower_partition_demand,days_between_delivery,\
    fob_contract_ids,fob_spot_ids,fob_spot_art_ports,operational_times,\
    fob_operational_times,number_of_berths,charter_vessel_upper_capacity,\
    charter_vessel_lower_capacity, loading_to_time = read_global_data_RHH(group, filename)
    
    model = gp.Model()

    model, x, z, w, g, s = init_model_vars_RHH(model, prediction_horizon, horizon_length, fob_ids, fob_days, total_feasible_arcs, loading_days, iteration_count, des_contract_ids, des_spot_ids, loading_port_ids, production_quantities)
    
    model = relax_horizon(model, prediction_horizon, horizon_length, iteration_count)

    model = init_objective_and_constraints(model, x, z, w, g, s, horizon_length, prediction_horizon, \
        iteration_count, last_inventory, fob_ids,fob_days,loading_port_ids,\
        loading_days,des_contract_ids,spot_port_ids,production_quantities,\
        fob_revenues,fob_demands,des_contract_revenues,\
        vessel_capacities,vessel_boil_off_rate,vessel_ids,all_days,\
        sailing_time_charter,unloading_days,charter_boil_off,\
        tank_leftover_value,vessel_available_days,sailing_costs,\
        charter_total_cost,des_spot_ids,initial_inventory,max_inventory,\
        min_inventory,maintenance_vessel_ports,maintenance_vessels,port_ids,\
        vessel_start_ports,partition_days,upper_partition_demand,\
        des_contract_partitions,lower_partition_demand,days_between_delivery,\
        fob_contract_ids,fob_spot_ids,fob_spot_art_ports,operational_times,\
        fob_operational_times,number_of_berths,charter_vessel_upper_capacity,\
        charter_vessel_lower_capacity)

    while horizon_length * iteration_count <= len(loading_days): 

        print("Constraints in total: ", len(model.getConstrs()))
        #print("model objective: ", model.getObjective())
        print("x variables in x: ", len(x))
        print("tot variables in model: ", len(model.getVars()))
        frozen = []
        binary = []
        continuous = []
        for var in x.values():
            if var.ub == var.lb: 
                frozen.append(var)
            else: 
                if var.vtype == GRB.BINARY:
                    binary.append(var)
                elif var.vtype == GRB.CONTINUOUS:
                    continuous.append(var)
        print("- Froxen x variables: ", len(frozen))
        print("- Binary x variables: ", len(binary))
        print("- Continuous x variables: ", len(continuous))
        print("z variables: ", len(z))
        print("w variables: ", len(w))
        print("g variables: ", len(g))
        print("s variables: ", len(s))  
        
        print("----------------------------------------------------------------")
        print(description) 
        print("Horizon interval: period", horizon_length*iteration_count+1, "-", horizon_length*(iteration_count+1))
        #print("Number of freezed variables: ", len(frozen_variables))
        print("Tot. loading days length: ", len(loading_days))
        print("Days frozen: ", horizon_length*iteration_count)
        print("----------------------------------------------------------------")
        model.setParam('TimeLimit', time_limit)
        model.setParam('MIPGap', gap_limit)
        model.setParam('LogFile', f'logFiles/{group}/{filename}-basic.log')
        model.optimize()

        #plot_time_space(model, loading_days_length)

        optimization_status = model.Status
        print("Optimization status:", optimization_status)

        if model.Status == GRB.Status.TIME_LIMIT:
            best_bound = model.ObjBound
            print("----------------------------Best bound after time limit: ", best_bound)
        elif model.Status == GRB.Status.OPTIMAL:
            best_bound = model.ObjVal
            print("----------------------------Optimal solution found: ", best_bound)
        elif model.Status == GRB.Status.INFEASIBLE:
            print("----------------------------Model is infeasible.")
            break
        elif model.Status == GRB.Status.UNBOUNDED:
            print("----------------------------Model is unbounded.")
            break
        elif model.Status == GRB.Status.INF_OR_UNBD:
            print("----------------------------Model is infeasible or unbounded.")
            break
        else:
            print("----------------------------Optimization status:", model.Status)
            print("----------------------------Unexpected status. Check the Gurobi documentation for more information.")
            break
        
        if horizon_length*(iteration_count+1) <= len(loading_days):
            model, x, z, w, g, s = freeze_variables_and_change(model, x, z, w, g, s, horizon_length, iteration_count)
            model.update()
        '''
        constraints = model.getConstrs()
        # Remove each constraint from the model
        for constraint in constraints:
            model.remove(constraint)
        '''
        iteration_count += 1

        
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
