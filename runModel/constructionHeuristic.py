import gurobipy
import random
from runModel.constructionSupportFuncs import *

"""
File for initializing a feasible solution to start with 
"""

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

def find_initial_solution(z1, s1, w1, g1, all_days, des_contract_ids, lower_partition_demand, upper_partition_demand,
        des_contract_partitions, partition_days, fob_ids, fob_contract_ids, fob_demands, fob_days, min_inventory, max_inventory,
        initial_inventory, production_quantities, minimum_spread, des_loading_ports, number_of_berths, sailing_time_charter,
        loading_days, fob_loading_ports, maintenance_vessels, fob_spot_art_ports, unloading_days, loading_port_ids):

    # This function should return a initial solution that is feasible 
    # x : arcs
    # z : fob 
    # w : charter binary
    # g : charter continuous
    # s : inventory for loading ports 

    lower_charter_amount = 130000
    upper_charter_amount = 175000

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



    # ------------ Fixing FOB contracts -------------
    amount_picked_up = {fob_contract_id:0 for fob_contract_id in fob_contract_ids}
    # for each contract
    for fob_contract_id in fob_contract_ids:
        fob_satisfied = False
        # finding the corresponding loading port 
        fob_loading_port = fob_loading_ports[fob_contract_id][0]
        # iterating through days until we find feasible day
        while not fob_satisfied:
            # randomizing the days
            fob_random_loading_days = [i for i in loading_days if i in fob_days[fob_contract_id]]
            fob_random_loading_days = generate_random_loading_days(fob_random_loading_days)
            # starts with a random day
            for day in fob_random_loading_days:
                # will deliver exactly what the FOB contract require 
                fob_amount = fob_demands[fob_contract_id]
                # checks if the fob-move is feasible
                if check_feasible_fob_move(day, loading_days, s, fob_loading_port, fob_amount, min_inventory, w, z, 
                    number_of_berths, fob_loading_ports, fob_contract_id):
                    # if yes: sets the z-variable to 1
                    z[fob_contract_id, day] = 1
                    # updates inventory
                    update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                    # updates the amount-picked-up-dict
                    amount_picked_up[fob_contract_id] = fob_amount
                    fob_satisfied = True
                    # moves on to next FOB-contract
                    break




    # printing jippi beacuse we are done with FOB
    print('(finished with FOB, jippi)')
    for (f,t), value in z.items():
        if value != 0:
            print(f,t, value)



    # ------ Then finding charter variables for DES contracts --------
    print(f'DES contract ids: {des_contract_ids}')
    # Creating new list and dict for des_contract_ids and des_contract_partitions
    des_contract_ids_updated = des_contract_ids.copy()
    des_contract_partitions_updated = des_contract_partitions.copy()
    # all_demand_satisfied is False as long as not all contracts is fulfuilled 
    all_demand_satisfied = False
    # amount chartered is calculcated 
    amount_chartered = calculate_total_demand_delivered(des_contract_partitions, sailing_time_charter, partition_days, g, des_contract_ids)
    demand_is_satisfied = update_if_demand_is_satisfied(amount_chartered, des_contract_ids_updated, lower_partition_demand)
    # For each loading day where LNG is produced
    for loading_day in loading_days:
        
        # For each loading port in the model 
        for loading_port in loading_port_ids:

            print(f'Day: {loading_day} for loading port {loading_port }\n')
            print(f'des contract ids: {des_contract_ids}')
            print(f'des contract partitions: {des_contract_partitions}')
            # Randomly choosing an amount to charter
            charter_amount = random.randrange(lower_charter_amount, upper_charter_amount)

            # If there is too little 
            inventory = s[loading_port, loading_day]   
            if inventory < min_inventory[loading_port]+charter_amount:
                print(f'Inventory infeasible for loading port {loading_port} on  day: {loading_day}, inventory: {inventory}')
                continue

            # Finding the best contract and the best partition
            best_des_contract, best_partition = find_best_contract_and_partition(loading_day, amount_chartered, loading_port, lower_partition_demand,
            des_contract_ids_updated, des_loading_ports, des_contract_partitions_updated, partition_days, sailing_time_charter, minimum_spread, w,
            loading_days, charter_amount, upper_partition_demand, unloading_days)

            # Did not find any feasible contracts?? Weird but can happen I guess
            if (best_des_contract, best_partition) == (None, None):
                print('Did not find a best partition and a best contract')
                print(f'remaining contracts:{des_contract_ids_updated}')
                print(f'remaining partitions:{des_contract_partitions_updated}')
                continue

            print(best_des_contract, best_partition)

            # Finding the corresponding loading port 
            des_loading_port = loading_port

            # Checking if the charter move is feasible
            if check_feasible_charter_move(loading_day, best_partition, best_des_contract, des_loading_port, charter_amount, min_inventory, s, w,
                            number_of_berths, minimum_spread, amount_chartered, upper_partition_demand, loading_days, fob_loading_ports, z,
                            partition_days, sailing_time_charter,g):
                #print(f'amount_chartered: {amount_chartered}')
                print(f'Found feasible move for {best_des_contract}, for partition {best_partition} in day {loading_day} with amount {charter_amount}')
                g[des_loading_port, loading_day, best_des_contract] = charter_amount
                w[des_loading_port, loading_day, best_des_contract] = 1
                update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                print(f'des contract ids: {des_contract_ids}')
                print(f'des contract partitions: {des_contract_partitions}')
                # her forsvinner de
                amount_chartered = calculate_total_demand_delivered(des_contract_partitions, sailing_time_charter, partition_days,
                g, des_contract_ids)
                #print(f'amount_chartered: {amount_chartered}')
                print(f'des contract ids: {des_contract_ids}')
                print(f'des contract partitions: {des_contract_partitions}')
                demand_is_satisfied = update_if_demand_is_satisfied(amount_chartered, des_contract_ids_updated, lower_partition_demand)
                if demand_is_satisfied[best_des_contract]:
                    print(f'{best_des_contract} fulfilled \n\n')
                    des_contract_ids_updated.remove(best_des_contract)
                    des_contract_partitions_updated = remove_satisfied_partitions(des_contract_ids_updated, des_contract_partitions_updated, amount_chartered, lower_partition_demand)
                if len(des_contract_ids_updated)==0:
                    print(f'All contracts fulfilled \n\n')
                    all_demand_satisfied = True
                    print('Finished with DES')
                    break
                else:
                    des_contract_partitions_updated = remove_satisfied_partitions(des_contract_ids_updated, des_contract_partitions_updated, amount_chartered, lower_partition_demand)
            else:
                # update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                continue




 # ------------ Fixing left-over DES contracts -------------
    if not all_demand_satisfied:
        relevant_days = {(l_port, day): value for (l_port, day), value in s.items() if value > max_inventory[l_port]}
        for (loading_port, day), value in relevant_days.items():
            for des_contract in des_contract_partitions_updated.keys():
                for partition in des_contract_partitions_updated[des_contract]:
                    # Not relevant, wont make it in time/too early
                    if day+sailing_time_charter[loading_port, des_contract] not in partition_days[partition]:
                        continue
                    # How much is missing from the contract
                    missing_required_demand = lower_partition_demand[des_contract, partition] - amount_chartered[des_contract][partition]

                    if (missing_required_demand/0.85 + amount_chartered[des_contract][partition] < upper_charter_amount and 
                    missing_required_demand/0.85 + amount_chartered[des_contract][partition] < value-min_inventory[loading_port]):
                        g[loading_port, day, des_contract] += missing_required_demand/0.85
                        update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)


                    # Missing demand is larger than what is feasible to leave as inventory at loading port 
                    elif missing_required_demand/0.85 > value-min_inventory[loading_port] and missing_required_demand > lower_charter_amount:
                        smart_charter_amount = random.randrange(lower_charter_amount, value-min_inventory[loading_port])
                        
                    elif missing_required_demand/0.85 <= value-min_inventory[loading_port]:
                        smart_charter_amount = random.randrange(lower_charter_amount, upper_charter_amount)

                    else: 
                        smart_charter_amount = random.randrange(lower_charter_amount, (upper_charter_amount+lower_charter_amount)/2)
                    
                    if check_feasible_charter_move(loading_day, best_partition, best_des_contract, des_loading_port, smart_charter_amount, min_inventory, s, w,
                            number_of_berths, minimum_spread, amount_chartered, upper_partition_demand, loading_days, fob_loading_ports, z,
                            partition_days, sailing_time_charter,g):
                        g[loading_port, des_contract] = smart_charter_amount
                        w[loading_port, des_contract] = 1
                        update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                        amount_chartered = calculate_total_demand_delivered(des_contract_partitions, sailing_time_charter, partition_days,
                        g, des_contract_ids)

                    else:
                        continue


    print('(finished with DES)\n')        
    print(amount_chartered)
    
    
    for (loading_port, day), value in s.items():
        print(loading_port, day, value)
    
    for (i,t,j), value in g.items():
        if value != 0:
            print(i,t,j, value)

    for (f,t), value in z.items():
        if value != 0:
            print(f,t, value)
    
    # Fixing excess demand
    for (loading_port, day), value in s.items():
        if value > max_inventory[loading_port]:
            for fake_fob_loading_port, fake_fob in fob_spot_art_ports.items():
                if fake_fob_loading_port==loading_port:
                    z[fake_fob, day] = 1
    
    print('(finished with inventory')


    return z, s, w, g
