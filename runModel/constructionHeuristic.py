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

    upper_charter_amount = 170000
    lower_charter_amount = 125000

    x = x1.copy()
    z = z1.copy()
    s = s1.copy()
    w = w1.copy()
    g = g1.copy()

    # Setting all arcs except the arcs indicating the vessel is not used to zero
    for (vessel, port1, day1, port2, day2), value in x.items():
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
            for day in loading_days:
                if day in fob_days[fob_contract_id]:
                    fob_amount = fob_demands[fob_contract_id]
                    if check_feasible_fob_move(day, loading_days, s, fob_loading_port, fob_amount, min_inventory, w, z, 
                        number_of_berths, fob_loading_ports, fob_contract_id):
                        z[fob_contract_id, day] = 1
                        update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                        amount_picked_up[fob_contract_id] = fob_amount
                        fob_satisfied = True
                        break
    # Demand is not satisfied for all contracts yet
    demand_is_satisfied = False

    # Starting setting g-variables t
    while not demand_is_satisfied:
        for des_contract in des_contract_ids:
            des_loading_port = des_loading_ports[des_contract][0]
            amount_chartered = {partition:0 for partition in des_contract_partitions[des_contract]}
            for partition in des_contract_partitions[des_contract]:
                count = 0
                while amount_chartered[partition] < lower_partition_demand[des_contract,partition]:
                    count += 1
                    if count > 1:
                        reset_g_vars(g_altered_vars, g, w)
                        amount_chartered = calculate_total_demand_delivered(des_contract, des_contract_partitions,
                                                    sailing_time_charter,partition_days, g)
                        update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                    g_altered_vars = []
                    for day in loading_days:
                        if day+sailing_time_charter[des_loading_port, des_contract] in partition_days[partition]:
                            charter_amount = random.randrange(lower_charter_amount, upper_charter_amount)
                            if check_feasible_charter_move(day, partition, des_contract, des_loading_port, charter_amount, min_inventory, s, w,
                            number_of_berths, minimum_spread, amount_chartered, upper_partition_demand, loading_days, fob_loading_ports, z):
                                g[des_loading_port, day, des_contract] = charter_amount
                                w[des_loading_port, day, des_contract] = 1
                                g_altered_vars.append((des_loading_port, day, des_contract))
                                update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                                amount_chartered = calculate_total_demand_delivered(des_contract, des_contract_partitions,
                                                    sailing_time_charter,partition_days, g)
                                #print(f'DES demand for {partition} updated, amount chartered: {amount_chartered[partition]}')
                                demand_is_satisfied = check_if_demand_is_satisfied(amount_chartered, des_contract, lower_partition_demand)

    for (loading_port, day), value in s.items():
        print(loading_port, day, value)
    
    for (loading_port, day), value in s.items():
        if value > max_inventory[loading_port]:
            for fake_fob_loading_port, fake_fob in fob_spot_art_ports.items():
                if fake_fob_loading_port==loading_port:
                    z[fake_fob, day] = 1
                    update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
    
    
    for (loading_port, day), value in s.items():
        print(loading_port, day, value)
    
    for (i,t,j), value in g.items():
        if value != 0:
            print(i,t,j, value)

    for (f,t), value in z.items():
        if value != 0:
            print(f,t, value)

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
    
    for partition, value in amount_chartered.items():
        if value < lower_partition_demand[des_contract,partition]:
            return False
    #print(f'Finishing finding demand for partition: {partition}, with {amount_chartered[partition]}')
    return True


# Checks if new charter variable is feasible
def check_feasible_charter_move(day, partition, des_contract, des_loading_port, charter_amount, min_inventory, s, w,
    number_of_berths, minimum_spread, amount_chartered, upper_partition_demand, loading_days, fob_loading_ports, z):

    # inventory constraints, never below minimum inventory
    for t in range(day, loading_days[-1]+1):
        if s[des_loading_port, t] - charter_amount < min_inventory[des_loading_port]:
            # print('inventory problems')
            return False
    
    # berth constraints for the loading port, never more than number of berth g vars per day
    if (sum(value for (i,t,j), value in w.items() if i ==des_loading_port and t == day)+sum(value for (z,t), value
    in z.items() if des_loading_port in fob_loading_ports[z] and t == day)+1 > number_of_berths[des_loading_port]):
        # print('berth problems')
        return False
    
    # minimum spread, assumes that there is one charter boat with one speed and therefore can look at t
    if sum(value for (i,t,j), value in w.items() if j == des_contract and t >= day and t <= day + minimum_spread) +1 > 1:
        # print('spread problems')
        return False
    
    # never above upper demand for partition
    if amount_chartered[partition] + charter_amount*0.9 > upper_partition_demand[des_contract, partition]:
        # print('inventory problems')
        return False

    else:
        return True



def check_feasible_fob_move(day, loading_days, s, fob_loading_port, fob_amount, min_inventory, w, z, 
    number_of_berths, fob_loading_ports, fob_contract_id):
    
    # inventory constraints, never below minimum inventory
    for t in range(day, loading_days[-1]+1):
        if s[fob_loading_port, t] - fob_amount < min_inventory[fob_loading_port]:
            print(f'inventory problems with fob_contract {fob_contract_id}, tried day {day}')
            return False
    
    # berth constraints for the loading port, never more than number of berth g vars per day
    if (sum(value for (i,t,j), value in w.items() if i == fob_loading_port and t == day)+sum(value for (z,t), value
    in z.items() if t==day and fob_loading_port in fob_loading_ports[z])+1 > number_of_berths[fob_loading_port]):
        print(f'berth problems with fob_contract {fob_contract_id}, tried day {day}')
        return False
    
    # constraints are not violated
    else:
        return True 



def reset_g_vars(g_altered_vars, g, w):
    for (i,t,j) in g_altered_vars:
        g[i,t,j] = 0
        w[i,t,j] = 0


def set_initial_solution(model, solution):

    # This function should not return anything I think

    0


def check_if_solution_is_feasible(solution_is_feasible):

    this = 0

    if this:
        solution_is_feasible = True