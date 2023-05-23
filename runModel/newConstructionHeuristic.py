import gurobipy
import random
import copy
import math
from runModel.constructionSupportFuncs import *

"""
File for initializing a feasible solution to start with 
"""

# Function for setting hints for x-vars (not using any of them)
def find_initial_arcs(x1, maintenance_vessels, all_days, maintenance_vessel_ports, vessel_start_ports, 
                      maintenance_start_times, vessel_available_days, sailing_costs):

    x = x1.copy()

    # Setting all arcs except the arcs indicating the vessel is not used to zero
    for (vessel, port1, day1, port2, day2), value in x.items():
        if port1 == 'ART_PORT' and day1 == 0 and port2 == 'EXIT_PORT' and day2 == all_days[-1]+1 and not maintenance_vessels.__contains__(vessel):
            x[vessel, port1, day1, port2, day2] = 1
        else:
            x[vessel, port1, day1, port2, day2] = 0

    for vessel in maintenance_vessels: 
        find_best_maintenance_arcs(vessel, x, maintenance_vessel_ports, vessel_start_ports, vessel_available_days,
        maintenance_start_times, all_days, sailing_costs)

    return x


# Function for setting hints for production-vars (producing at full capacity all planning period)
def find_production_vars(q1, production_quantities):

    q = q1.copy()

    for (loading_port, day), value in q.items():
        q[loading_port, day] = production_quantities[loading_port, day]

    return q


# Function for setting hint for charter-out-vars (not chartering out any vessels)
def find_charter_out_vars(y1, vessel_ids):
    
    y = y1.copy()

    for v in y.keys():
        y[v] = 0

    return y


