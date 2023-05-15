import gurobipy
import random

"""
File for initializing a feasible solution to start with 
"""

def find_initial_solution(x1, z1, s1, w1, g1, all_days, des_contract_ids, lower_partition_demand, upper_partition_demand,
        des_contract_partitions, partition_days, fob_ids, fob_contract_ids, fob_demands, fob_days, min_inventory, max_inventory,
        initial_inventory, production_quantities, minimum_spread, des_loading_ports, number_of_berths, sailing_time_charter,
        loading_days, fob_loading_ports, maintenance_vessels, fob_spot_art_ports):

    # This function should return a initial solution that is feasible 
    # x : arcs
    # z : fob 
    # w : charter binary
    # g : charter continuous
    # s : inventory for loading ports 

    lower_charter_amount = 130000
    upper_charter_amount = 175000

    x = x1.copy()
    z = z1.copy()
    s = s1.copy()
    w = w1.copy()
    g = g1.copy()

    # Setting all arcs except the arcs indicating the vessel is not used to zero
    for (vessel, port1, day1, port2, day2), value in x.items():
        if maintenance_vessels.__contains__(vessel):
            pass
        else:
            if port1 == 'ART_PORT' and day1 == 0 and port2 == 'EXIT_PORT' and day2 == all_days[-1]+1:
                x[vessel, port1, day1, port2, day2] = 1
            else:
                x[vessel, port1, day1, port2, day2] = 0
    
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

    amount_picked_up = {fob_contract_id:0 for fob_contract_id in fob_contract_ids}
    for fob_contract_id in fob_contract_ids:
        fob_satisfied = False
        fob_loading_port = fob_loading_ports[fob_contract_id][0]
        count = 0
        while not fob_satisfied:
            fob_random_loading_days = [i for i in loading_days if i in fob_days[fob_contract_id]]
            fob_random_loading_days = generate_random_loading_days(fob_random_loading_days)
            for day in fob_random_loading_days:
                fob_amount = fob_demands[fob_contract_id]
                if check_feasible_fob_move(day, loading_days, s, fob_loading_port, fob_amount, min_inventory, w, z, 
                    number_of_berths, fob_loading_ports, fob_contract_id):
                    z[fob_contract_id, day] = 1
                    update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                    amount_picked_up[fob_contract_id] = fob_amount
                    fob_satisfied = True
                    break

    print('(finished with FOB)')
    for (f,t), value in z.items():
        if value != 0:
            print(f,t, value)

        # Then finding charter variables
    amount_chartered = {des_contract: {partition:0 for partition in des_contract_partitions[des_contract]} for des_contract in des_contract_ids}
    des_contract_partitions_updated = des_contract_partitions.copy()
    des_contract_ids_updated = des_contract_ids.copy()
    all_demand_satisfied = False
    for loading_day in loading_days:

        print(f'Day: {loading_day} \n')
        # Randomly choosing an amount to charter
        charter_amount = random.randrange(lower_charter_amount, upper_charter_amount)

        # Finding the best contract and the best partition
        best_des_contract, best_partition = find_best_contract_and_partition(loading_day, amount_chartered, loading_port, lower_partition_demand,
        des_contract_ids_updated, des_loading_ports, des_contract_partitions_updated, partition_days, sailing_time_charter, minimum_spread, w,
        loading_days, charter_amount, upper_partition_demand)

        if (best_des_contract, best_partition) == (None, None):
            print('Did not find a best partition and a best contract')
            continue

        print(best_des_contract, best_partition)

        # Finding the corresponding loading port 
        des_loading_port = des_loading_ports[best_des_contract][0]

        inventory = s[des_loading_port, loading_day]   
        if inventory < min_inventory[des_loading_port]+charter_amount:
            print(f'Inventory infeasible for day: {loading_day}, inventory: {inventory}')
            continue

        # Checking if the charter move is feasible
        if check_feasible_charter_move(loading_day, best_partition, best_des_contract, des_loading_port, charter_amount, min_inventory, s, w,
                        number_of_berths, minimum_spread, amount_chartered, upper_partition_demand, loading_days, fob_loading_ports, z,
                        partition_days, sailing_time_charter,g):
            print(f'Found feasible move for {best_des_contract}, for partition {best_partition} in day {loading_day} with amount {charter_amount}')
            g[des_loading_port, loading_day, best_des_contract] = charter_amount
            w[des_loading_port, loading_day, best_des_contract] = 1
            update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
            amount_chartered[best_des_contract] = calculate_total_demand_delivered(best_des_contract, des_contract_partitions,
            sailing_time_charter, partition_days, g)
            demand_is_satisfied = check_if_demand_is_satisfied(amount_chartered, best_des_contract, lower_partition_demand)
            if demand_is_satisfied:
                print(f'{best_des_contract} fulfilled \n\n')
                des_contract_ids_updated.remove(best_des_contract)
            if len(des_contract_ids_updated)==0:
                print(f'All contracts fulfilled \n\n')
                all_demand_satisfied = True
                print('Finished with DES')
                break
            if amount_chartered[best_des_contract][best_partition] >= lower_partition_demand[best_des_contract,best_partition]:
                print(f'Partition {best_partition} fulfilled \n\n')
                des_contract_partitions_updated[best_des_contract].remove(best_partition)
        

    print('(finished with DES\n')        
    print(amount_chartered)


    # Fixing excess demand
    for (loading_port, day), value in s.items():
        if value > max_inventory[loading_port]:
            for fake_fob_loading_port, fake_fob in fob_spot_art_ports.items():
                if fake_fob_loading_port==loading_port:
                    z[fake_fob, day] = 1
    
    print('(finished with inventory')
    """
    
    for (loading_port, day), value in s.items():
        print(loading_port, day, value)
    
    for (i,t,j), value in g.items():
        if value != 0:
            print(i,t,j, value)

    for (f,t), value in z.items():
        if value != 0:
            print(f,t, value)
    """

    return x, z, s, w, g


