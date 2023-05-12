import random
from runModel.constructionHeuristic import *

###
## Creating some simple data
##

loading_days = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]
all_days = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]
loading_port_ids = ['lng_bonny']
des_contract_ids = ['des_contract_1', 'des_contract_2', 'des_contract_3']

des_contract_partitions = {'des_contract_1': ['des_part_11', 'des_part_12', 'des_part_13',],
                         'des_contract_2': ['des_part_21', 'des_part_22', 'des_part_23'],
                        'des_contract_3': ['des_part_31', 'des_part_32', 'des_part_33']}

lower_partition_demand = {('des_contract_1','des_part_11'): 0,('des_contract_1','des_part_12'):20,('des_contract_1','des_part_13'):40,
                         ('des_contract_2','des_part_21'): 0,('des_contract_2','des_part_22'):21,('des_contract_2','des_part_23'):45, 
                         ('des_contract_3','des_part_31'): 0,('des_contract_3','des_part_32'):26,('des_contract_3','des_part_33'):50,}

upper_partition_demand = {('des_contract_1','des_part_11'): 13,('des_contract_1','des_part_12'):39,('des_contract_1','des_part_13'):55,
                         ('des_contract_2','des_part_21'): 14,('des_contract_2','des_part_22'):38,('des_contract_2','des_part_23'):60, 
                         ('des_contract_3','des_part_31'): 13,('des_contract_3','des_part_32'):38,('des_contract_3','des_part_33'):62,}

partition_days = {'des_part_11': [1,2,3,4,5,6,7,8], 'des_part_12': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16], 'des_part_13':[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30],
                  'des_part_21': [1,2,3,4,5,6,7,8], 'des_part_22': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16], 'des_part_23':[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30],
                  'des_part_31': [1,2,3,4,5,6,7,8], 'des_part_32': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16], 'des_part_33':[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]}

fob_ids = ['fob_con_1','fob_con_2', 'fob_con_3', 'fob_con_4', 'fob_art_port']
fob_contract_ids = ['fob_con_1','fob_con_2', 'fob_con_3', 'fob_con_4']
fob_demands = {'fob_con_1': 9,'fob_con_2':8, 'fob_con_3':9, 'fob_con_4':8, 'fob_art_port':10}

fob_days = {'fob_con_1':[1,2,3,4,5,6],'fob_con_2':[7,8,9,10,11,12], 'fob_con_3':[13,14,15,16,17,18], 'fob_con_4':[19,20,21,22,23,24],'fob_art_port': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]}

min_inventory = {'lng_bonny': 5}
max_inventory = {'lng_bonny': 80}
initial_inventory = {'lng_bonny':15}
number_of_berths = {'lng_bonny':3}

production_quantities = {('lng_bonny',t):10 for t in loading_days} 
des_loading_ports = {contract:['lng_bonny'] for contract in des_contract_ids}
sailing_time_charter = {('lng_bonny', contract): 4 for contract in des_contract_ids}
fob_loading_ports = {contract:['lng_bonny'] for contract in fob_ids}
fob_spot_art_ports = ['fob_art_port']

minimum_spread =1
maintenance_vessels = []

z = {(f,t):0 for f in fob_ids for t in fob_days[f]}
s = {(i,t):0 for i in loading_port_ids for t in loading_days}
w = {(i,t,j):0 for j in des_contract_ids for i in des_loading_ports[j] for t in all_days if t + sailing_time_charter[i,j] in all_days}
g = {(i,t,j):0 for j in des_contract_ids for i in des_loading_ports[j] for t in all_days if t + sailing_time_charter[i,j] in all_days}

lower_charter_amount = 4
upper_charter_amount = 15

total_lng = 15 + len(loading_days)*10
print(f'Total produced LNG: {total_lng}')
total_demand_lng_fob = sum(fob_demands.values())
total_lower_demand_lng_des = 40+45+50
total_upper_demand_lng_des = 55+60+62
print(f'Total lower- and upper demand DES: {total_lower_demand_lng_des, total_upper_demand_lng_des}')

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

# Checking loading port inventory before 
for (loading_port, day), value in s.items():
        print(loading_port, day, value)
print('\n')