# Function for setting an initail solution for the problem (greedy)
def find_initial_solution(z1, s1, w1, g1, all_days, des_contract_ids, lower_partition_demand, upper_partition_demand,
        des_contract_partitions, partition_days, fob_ids, fob_contract_ids, fob_demands, fob_days, min_inventory, max_inventory,
        initial_inventory, production_quantities, minimum_spread, des_loading_ports, number_of_berths, sailing_time_charter,
        loading_days, fob_loading_ports, maintenance_vessels, fob_spot_art_ports, unloading_days, loading_port_ids, des_spot_ids):

    # This function should return a initial solution that is feasible 
    # x : arcs
    # z : fob 
    # w : charter binary
    # g : charter continuous
    # s : inventory for loading ports 

    lower_charter_amount = 135000
    upper_charter_amount = 160000

    # Creating copies of variables
    z = z1.copy()
    s = s1.copy()
    w = w1.copy()
    g = g1.copy()
    
    # Producing all the LNG and initializing all the storage 
    for (loading_port, day), value in s.items():
        if day == all_days[0]:
            s[loading_port, day] = initial_inventory[loading_port] + production_quantities[loading_port, day]
        else: 
            s[loading_port, day] = s[loading_port, day-1] + production_quantities[loading_port, day]

    # Setting all the charter variables to zero to start with
    for (loading_port, day, contract), value in g.items():
        g[loading_port, day, contract] = 0
        w[loading_port, day, contract] = 0
    
    # Stting all the fob variables to zero to start with
    for (fob_id, day), value in z.items():
        z[fob_id, day] = 0


    # Boil-off factor for all des-contracts
    boil_off_factors = calc_boil_off_factors(des_contract_ids, des_loading_ports, sailing_time_charter)

    # ------ Then finding charter variables for DES contracts --------
    # Creating new list and dict for des_contract_ids and des_contract_partitions and fob
    des_contract_ids_updated = copy.deepcopy(des_contract_ids)
    des_contract_partitions_updated = copy.deepcopy(des_contract_partitions)
    fob_contract_ids_updated = copy.deepcopy(fob_contract_ids)
    planned_fob_days = {fob_contract_id: set_planned_fob_day(fob_contract_id, fob_days) for fob_contract_id in fob_contract_ids_updated}
    # all_demand_satisfied is False as long as not all contracts is fulfuilled 
    all_demand_satisfied = False
    # amount chartered is calculcated 
    amount_chartered = calculate_total_demand_delivered(des_contract_partitions, sailing_time_charter, partition_days, g, des_contract_ids, boil_off_factors)
    demand_is_satisfied = update_if_demand_is_satisfied(amount_chartered, des_contract_ids_updated, lower_partition_demand)

    # For each loading day where LNG is produced
    for loading_day in loading_days:

        # For each loading port in the model 
        for loading_port in loading_port_ids:

            # In case you can ship out more on one day
            for iteration_count in range(1, number_of_berths[loading_port]+1):

                planned_fobs = check_if_fob_is_planned(loading_day, planned_fob_days, loading_port, fob_loading_ports)

                if len(planned_fobs) != 0:
                    fob_contract_id, planned_fob_days = choose_fob(planned_fobs, fob_days, planned_fob_days)
                    fob_amount = fob_demands[fob_contract_id]
                    if check_feasible_fob_move(loading_day, loading_days, s, loading_port, fob_amount, min_inventory, w, z, 
                    number_of_berths, fob_loading_ports, fob_contract_id):
                        z[fob_contract_id, loading_day] = 1
                        update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands, fob_loading_ports)
                        fob_contract_ids_updated.remove(fob_contract_id)
                        planned_fob_days.pop(fob_contract_id)
                        if len(fob_contract_ids_updated)==0:
                            # printing jippi beacuse we are done with FOB
                            print('Finished with FOB, jippi!\n')
                        continue
                    else:
                        planned_fob_days[fob_contract_id] += 1

                #print(f'Day: {loading_day} for loading port {loading_port}, round {iteration_count} \n')
                # Randomly choosing an amount to charter
                charter_amount = upper_charter_amount

                # If there is too little 
                inventory = s[loading_port, loading_day]   
                if inventory < min_inventory[loading_port]+charter_amount:
                    #print(f'Inventory infeasible for loading port {loading_port} on  day: {loading_day}, inventory: {inventory}')
                    continue

                # If there is not enough berths
                if (sum(value1 for (i,t,j), value1 in w.items() if i ==loading_port and t == loading_day)+sum(value2 for (z,t), value2
                in z.items() if loading_port in fob_loading_ports[z] and t == loading_day)+1 > number_of_berths[loading_port]):
                    #print(f'Not enough berths for this loading port ')
                    continue

                # Finding the best contract and the best partition
                best_des_contract, best_partition = find_best_contract_and_partition(loading_day, amount_chartered, loading_port, lower_partition_demand,
                des_contract_ids_updated, des_loading_ports, des_contract_partitions_updated, partition_days, sailing_time_charter, minimum_spread, w,
                loading_days, charter_amount, upper_partition_demand, unloading_days, boil_off_factors)

                # Did not find any feasible contracts?? Weird but can happen I guess
                if (best_des_contract, best_partition) == (None, None):
                    #print('Did not find a best partition and a best contract')
                    charter_amount = random.randrange(lower_charter_amount, lower_charter_amount+(upper_charter_amount-lower_charter_amount)*1/2)
                    best_des_contract, best_partition = find_best_contract_and_partition(loading_day, amount_chartered, loading_port, lower_partition_demand,
                    des_contract_ids_updated, des_loading_ports, des_contract_partitions_updated, partition_days, sailing_time_charter, minimum_spread, w,
                    loading_days, charter_amount, upper_partition_demand, unloading_days, boil_off_factors)
                    if (best_des_contract, best_partition) == (None, None):
                        continue
                
                
                missing_demand = (lower_partition_demand[best_des_contract, best_partition] - amount_chartered[best_des_contract][best_partition])/boil_off_factors[best_des_contract]
                if (math.ceil(missing_demand/lower_charter_amount) == math.ceil(missing_demand/upper_charter_amount)):
                    charter_amount = lower_charter_amount
                else: 
                    charter_amount = missing_demand/(math.ceil(missing_demand/upper_charter_amount))


                # Finding the corresponding loading port 
                des_loading_port = loading_port

                # Checking if the charter move is feasible
                if check_feasible_charter_move(loading_day, best_partition, best_des_contract, des_loading_port, charter_amount, min_inventory, s, w,
                                number_of_berths, minimum_spread, amount_chartered, upper_partition_demand, loading_days, fob_loading_ports, z,
                                partition_days, sailing_time_charter,boil_off_factors):
                    #print(f'amount_chartered: {amount_chartered}')
                    #print(f'Found feasible move for {best_des_contract}, for partition {best_partition} in day {loading_day} with amount {charter_amount}')
                    g[des_loading_port, loading_day, best_des_contract] = charter_amount
                    w[des_loading_port, loading_day, best_des_contract] = 1
                    update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands, fob_loading_ports)
                    # her forsvinner de
                    amount_chartered = calculate_total_demand_delivered(des_contract_partitions, sailing_time_charter, partition_days,
                    g, des_contract_ids, boil_off_factors)
                    #print(f'amount_chartered: {amount_chartered}')
                    demand_is_satisfied = update_if_demand_is_satisfied(amount_chartered, des_contract_ids_updated, lower_partition_demand)
                    if demand_is_satisfied[best_des_contract]:
                        print(f'{best_des_contract} fulfilled \n\n')
                        remove_satisfied_partitions(des_contract_ids_updated, des_contract_partitions_updated, amount_chartered, lower_partition_demand)
                        des_contract_ids_updated.remove(best_des_contract)
                    if len(des_contract_ids_updated)==0:
                        print(f'All contracts fulfilled \n\n')
                        all_demand_satisfied = True
                        print('Finished with DES, jippi!\n')
                        break
                    else:
                        remove_satisfied_partitions(des_contract_ids_updated, des_contract_partitions_updated, amount_chartered, lower_partition_demand)
                else:
                    # update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                    continue
            
            # If inventory this day, after all iterations is infeasible: create fake fob
            if s[loading_port, loading_day] > max_inventory[loading_port]:
                fake_fob = fob_spot_art_ports[loading_port]
                z[fake_fob, loading_day] = 1
                update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands, fob_loading_ports)


 # ------------ Fixing left-over DES contracts -------------
    if not all_demand_satisfied:
        print('\n Not all contracts were satisfied')

        for des_contract in des_contract_ids_updated:
            if des_contract  not in des_spot_ids:
                for partition in des_contract_partitions_updated[des_contract]:

                    g_vars = []
                    
                    # Identifying how much is missing for the contract and scaling for boil off 
                    missing_required_demand = (lower_partition_demand[des_contract, partition] - amount_chartered[des_contract][partition])/boil_off_factors[des_contract]

                    for (i,t,j), value in g.items():
                        if j==des_contract and t+sailing_time_charter[i,j] in partition_days[partition] and value > 0:
                            g_vars.append((i,t,j))

                            # If missing demand is small enough to add to 
                            if missing_required_demand + value < upper_charter_amount:

                                # inventory constraints, never below minimum inventory
                                inventory_feasible = True
                                for t_ in range(t, loading_days[-1]+1):
                                    if s[i, t_] - missing_required_demand < min_inventory[i]:
                                        inventory_feasible = False
                                        break # Made partition feasible
                                if inventory_feasible:
                                    g[i, t, j] += missing_required_demand
                                    update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands, fob_loading_ports)
                                    amount_chartered = calculate_total_demand_delivered(des_contract_partitions, sailing_time_charter, partition_days,
                                    g, des_contract_ids, boil_off_factors)
                                    remove_satisfied_partitions(des_contract_ids_updated, des_contract_partitions_updated, amount_chartered, lower_partition_demand)
                                    break
                                else:
                                    continue
                            else: 
                                biggest_feasible_delivery = upper_charter_amount - value
                                inventory_feasible = True
                                for t_ in range(t, loading_days[-1]+1):
                                    if s[i, t_] - biggest_feasible_delivery < min_inventory[i]:
                                        inventory_feasible = False
                                        break # Made partition feasible
                                if inventory_feasible:
                                    g[i,t,j] += biggest_feasible_delivery
                                    update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands, fob_loading_ports)
                                    amount_chartered = calculate_total_demand_delivered(des_contract_partitions, sailing_time_charter, partition_days,
                                    g, des_contract_ids, boil_off_factors)
                                    missing_required_demand -= biggest_feasible_delivery
                                    continue
                    
                    # If the partition is not the first partition (with minimum demand==0)
                    if not len(g_vars)==0:
                        average_charter_amount = (lower_partition_demand[des_contract,partition]/boil_off_factors[des_contract])/len(g_vars)
                        print(f'Did not finish for partition {partition}, must deliver at least {average_charter_amount} per ship')
                        # distance_upper = abs(average_charter_amount- upper_charter_amount)
                        # distance_lower = abs(average_charter_amount-lower_charter_amount)

        print('(finished with DES)\n')        
        print(f'Des contracts not satisfied : {des_contract_ids_updated}\n')
        print(f'Des contracts partitions not satisfied : {des_contract_partitions_updated}\n')
    

    if len(fob_contract_ids_updated) != 0:
        print('\n Not all fobs were fixed')
        all_demand_satisfied = False

    print('Before fixing inventory: \n')
    for (loading_port, day), value in s.items():
        print(loading_port, day, value)
    
    # Fixing excess demand
    for (loading_port, day), value in s.items():
        if value > max_inventory[loading_port]:
            for fake_fob_loading_port, fake_fob in fob_spot_art_ports.items():
                if fake_fob_loading_port==loading_port:
                    z[fake_fob, day] = 1
                    update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands, fob_loading_ports)
    
    print('\nFinished with fixing inventory, jippi!\n')
    for (loading_port, day), value in s.items():
        print(loading_port, day, value)


    return z, s, w, g, all_demand_satisfied
