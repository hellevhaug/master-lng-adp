import random

# Calculates all amount delivered for every partition in every contract
def calculate_total_demand_delivered(des_contract_partitions, sailing_time_charter, partition_days, g, des_contract_ids):
    amount_chartered = {des_contract: {partition:0 for partition in des_contract_partitions[des_contract]} for des_contract in des_contract_ids}
    for des_contract in des_contract_ids:
        for partition in des_contract_partitions[des_contract]:
            for (i,t,j), value in g.items():
                if j == des_contract:
                    if t+sailing_time_charter[i,j] in partition_days[partition]:
                        amount_chartered[des_contract][partition] += value*0.85   
    return amount_chartered


# Updating the s-variables with g and z (charter and fob)
def update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands):
    for (loading_port, day), value in s.items():
        if day == all_days[0]:
            s[loading_port, day] = initial_inventory[loading_port] + production_quantities[loading_port, day]
            for j in des_contract_ids:
                if (loading_port, day, j) in g.keys():
                    s[loading_port, day] -= g[loading_port, day, j] 
            for fob_id in fob_ids:
                if (fob_id,day) in z.keys():
                    s[loading_port, day] -= z[fob_id, day]*fob_demands[fob_id]
        else: 
            s[loading_port, day] = s[loading_port, day-1] + production_quantities[loading_port, day]
            for j in des_contract_ids:
                if (loading_port, day, j) in g.keys():
                    s[loading_port, day] -=  g[loading_port, day, j] 
            for fob_id in fob_ids:
                if (fob_id, day) in z.keys():
                    s[loading_port, day] -= z[fob_id, day]*fob_demands[fob_id]


# Updates the demand-is-satisfied-dict
def update_if_demand_is_satisfied(amount_chartered, des_contract_ids, lower_partition_demand):
    demand_is_satisfied = {des_contract: False for des_contract in des_contract_ids}
    for des_contract in des_contract_ids:
        contract_satisfied = True
        for partition, value in amount_chartered[des_contract].items():
            if value < lower_partition_demand[des_contract,partition]:
                contract_satisfied = False
                break
        demand_is_satisfied[des_contract] = contract_satisfied 
    #print(f'Finishing finding demand for partition: {partition}, with {amount_chartered[partition]}')
    #print(partition, value, lower_partition_demand)
    return demand_is_satisfied


# Checks if a given charter-move is feasible
def check_feasible_charter_move(day, partition, des_contract, des_loading_port, charter_amount, min_inventory, s, w,
    number_of_berths, minimum_spread, amount_chartered, upper_partition_demand, loading_days, fob_loading_ports, z,
    partition_days, sailing_time_charter,g):

    # 
    if day+sailing_time_charter[des_loading_port,des_contract] not in partition_days[partition]:
        print('should be within the partitions unloading days')
        return False

    # inventory constraints, never below minimum inventory
    for t in range(day, loading_days[-1]+1):
        if s[des_loading_port, t] - charter_amount < min_inventory[des_loading_port]:
            print('inventory problems')
            return False
    
    # berth constraints for the loading port, never more than number of berth g vars per day
    if (sum(value for (i,t,j), value in w.items() if i ==des_loading_port and t == day)+sum(value for (z,t), value
    in z.items() if des_loading_port in fob_loading_ports[z] and t == day)+1 > number_of_berths[des_loading_port]):
        print('berth problems')
        return False
    
    # minimum spread, assumes that there is one charter boat with one speed and therefore can look at t
    if sum(value for (i,t,j), value in w.items() if j == des_contract and t >= day and t < (day + minimum_spread)) +1 > 1:
        print(sum(value for (i,t,j), value in w.items() if j == des_contract and t >= day and t <= day + minimum_spread) +1)
        print(f'spread problems for {partition} on day {day}')
        return False
    
    # never above upper demand for partition
    for ot_partition, value in amount_chartered[des_contract].items():
        if day+sailing_time_charter[des_loading_port, des_contract] in partition_days[ot_partition]:
            if amount_chartered[des_contract][ot_partition] + charter_amount*0.85 > upper_partition_demand[des_contract, ot_partition]:
                print('infeasible pa')
                return False

    else:
        return True


# Function for checking is a given DES-move is feasible
def check_feasible_fob_move(day, loading_days, s, fob_loading_port, fob_amount, min_inventory, w, z, 
    number_of_berths, fob_loading_ports, fob_contract_id):

    # inventory constraints, never below minimum inventory
    for t in range(day, loading_days[-1]+1):
        if s[fob_loading_port, t] - fob_amount < min_inventory[fob_loading_port]:
            return False
    
    # berth constraints for the loading port, never more than number of berth g vars per day
    if (sum(value for (i,t,j), value in w.items() if i == fob_loading_port and t == day)+sum(value for (z,t), value
    in z.items() if t==day and fob_loading_port in fob_loading_ports[z])+1 > number_of_berths[fob_loading_port]):
        return False
    
    # constraints are not violated
    else:
        return True 