# Setting FOB, this works 
amount_picked_up = {fob_contract_id:0 for fob_contract_id in fob_contract_ids}
for fob_contract_id in fob_contract_ids:
    fob_satisfied = False
    fob_loading_port = fob_loading_ports[fob_contract_id][0]
    count = 0
    while not fob_satisfied:
        fob_random_loading_days = [i for i in loading_days if i in fob_days[fob_contract_id]]
        fob_random_loading_days = generate_random_loading_days(fob_random_loading_days)
        for day in fob_random_loading_days:
            if day in fob_days[fob_contract_id]:
                fob_amount = fob_demands[fob_contract_id]
                if check_feasible_fob_move(day, loading_days, s, fob_loading_port, fob_amount, min_inventory, w, z, 
                    number_of_berths, fob_loading_ports, fob_contract_id):
                    z[fob_contract_id, day] = 1
                    update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                    amount_picked_up[fob_contract_id] = fob_amount
                    fob_satisfied = True
                    break

print('\nFinished with FOB! Next: DES:) \n')

# Setting DES, this does not work yet
total_demand_is_satisfied = False
g_total_altered_vars = []
while not total_demand_is_satisfied:
    reset_g_vars(g_total_altered_vars, g, w)
    amount_chartered = {}
    random.shuffle(des_contract_ids)
    contract_count = 0
    for des_contract in des_contract_ids:
        demand_is_satisfied = False
        g_altered_contract_variables = []
        des_loading_port = des_loading_ports[des_contract][0]
        print(f'{des_contract}\n')
        amount_chartered[des_contract] = {partition: 0 for partition in des_contract_partitions[des_contract]}
        for partition in des_contract_partitions[des_contract]:
            print(partition)
            partition_count = 0
            amount_chartered[des_contract] = calculate_total_demand_delivered(des_contract, des_contract_partitions,
            sailing_time_charter,partition_days, g)
            partition_fulfilled = False
            while not partition_fulfilled or partition_count < 1:
                g_altered_partition_vars = []
                if partition_count >= 1:
                    reset_g_vars(g_altered_partition_vars, g, w)
                    g_total_altered_vars = [i for i in g_total_altered_vars if i not in g_altered_partition_vars]
                    g_total_contract_vars = [i for i in g_total_altered_vars if i not in g_altered_partition_vars]
                    amount_chartered[des_contract] = calculate_total_demand_delivered(des_contract, des_contract_partitions,
                    sailing_time_charter,partition_days, g)
                    update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                if partition_count > 50:
                    raise KeyError('Something is wrong')
                partition_count += 1
                partition_loading_days = [i for i in loading_days if i+sailing_time_charter[des_loading_port, des_contract] in partition_days[partition]]
                random_loading_days = generate_random_loading_days(partition_loading_days)
                for day in random_loading_days:
                    charter_amount = random.randrange(lower_charter_amount, upper_charter_amount)
                    if check_feasible_charter_move(day, partition, des_contract, des_loading_port, charter_amount, min_inventory, s, w,
                    number_of_berths, minimum_spread, amount_chartered, upper_partition_demand, loading_days, fob_loading_ports, z,
                    partition_days, sailing_time_charter):
                        print(f'Found feasible move for {des_contract}, for partition {partition} in day {day} with amount {charter_amount}')
                        g[des_loading_port, day, des_contract] = charter_amount
                        w[des_loading_port, day, des_contract] = 1
                        g_altered_partition_vars.append((des_loading_port, day, des_contract))
                        g_altered_contract_variables.append((des_loading_port, day, des_contract))
                        g_total_altered_vars.append((des_loading_port, day, des_contract))
                        update_inventory(s, all_days, initial_inventory, production_quantities, des_contract_ids, g, z, fob_ids, fob_demands)
                        amount_chartered[des_contract] = calculate_total_demand_delivered(des_contract, des_contract_partitions,
                                            sailing_time_charter,partition_days, g)
                        print(f'Showing amount chartered: \n')
                        print(f'{amount_chartered} \n')
                        demand_is_satisfied = check_if_demand_is_satisfied(amount_chartered, des_contract, lower_partition_demand)
                        if demand_is_satisfied:
                            contract_count += 1
                            print(f'{des_contract} fulfilled, {contract_count} \n\n')
                            print(f'Showing amount chartered: \n')
                            print(f'{amount_chartered} \n')
                            if contract_count == len(des_contract_ids):
                                total_demand_is_satisfied = True
                                print('\nAll contracts is fulfilled!')
                            break
                        if amount_chartered[des_contract][partition] >= lower_partition_demand[des_contract,partition]:
                            print(f'Partition {partition} is fulfilled, amound: {amount_chartered[des_contract][partition]}')
                            partition_fulfilled = True
                            break




print('(finished with FOB)')

# Checking what is set after FOB initialization
for (f,t), value in z.items():
    if value != 0:
        print(f,t, value)

