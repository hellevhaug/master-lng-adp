from runModel.initModel import *
from runModel.initModelRHH import *
from supportFiles.getVars import *
from supportFiles.plotTimeSpace import *
from runModel.constructionHeuristic import *
import datetime

# Function for running basic model
def run_basic_model(group, filename, time_limit, description):
    model = initialize_basic_model(group, filename)
    print(description)
    now = datetime.datetime.now()
    date = now.strftime("%m-%d-%Y, %H-%M")
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}/basic-{date}.log')
    model.optimize()
    #model.write(f'{filename}_basic.lp')
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model

def run_basic_model_RHH(gap_limit, group, filename, time_limit, description, horizon_length, prediction_horizon, overlap):
    
    #frozen_variables = {key: [] for key in ['x','s','g','z','q','y']}
    iteration_count = 0
    construction = CONSTRUCTION

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
    charter_vessel_lower_capacity, loading_to_time, des_loading_ports, fob_loading_ports,\
    maintenance_start_times = read_global_data_RHH(group, filename)
    
    model = gp.Model()

    start_time_total = time.time()
    print("\nTOTAL TIME START: %.1f seconds ---" % (time.time() - start_time_total))

    model, x, z, w, g, s = init_model_vars_RHH(model, prediction_horizon, horizon_length, fob_ids, fob_days, 
                                               total_feasible_arcs, loading_days, iteration_count, des_contract_ids, 
                                               des_spot_ids, loading_port_ids, production_quantities, 
                                               des_loading_ports, sailing_time_charter, unloading_days)
    
    model = relax_horizon(model, prediction_horizon, overlap, horizon_length, iteration_count)

    print("Number of x-variables before removal: ", len(x))

    if prediction_horizon != "ALL": 
        model, x, z, w, g, s = remove_variables_after_pred_hor(model, prediction_horizon, horizon_length, iteration_count, x, z, w, g, s, all_days, loading_days)
    
    print("Number of x-variables after removal: ", len(x))

    model = init_objective_and_constraints(model, x, z, w, g, s, horizon_length, prediction_horizon, \
        iteration_count, fob_ids,fob_days,loading_port_ids,\
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
        charter_vessel_lower_capacity, fob_loading_ports)
    

    # ------------- CONSTRUCTION HEURISTIC --------------- #
    stop_time_construction = prediction_horizon + horizon_length
    overlap_construction = overlap

    if construction:
        print("\n--- Starting heuristic construction with random FOB ----\n")

        x1 = find_initial_arcs(x, maintenance_vessels, all_days, maintenance_vessel_ports, vessel_start_ports, maintenance_start_times,
                                vessel_available_days, sailing_costs)

        z1, s1, w1, g1, demand_satisfied = find_initial_solution_random(z, s, w, g, all_days, des_contract_ids, lower_partition_demand, upper_partition_demand,
        des_contract_partitions, partition_days, fob_ids, fob_contract_ids, fob_demands, fob_days, min_inventory, max_inventory, initial_inventory, 
        production_quantities, MINIMUM_DAYS_BETWEEN_DELIVERY, des_loading_ports, number_of_berths, sailing_time_charter, loading_days,
        fob_loading_ports, stop_time_construction, fob_spot_art_ports, unloading_days, loading_port_ids, des_spot_ids, overlap_construction)

        if not demand_satisfied: 

            config = 'tryFob'

            print("\n--- Trying heuristic construction with prioritixing FOB ----\n")

            z1, s1, w1, g1, demand_satisfied = find_initial_solution(z, s, w, g, all_days, des_contract_ids, lower_partition_demand, upper_partition_demand,
            des_contract_partitions, partition_days, fob_ids, fob_contract_ids, fob_demands, fob_days, min_inventory, max_inventory, initial_inventory, 
            production_quantities, MINIMUM_DAYS_BETWEEN_DELIVERY, des_loading_ports, number_of_berths, sailing_time_charter, loading_days,
            fob_loading_ports, stop_time_construction, fob_spot_art_ports, unloading_days, loading_port_ids, des_spot_ids, config, overlap_construction)

        if not demand_satisfied:

            print("\n--- Trying heuristic construction with prioritixing DES ----\n")
            
            config = 'tryDes'
            
            z1, s1, w1, g1, demand_satisfied = find_initial_solution(z, s, w, g, all_days, des_contract_ids, lower_partition_demand, upper_partition_demand,
            des_contract_partitions, partition_days, fob_ids, fob_contract_ids, fob_demands, fob_days, min_inventory, max_inventory, initial_inventory, 
            production_quantities, MINIMUM_DAYS_BETWEEN_DELIVERY, des_loading_ports, number_of_berths, sailing_time_charter, loading_days,
            fob_loading_ports, stop_time_construction, fob_spot_art_ports, unloading_days, loading_port_ids, des_spot_ids, config, overlap_construction)

        if not demand_satisfied:
            
            print("\n--- Trying heuristic construction with prioritixing FOB and squaring score ----\n")

            config = 'trySquared'

            z1, s1, w1, g1, demand_satisfied = find_initial_solution(z, s, w, g, all_days, des_contract_ids, lower_partition_demand, upper_partition_demand,
            des_contract_partitions, partition_days, fob_ids, fob_contract_ids, fob_demands, fob_days, min_inventory, max_inventory, initial_inventory, 
            production_quantities, MINIMUM_DAYS_BETWEEN_DELIVERY, des_loading_ports, number_of_berths, sailing_time_charter, loading_days,
            fob_loading_ports, stop_time_construction, fob_spot_art_ports, unloading_days, loading_port_ids, des_spot_ids, config, overlap_construction)

            # If the model finds a feasible solution
        if demand_satisfied:

            for (v,i,t,j,t_) in x.keys():
                x[v,i,t,j,t_].Start = x1[v,i,t,j,t_]
            
            for (i,t,j) in g.keys():
                g[i,t,j].Start = g1[i,t,j]
                w[i,t,j].Start = w1[i,t,j]
            
            for (f,t) in z.keys():
                z[f,t].Start = z1[f,t]

            for (i,t) in s.keys():
                s[i,t].Start = s1[i,t]
                s[i,t].Start = s1[i,t]
        
            print("\n--- Finished heuristic construction----\n")

        else:
            for (v,i,t,j,t_) in x.keys():
                x[v,i,t,j,t_].VarHintVal = x1[v,i,t,j,t_]
            
            for (i,t,j) in g.keys():
                g[i,t,j].VarHintVal = g1[i,t,j]
                w[i,t,j].VarHintVal = w1[i,t,j]
            
            for (f,t) in z.keys():
                z[f,t].VarHintVal = z1[f,t]

            for (i,t) in s.keys():
                s[i,t].VarHintVal = s1[i,t]

            print("\n--- Did not find a feasible solution for this problem----\n")

        model.update()
    
    horizon_ext = 0
    last_it = False
    now = datetime.datetime.now()
    date = now.strftime("%m-%d-%Y, %H-%M")
    config = f'H{horizon_length}-P{prediction_horizon}-O{overlap}'

    while horizon_length * (iteration_count) + horizon_ext <= len(loading_days): 
        print('horizon_length * (iteration_count) + horizon_ext: ', horizon_length * (iteration_count) + horizon_ext)
        
        if (horizon_length*(iteration_count+2)+prediction_horizon) >= len(loading_days)-(prediction_horizon/2) and (horizon_length*(iteration_count+2)+prediction_horizon) < len(loading_days):
            horizon_ext = len(loading_days)-(horizon_length*(iteration_count+2)) +1
            horizon_ext_ext = len(all_days)-(horizon_length*(iteration_count+2)) +1
    # printing and optimizing:
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
                    #print(var)
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
        print("Tot. all days length: ", len(all_days))
        print("Days frozen: ", horizon_length*iteration_count)
        print("Iteration count: ", iteration_count)
        print("Horizon extension: ", horizon_ext)
        print("----------------------------------------------------------------")
        model.setParam('TimeLimit', time_limit)
        model.setParam('MIPGap', gap_limit)
        model.setParam('FeasibilityTol', 1e-2)
        model.setParam('LogFile', f'logFiles/{group}/{filename}/basic-{date}-{config}.log')
        model.optimize()
        if last_it == True:
            iteration_count += 1
            break

        #plot_time_space(model, loading_days_length)

        optimization_status = model.Status
        print("Optimization status:", optimization_status)

        if model.Status == GRB.Status.TIME_LIMIT:
            best_bound = model.ObjBound
            print("----------------------------Best bound after time limit: ", best_bound)
        elif model.Status == GRB.Status.TIME_LIMIT and  best_bound :
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

        if horizon_length*(iteration_count+1) + horizon_ext <= len(all_days): #Can probably be omitted

            start_inventory_constraint_time = horizon_length*(iteration_count+1)-1 if horizon_length*(iteration_count+1) <= len(loading_days) else len(loading_days) #XX
            stop_time = horizon_length*(iteration_count+2)+prediction_horizon+horizon_ext if horizon_length*(iteration_count+2)+prediction_horizon+horizon_ext <= len(loading_days) else len(all_days)+1
            leftover_stop_time = horizon_length*(iteration_count+2)+prediction_horizon if horizon_length*(iteration_count+2)+prediction_horizon <= len(loading_days) else len(loading_days)
            #all_days_stop_time = horizon_length*(iteration_count+2)+prediction_horizon + (len(all_days)-len(loading_days)) if horizon_length*(iteration_count+2)+prediction_horizon + (len(all_days)-len(loading_days)) <= len(all_days) else len(all_days)
            print('stop_time: ', stop_time)
            print("horizon extension: ", horizon_ext)
            #print('all_days_stop_time: ', all_days_stop_time)
            print('start_inventory_constraint_time: ', start_inventory_constraint_time)

            model, x, z, w, g, s = freeze_variables(model, x, z, w, g, s, horizon_length, iteration_count, prediction_horizon, all_days, horizon_ext, overlap)
            # deleting forecast horizon variables: 
            x_vars_to_remove = []
            z_vars_to_remove = []
            w_vars_to_remove = []
            g_vars_to_remove = []
            s_vars_to_remove = []
            if prediction_horizon != "ALL": 
                for var in model.getVars():
                    var_name = var.varName
                    if var_name[0] == 'x':
                        varName_list = var_name.split('[')[1].split(']')[0].split(',')
                        key_parts = var_name[2:-1].split(',')
                        tuple_key = (key_parts[0], key_parts[1], int(key_parts[2]), key_parts[3], int(key_parts[4]))
                        if horizon_length*(iteration_count+1) < int(varName_list[2]):
                            x_vars_to_remove.append(tuple_key)
                    elif var_name[0] == 'z':
                        varName_list = var_name.split('[')[1].split(']')[0].split(',')
                        key_parts = var_name[2:-1].split(',')
                        tuple_key = (key_parts[0], int(key_parts[1]))
                        # now looks like this: [1001,6]
                        if horizon_length*(iteration_count+1) < int(varName_list[1]):
                            z_vars_to_remove.append(tuple_key)
                    elif var_name[0] == 'w':
                        varName_list = var_name.split('[')[1].split(']')[0].split(',')
                        key_parts = var_name[2:-1].split(',')
                        tuple_key = (key_parts[0], int(key_parts[1]), key_parts[2])
                        # now looks like this: [1001,6]
                        if horizon_length*(iteration_count+1) < int(varName_list[1]):
                            w_vars_to_remove.append(tuple_key)
                    elif var_name[0] == 'g':
                        varName_list = var_name.split('[')[1].split(']')[0].split(',')
                        key_parts = var_name[2:-1].split(',')
                        tuple_key = (key_parts[0], int(key_parts[1]), key_parts[2])
                        # now looks like this: [1001,6]
                        if horizon_length*(iteration_count+1) < int(varName_list[1]):
                            g_vars_to_remove.append(tuple_key)
                    elif var_name[0] == 's':
                        varName_list = var_name.split('[')[1].split(']')[0].split(',')
                        key_parts = var_name[2:-1].split(',')
                        tuple_key = (key_parts[0], int(key_parts[1]))
                        # now looks like this: [1001,6]
                        if horizon_length*(iteration_count+1) < int(varName_list[1]):
                            s_vars_to_remove.append(tuple_key)

                model.update()
                
                for tuple_key in list(set(x_vars_to_remove)):
                    model.remove(x[tuple_key])
                    del x[tuple_key]

                for tuple_key in list(set(z_vars_to_remove)):
                    model.remove(z[tuple_key])
                    del z[tuple_key]

                for tuple_key in list(set(w_vars_to_remove)):
                    model.remove(w[tuple_key])
                    del w[tuple_key]

                for tuple_key in list(set(g_vars_to_remove)):
                    model.remove(g[tuple_key])
                    del g[tuple_key]

                for tuple_key in list(set(s_vars_to_remove)):
                    model.remove(s[tuple_key])
                    del s[tuple_key]

                model.update()
            
                # Adding new bin variables for next iteration main horizon: 

                model, x, z, w, g, s = add_variables_for_next_main_horizon(model, x, z, w, g, s, prediction_horizon, horizon_length, total_feasible_arcs, 
                                              iteration_count, fob_ids, fob_days, des_contract_ids, des_spot_ids, loading_port_ids, 
                                              loading_days, production_quantities, horizon_ext, sailing_time_charter, unloading_days, des_loading_ports, overlap)
                
                if (horizon_length*(iteration_count+2)+prediction_horizon) >= len(loading_days)-(prediction_horizon) and (horizon_length*(iteration_count+2)+prediction_horizon) < len(loading_days):
                    horizon_ext = len(loading_days)-(horizon_length*(iteration_count+2)+prediction_horizon)+1
                    inventory_horizon_ext = len(all_days)-(horizon_length*(iteration_count+2)+prediction_horizon)+1
                else:
                    horizon_ext = 0
                
                if horizon_length*(iteration_count+2) + horizon_ext <= len(loading_days):

                    model, x, z, w, g, s = add_variables_for_next_prediction_horizon(model, x, z, w, g, s, prediction_horizon, horizon_length, total_feasible_arcs, 
                                                iteration_count, fob_ids, fob_days, des_contract_ids, des_spot_ids, loading_port_ids, 
                                                loading_days, production_quantities, horizon_ext, sailing_time_charter, unloading_days, des_loading_ports, overlap)

                start_time = time.time()
                print("\n--- Starting to remove constraints and add new for next horizon: %.1f seconds ---" % (time.time() - start_time))
                
                all_constraints = model.getConstrs()
                '''
                for constr in all_constraints:
                    if constr.ConstrName.startswith('inventory_control'):
                        model.remove(constr)
                    elif constr.ConstrName.startswith('flow'):
                        model.remove(constr)
                    elif constr.ConstrName.startswith('upper_demand'):
                        model.remove(constr)
                    elif constr.ConstrName.startswith('lower_demand'):
                        model.remove(constr)
                    elif constr.ConstrName.startswith('fob_max_contracts'):
                        model.remove(constr)
                model.update()
                '''

                for constr in all_constraints:
                    model.remove(constr)

                # 5.3
                print("iteration_count: ", iteration_count)
                print("IIIIIIIIIIIIIIIIIIIIIIII: start_inventory_constraint_time+1: ", start_inventory_constraint_time)
                print("IIIIIIIIIIIIIIIIIIIIIIII: stop_time+horizon_ext: ", stop_time+horizon_ext)
                print("IIIIIIIIIIIIIIIIIIIIIIII: stop_time: ", stop_time)

                model.addConstrs(init_loading_inventory_constr(start_inventory_constraint_time, stop_time+horizon_ext, s, g, z, x, production_quantities, vessel_capacities, vessel_ids,
                des_contract_ids, all_days,fob_demands, fob_ids, loading_port_ids, loading_days, fob_loading_ports, 
                des_spot_ids, horizon_length, iteration_count), name='inventory_control')

                # Constraint 5.4
                model.addConstrs(init_upper_inventory_constr(s, max_inventory),name='upper_inventory')

                model.addConstrs(init_lower_inventory_constr(s, min_inventory),name='lower_inventory')

                # Constraint 5.5
                model.addConstrs(init_maintenance_constr(x, maintenance_vessel_ports, maintenance_vessels), name='maintenance')

                # Constraint 5.6
                model.addConstrs(init_flow_constr(x, all_days, vessel_ids, port_ids, stop_time+horizon_ext), name='flow')

                # Constraint 5.61
                model.addConstrs(init_artificial_flow_constr(x, vessel_start_ports, vessel_available_days, all_days, vessel_ids),
                name='artificial_node')

                # Constraint 5.8
                model.addConstrs(init_upper_demand_constr(stop_time+horizon_ext, x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, port_ids, loading_days,
                partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, upper_partition_demand, des_contract_ids, des_spot_ids,
                des_contract_partitions), name='upper_demand')

                model.addConstrs(init_lower_demand_constr(stop_time+horizon_ext, x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, port_ids, loading_days,
                partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, lower_partition_demand, des_contract_ids, des_spot_ids,
                des_contract_partitions), name='lower_demand')

                #Constraint 5.9 
                model.addConstrs(init_spread_delivery_constraints(x, w, vessel_ids, loading_port_ids, vessel_available_days, des_contract_ids, unloading_days,
                days_between_delivery, des_spot_ids, sailing_time_charter), name='spread_delivery')

                #5.10
                model.addConstrs(init_fob_max_contracts_constr(z, fob_days, fob_contract_ids, stop_time+horizon_ext), name='fob_max_contracts')

                # Constraint 5.11
                model.addConstrs(init_fob_max_order_constr(z, fob_days, fob_spot_ids, fob_spot_art_ports), name='fob_order')

                print("\n--- 5.11 done in: %.1f seconds ---" % (time.time() - start_time))

                # Constraint 5.12
                model.addConstrs(init_berth_constr(stop_time+horizon_ext, x, z, w, vessel_ids, port_ids, loading_days, operational_times, des_contract_ids, fob_ids, fob_operational_times,
                number_of_berths, loading_port_ids, des_spot_ids, fob_loading_ports), name='berth_constraint')

                print("\n--- 5.12 done in: %.1f seconds ---" % (time.time() - start_time))

                # Constraint 5.13 
                model.addConstrs(init_charter_upper_capacity_constr(stop_time+horizon_ext, g, w, charter_vessel_upper_capacity, loading_port_ids, loading_days, 
                des_spot_ids, des_contract_ids), name='charter_upper_capacity')

                model.addConstrs(init_charter_lower_capacity_constr(stop_time+horizon_ext, g, w, charter_vessel_lower_capacity, loading_port_ids, loading_days, 
                des_spot_ids, des_contract_ids), name='charter_lower_capacity') # This should be the last thing happening here

                model.update()

                model.setObjective(init_objective(leftover_stop_time, x, z, s, w, g, fob_revenues, fob_demands, fob_ids, fob_days,
                des_contract_revenues, vessel_capacities, vessel_boil_off_rate, vessel_ids, loading_port_ids, loading_days, 
                spot_port_ids, all_days, sailing_time_charter, unloading_days, charter_boil_off, tank_leftover_value, 
                vessel_available_days, des_contract_ids, sailing_costs, charter_total_cost, des_spot_ids),GRB.MAXIMIZE)
    
                model.update()

                print("\n--- Done removing constraints and add new for next horizon: %.1f seconds ---" % (time.time() - start_time))
        '''
        if iteration_count == 0:
            all_constraints = model.getConstrs()

            for constr in all_constraints:
                if constr.ConstrName.startswith('initital_inventory_control'):
                    model.remove(constr)
        '''

        model.update()
        
        iteration_count += 1

        if horizon_length*(iteration_count+1)+horizon_ext >= len(loading_days):
            last_it = True
            print("THIS IS THE LAST ITERATION: ", iteration_count)

    print("\nTOTAL TIME END: %.1f seconds ---" % (time.time() - start_time_total))
    total_time_entire_model = time.time() - start_time_total    
        
    return model, date, total_time_entire_model