# Function for resetting the g- and w-vars
def reset_g_vars(g_altered_vars, g, w):
    for (i,t,j) in g_altered_vars:
        g[i,t,j] = 0
        w[i,t,j] = 0


# Function for randomizing a list of days
def generate_random_loading_days(loading_days):

    random_loading_days = []

    while loading_days:
        random_day = random.choice(loading_days)  # Randomly select a day
        random_loading_days.append(random_day)  # Add the chosen day to the list of chosen days
        loading_days.remove(random_day)
    
    return random_loading_days


# Function for finding the best contract,partition to charter to at day=loading_day
def find_best_contract_and_partition(loading_day, amount_chartered, loading_port, lower_partition_demand,
    des_contract_ids, des_loading_ports, des_contract_partitions, partition_days,
    sailing_time_charter, minimum_spread, w, loading_days, charter_amount, upper_partition_demand, unloading_days):

    best_contract, best_partition = None, None

    best_amount_missing = 0
    best_last_partition_day = 1000

    for des_contract_id in des_contract_ids: 
        if des_loading_ports[des_contract_id].__contains__(loading_port):
            # Minimum spread
            if sum(w[loading_port,t,des_contract_id] for t in loading_days if t >= loading_day and t < loading_day+minimum_spread and t+sailing_time_charter[loading_port, des_contract_id] in unloading_days[des_contract_id])+ 1 > 1:
                #print(f'{partition}')
                #print('minimum spread')
                continue
            for partition in des_contract_partitions[des_contract_id]:
                # Should be delivered within unloading days for the partition
                if not loading_day+sailing_time_charter[loading_port, des_contract_id] in partition_days[partition]:
                    #print(f'{partition}')
                    #print('not withing time window')
                    continue
                # If lower is bad
                if lower_partition_demand[des_contract_id, partition] < amount_chartered[des_contract_id][partition]:
                    #print(f'{partition}')
                    #print('lower is bad')
                    continue
                # If upper is bad
                infeasible_partition = False
                for ot_partition, value in amount_chartered[des_contract_id].items():
                    if loading_day+sailing_time_charter[loading_port, des_contract_id] in partition_days[ot_partition]:
                        if value + charter_amount*0.85 > upper_partition_demand[des_contract_id, ot_partition]:
                            infeasible_partition = True
                            break
                if infeasible_partition:
                    continue
                last_partition_day = partition_days[partition][-1]
                if last_partition_day < best_last_partition_day:
                    best_last_partition_day = last_partition_day
                    best_contract, best_partition = des_contract_id, partition
                elif last_partition_day == best_last_partition_day:
                    amount_missing = lower_partition_demand[des_contract_id,partition] - amount_chartered[des_contract_id][partition]
                    if amount_missing > best_amount_missing:
                        best_last_partition_day = last_partition_day
                        best_amount_missing = amount_missing
                        best_contract, best_partition = des_contract_id, partition
                else:
                    continue

    return best_contract, best_partition


# Just sets stupid maintenance arcs
def find_best_maintenance_arcs(vessel, x, maintenance_vessel_ports, vessel_start_ports, vessel_available_days,
    maintenance_start_times, all_days, sailing_costs):

    # Ensuring that the vessels starts a voyage
    x[vessel, 'ART_PORT',0, vessel_start_ports[vessel], vessel_available_days[vessel][0]] = 1

    # Goes only to maintenance and then done
    direct_arc = (vessel, vessel_available_days[vessel][0],vessel_start_ports[vessel], maintenance_vessel_ports[vessel], maintenance_start_times[vessel])
    sailing_costs[direct_arc] = 0
    x[direct_arc] = 1
    x[vessel, maintenance_vessel_ports[vessel], maintenance_start_times[vessel], 'EXIT_PORT', all_days[-1]+1]


    return 


# Function for removing satisfied partitions from the des_contract_partition_updated-dict
def remove_satisfied_partitions(des_contract_ids_updated, des_contract_partitions_updated, amount_chartered, lower_partition_demand):
    for des_contract_id in des_contract_ids_updated:
        for partition in des_contract_partitions_updated[des_contract_id]:
            # If lower demand is satisfied, the partition is satisfied
            if amount_chartered[des_contract_id][partition] >= lower_partition_demand[des_contract_id,partition]:
                print(f'Partition {partition} fulfilled \n\n')
                des_contract_partitions_updated[des_contract_id].remove(partition)