# Calculates all amount delivered for every partition in every contract
def calculate_total_demand_delivered(des_contract, des_contract_partitions, sailing_time_charter,
    partition_days, g):
    amount_chartered = {partition:0 for partition in des_contract_partitions[des_contract]}
    for partition in des_contract_partitions[des_contract]:
        for (i,t,j), value in g.items():
            if j == des_contract:
                if t+sailing_time_charter[i,j] in partition_days[partition]:
                    amount_chartered[partition] += value*0.85   
    return amount_chartered


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



# Checks if all partitions is satisfied 
def check_if_demand_is_satisfied(amount_chartered, des_contract, lower_partition_demand):
    
    for partition, value in amount_chartered[des_contract].items():
        if value < lower_partition_demand[des_contract,partition]:
            return False
    #print(f'Finishing finding demand for partition: {partition}, with {amount_chartered[partition]}')
    #print(partition, value, lower_partition_demand)
    return True


# Checks if new charter variable is feasible
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



def reset_g_vars(g_altered_vars, g, w):
    for (i,t,j) in g_altered_vars:
        g[i,t,j] = 0
        w[i,t,j] = 0


def generate_random_loading_days(loading_days):

    random_loading_days = []

    while loading_days:
        random_day = random.choice(loading_days)  # Randomly select a day
        random_loading_days.append(random_day)  # Add the chosen day to the list of chosen days
        loading_days.remove(random_day)
    
    return random_loading_days



def find_best_contract_and_partition(loading_day, amount_chartered, loading_port, lower_partition_demand,
    des_contract_ids, des_loading_ports, des_contract_partitions, partition_days,
    sailing_time_charter, minimum_spread, w, loading_days, charter_amount, upper_partition_demand):

    best_contract, best_partition = None, None

    best_amount_missing = 0
    best_last_partition_day = 1000

    for des_contract_id in des_contract_ids:
        loading_port = des_loading_ports[des_contract_id][0]
        # Minimum spread
        if sum(w[loading_port,t,des_contract_id] for t in loading_days if t >= loading_day and t < loading_day+minimum_spread)+ 1 > 1:
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


def set_initial_solution(model, solution):

    # This function should not return anything I think

    0


def check_if_solution_is_feasible(solution_is_feasible):

    this = 0

    if this:
        solution_is_feasible = True