# Function for running model with variable production
def run_variable_production_model(group, filename, time_limit, description):
    model = initialize_variable_production_model(group, filename)
    print(description)
    now = datetime.datetime.now()
    date = now.strftime("%m-%d-%Y, %H-%M")
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}/varprod-{date}.log')
    model.optimize()
    #model.write(f'{filename}_varprod.lp')
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model


# Function for running model with possibility to charter out 
def run_charter_out_model(group, filename, time_limit, description):
    model = initialize_charter_out_model(group, filename)
    print(description)
    now = datetime.datetime.now()
    date = now.strftime("%m-%d-%Y, %H-%M")
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}/charterout-{date}.log')
    model.optimize()
    #model.write(f'{filename}_charter.lp')
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model

# Function for running model with possibility to both vary production and charter out 
def run_combined_model(group, filename, time_limit, description):
    model = initialize_combined_model(group, filename)
    print(description)
    now = datetime.datetime.now()
    date = now.strftime("%m-%d-%Y, %H-%M")
    model.setParam('TimeLimit', time_limit)
    model.setParam('LogFile', f'logFiles/{group}/{filename}/combined-{date}.log')
    model.optimize()
    #model.write(f'{filename}_charter.lp')
    # Finding out what should be returned here as well, mabye just like a status message 
    # Will figure out something smart here
    return model
