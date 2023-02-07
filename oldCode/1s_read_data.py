import json
import gurobipy as gp
from gurobipy import GRB
import itertools
import math
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from operator import itemgetter

"""
This file is for reading data and run the model for 1 loading port and speed optimization,
for a test instance
"""

filename = 't_1S_23V_120D_a'
group = '1S_23V_120D'

file = open(f'testData/{group}/{filename}.json')
data = json.load(file)

# Planning horizon, loading days
loading_from_time = datetime.strptime(data['forecast']['fromDateTime'].split('T')[0], '%Y-%m-%d')
loading_to_time = datetime.strptime(data['forecast']['toDateTime'].split('T')[0], '%Y-%m-%d')
loading_days = [i for i in range(1,(loading_to_time-loading_from_time).days+1)]

# Locations and ports sets
location_ids = []
location_names = {}
location_types = {}
location_ports = {}
port_types = {}
port_locations = {}

# All locations
for location in data['network']['ports']:
    location_ids.append(location['id'])
    location_names[location['id']] = location['name']

# Loading- and physical locations
loading_location_ids = loading_port_ids = ['NGBON']
unloading_location_ids = [location for location in location_ids if location not in loading_location_ids]
for u_id in unloading_location_ids:
    location_types[u_id] = 'u'
    location_ports[u_id] = []

# Loading port
min_inventory = {}
max_inventory = {}
initial_inventory = {}
number_of_berths = {}

for location in data['network']['ports']:
    if location['id'] in loading_port_ids:
        location_types[location['id']]='l'
        port_types[location['id']]='l'
        port_locations[location['id']] = location['id']
        location_ports[location['id']] = location['id']
        for info in location['export']['storages']:
            min_inventory[location['id']] = info['minSafeLimit']
            max_inventory[location['id']] = info['maxSafeLimit']
            initial_inventory[location['id']] = info['tankLevel'][0]['level']
            number_of_berths[location['id']] = len(info['compatibleBerths'])
            production_quantities = {(location['id'], day): info['production'][0]['rate'] for day in loading_days} # Pls fix
            fake_fob_quantity = info['defaultLoadingQuantity']

# Contracts/partitions
unloading_port_ids = []
des_contract_ids = []
des_contract_revenues = {}
des_contract_partitions = {}
partition_names = {}
partition_days = {}
upper_partition_demand = {}
lower_partition_demand = {}
des_biggest_partition = {}
des_biggest_demand = {}
fob_ids = []
fob_contract_ids = []
fob_revenues = {}
fob_demands = {}
fob_days = {}
fob_loading_port = 'NGBON' # hardkodet, fikser når vi får data
unloading_days = {}
last_day = loading_to_time

for contract in data['contracts']:
    last_unloading_day = loading_to_time
    earliest_unloading_day = loading_to_time
    # Defining ordinary contracts
    if contract['id'][:3]=='DES':
        des_contract_ids.append(contract['id'])
        des_contract_partitions[contract['id']] = []
        des_biggest_demand[contract['id']] = 0
        port_types[contract['id']] = 'u'
        port_locations[contract['id']] = contract['desRequests'][0]['portId']
        location_ports[contract['desRequests'][0]['portId']].append(contract['id'])
        for partition in contract['desRequests']:
            des_contract_partitions[contract['id']].append(partition['id'])
            partition_names[partition['id']] = partition['name']
            upper_partition_demand[contract['id'], partition['id']] = partition['quantity']
            lower_partition_demand[contract['id'], partition['id']] = partition['minQuantity']
            if (partition['minQuantity']> des_biggest_demand[contract['id']]):
                des_biggest_demand[contract['id']] = partition['minQuantity']
                des_biggest_partition[contract['id']] = partition['id']
            partition_from_time = datetime.strptime(partition['from'].split('T')[0], '%Y-%m-%d') # Start time of contract
            if partition_from_time < earliest_unloading_day:
                earliest_unloading_day = partition_from_time
            elif partition_from_time > last_unloading_day:
                id = partition['id']
                raise ValueError(f'There is a contract that starts after last unloading day ({id}), fix data')
            partition_to_time = datetime.strptime(partition['to'].split('T')[0], '%Y-%m-%d') # End time of contract
            if partition_to_time>last_unloading_day:
                last_unloading_day = partition_to_time
            partition_start_time = (partition_from_time-loading_from_time).days
            partition_delta_time = (partition_to_time-partition_from_time).days
            if partition_start_time < 0:
                partition_start_time = 0 
            partition_days[partition['id']] = [
                i for i in range(partition_start_time+1,partition_start_time+partition_delta_time+1)]
        if(last_unloading_day>last_day):
            last_day=last_unloading_day
        unloading_days[contract['id']] = [i for i in range((earliest_unloading_day-loading_from_time).days,
        (earliest_unloading_day-loading_from_time).days + (last_unloading_day-earliest_unloading_day).days)]
        if len(contract['salesPrices'])==1:
            for t in unloading_days[contract['id']]:
                des_contract_revenues[contract['id'], t] = contract['salesPrices'][0]['price']
        else: 
            for price in contract['salesPrices']:
                price_from_time = datetime.strptime(price['fromDateTime'].split('T')[0], '%Y-%m-%d')
                if price_from_time < earliest_unloading_day:
                    price_from_time = earliest_unloading_day
                price_start_time = (price_from_time-earliest_unloading_day).days
                for t in unloading_days[contract['id']]:
                    des_contract_revenues[contract['id'], t] = price['price']
    elif contract['id'][:3]=='FOB':
        for partition in contract['fobRequests']:
            fob_ids.append(partition['id'])
            fob_contract_ids.append(partition['id'])
            fob_demands[partition['id']] = partition['quantity']
            partition_from_time = datetime.strptime(partition['from'].split('T')[0], '%Y-%m-%d') # Start time of contract
            partition_to_time = datetime.strptime(partition['to'].split('T')[0], '%Y-%m-%d') # End time of contract
            partition_start_time = (partition_from_time-loading_from_time).days
            partition_delta_time = (partition_to_time-partition_from_time).days
            if partition_start_time < 0:
                partition_start_time = 0
            fob_days[partition['id']] = [
                i for i in range(partition_start_time+1,partition_start_time+partition_delta_time+1)]
            if len(contract['salesPrices'])==1:
                for t in fob_days[partition['id']]:
                    fob_revenues[partition['id'], t] = contract['salesPrices'][0]['price']
            else: 
                for price in contract['salesPrices']:
                    price_from_time = datetime.strptime(price['fromDateTime'].split('T')[0], '%Y-%m-%d')
                    if price_from_time < loading_from_time:
                        price_from_time = loading_from_time
                    price_start_time = (price_from_time-loading_from_time).days
                    for t in range(price_start_time+1, len(fob_days[partition['id']])+1):
                        fob_revenues[partition['id'], t] = price['price']

if len(des_contract_ids)!=len(set(des_contract_ids)):
    raise ValueError('There is duplicates in long-term DES contracts, fix data')

if len(fob_ids)!=len(set(fob_ids)):
    raise ValueError('There is duplicates in long-term FOB contracts, fix data')

last_unloading_day = last_day
last_day = (last_day-loading_from_time).days
all_days = [i for i in range(1, last_day+1)]

# Distances
distances = {} # Given with ports

for pair in data['network']['legDistances']:
    distances[(pair['fromNode'],pair['toNode'])] = pair['distance']

# Spot nodes
spot_port_ids = []
des_spot_ids = []
fob_spot_ids = []

# Hardkoding, fake fob
fob_spot_art_port = 'ART_FIC'
fob_ids.append(fob_spot_art_port)
fob_spot_ids.append(fob_spot_art_port)
fob_days[fob_spot_art_port] = loading_days
for t in loading_days:
    fob_demands[fob_spot_art_port] = fake_fob_quantity
    fob_revenues[fob_spot_art_port,t] = 0
port_types[fob_spot_art_port] = 's'

# Fob operational times
fob_operational_times = {
    (f,j): 1 for f,j in list(itertools.product(fob_ids, loading_port_ids))}

# Vessels 
vessel_ids = []
vessel_names = [vessel['id'] for vessel in data['vessels']]
vessel_available_days = {}
vessel_capacities = {}
vessel_start_ports = {}
vessel_min_speed = {}
vessel_max_speed = {}
vessel_ballast_speed_profile = {}
vessel_laden_speed_profile = {}
vessel_boil_off_rate = {}
vessel_location_acceptances = {vessel['id']: [] for vessel in data['vessels']}
vessel_port_acceptances = {vessel['id']: [] for vessel in data['vessels']}
maintenance_ids = []
maintenance_vessels = []
maintenance_vessel_ports = {}
maintenance_durations = {}
maintenance_start_times = {}
maintenance_end_times = {}

for vessel in data['vessels']:
    vessel_ids.append(vessel['id'])
    vessel_capacities[vessel['id']] = vessel['capacity']
    start_location = vessel['location'] # All vessels start in loading node??
    if len(location_ports[start_location])==0:
        start_port_id = vessel['id']+'-start'
        port_locations[start_port_id] = start_location
        location_ports[start_location].append(start_port_id)
        port_types[start_port_id] = 'u'
        vessel_start_ports[vessel['id']] = start_port_id
        vessel_location_acceptances[vessel['id']].append(start_location)
        vessel_port_acceptances[vessel['id']].append(start_port_id)
    else: 
        vessel_start_ports[vessel['id']] = location_ports[start_location][0]
        if start_location not in vessel_location_acceptances[vessel['id']]: #OBS
            vessel_location_acceptances[vessel['id']].append(start_location)
        if location_ports[start_location][0] not in vessel_port_acceptances[vessel['id']]:
            vessel_port_acceptances[vessel['id']].append(location_ports[start_location][0])
    for id in loading_port_ids: # Alle båtene er feasible med alle loading_nodes men kan sjekke
        vessel_port_acceptances[vessel['id']].append(id )
    vessel_min_speed[vessel['id']] = vessel['ladenSpeedProfile']['options'][0]['speed']
    vessel_max_speed[vessel['id']] = vessel['ladenSpeedProfile']['options'][-1]['speed']
    vessel_ballast_speed_profile[vessel['id']] = vessel['ballastSpeedProfile']['options']
    vessel_laden_speed_profile[vessel['id']] = vessel['ladenSpeedProfile']['options']
    vessel_boil_off_rate[vessel['id']] = 2*0.0015 #2*vessel['boilOffRate']
    vessel_from_time = datetime.strptime(vessel['from'].split('T')[0], '%Y-%m-%d')
    vessel_to_time = datetime.strptime(vessel['to'].split('T')[0], '%Y-%m-%d')
    if vessel_from_time < loading_from_time: # If defined before planning period
        vessel_from_time = loading_from_time
    vessel_start_time =(vessel_from_time-loading_from_time).days
    if vessel_to_time > loading_to_time: # If defined after planning period
        vessel_to_time  = loading_to_time
    vessel_delta_time = (vessel_to_time-vessel_from_time).days
    vessel_available_days[vessel['id']] = [
        i for i in range(vessel_start_time+1,vessel_start_time+vessel_delta_time+1)]
    if len(vessel_available_days[vessel['id']])==0:
        vessel_ids.remove(vessel['id'])
    for port in vessel['portAcceptance']:
        vessel_location_acceptances[vessel['id']].append(port['portId'])
    for contract in vessel['contractAcceptance']:
        if contract['contractId'] in des_contract_ids:
            for batch in data['contracts']:
                if batch['id']==contract['contractId'] and contract['contractId'] not in vessel_port_acceptances[vessel['id']]:
                    vessel_port_acceptances[vessel['id']].append(contract['contractId'])          
    for info in vessel:
        if info=='maintenances':
            for maintenance in vessel[info]:
                for port in data['network']['ports']:
                    if port['id']==maintenance['location']:
                        maintenance_id = vessel['id']+ '-M'
                        maintenance_ids.append(maintenance_id)
                        maintenance_vessels.append(vessel['id'])
                        maintenance_vessel_ports[vessel['id']] = maintenance_id
                        port_locations[maintenance_id] = maintenance['location']
                        port_types[maintenance_id] = 'm'
                        maintenance_start_date = datetime.strptime(maintenance['from'].split('T')[0],'%Y-%m-%d')
                        if (last_unloading_day-maintenance_start_date).days<0:
                            raise ValueError('Maintenance starts after the last unloading day, fix data')
                        maintenance_durations[maintenance_id] = maintenance['duration']
                        if maintenance_durations[maintenance_id]>(last_unloading_day-maintenance_start_date).days:
                            maintenance_durations[maintenance_id] =(last_unloading_day-maintenance_start_date).days
                        maintenance_start_times[vessel['id']] = (maintenance_start_date-loading_from_time).days + maintenance_durations[maintenance_id]                   

                                                
# Now all nodes is defined, should include des contract, des spot, loading and maintenance ports
node_ids = [node_id for node_id in port_locations]

# Charter vessel
charter_vessel_port_acceptances = {vessel['id']: [] for vessel in data['charterVessels']}
charter_vessel_node_acceptances = {vessel['id']: [] for vessel in data['charterVessels']}
charter_vessel_upper_capacity = 180000 #max(upper_partition_demand.values())
charter_vessel_lower_capacity = 100000 #min(lower_partition_demand.values())
charter_vessel_prices = {}

for charter in data['charterVessels']:
    charter_vessel_id = charter['id']
    charter_vessel_loading_quantity = charter['quantity']
    charter_vessel_speed = charter['speedProfile']['defaultSpeed']
    if len(charter['charterRates'])==1:
        for t in loading_days:
            charter_vessel_prices[t] = charter['charterRates'][0]['rate']
    else: 
        for price in charter['charterRates']:
            price_from_time = datetime.strptime(price['fromDateTime'].split('T')[0], '%Y-%m-%d')
            if price_from_time > loading_to_time:
                continue
            if price_from_time < loading_from_time:
                price_from_time = loading_from_time
            price_start_time = (price_from_time-loading_from_time).days
            for t in range(price_start_time+1, len(loading_days)+1):
                charter_vessel_prices[t] = price['rate']
    for id in loading_port_ids: # Alle båtene er feasible med alle loading_nodes men kan sjekke
        charter_vessel_node_acceptances[charter['id']].append(id )
    for port in charter['portAcceptance']:
        charter_vessel_port_acceptances[charter['id']].append(port['portId'])
    for contract in charter['contractAcceptance']:
        if contract['contractId'] in des_contract_ids:
            for batch in data['contracts']:
                if batch['id']==contract['contractId']:
                    charter_vessel_node_acceptances[charter['id']].append(contract['contractId'])

def calculate_charter_sailing_time(i, j):
    distance = distances[port_locations[i],port_locations[j]]
    time = np.ceil(distance/(charter_vessel_speed*24))
    return time

sailing_time_charter = {(i, j): calculate_charter_sailing_time(i,j) for i in loading_port_ids for j in (spot_port_ids+des_contract_ids)}
charter_total_cost = {(i,t,j):sailing_time_charter[i,j]*charter_vessel_prices[t]*2 for i in loading_port_ids for j in des_contract_ids for t in loading_days}

# Arcs
arc_speeds = {}
arc_waiting_times = {}
arc_saililng_times = {}
sailing_costs = {}

def set_operational_time(v,i,j):
    if maintenance_ids.__contains__(j): # If the boat sails to a maintenance node
        return maintenance_durations[j]
    elif maintenance_ids.__contains__(i): # If the boat sails frorm a maintenance node
        return 2
    # Legge inn at dersom distance (i,j) er over en viss grense må vi også legge til xtra op-time
    else:
        return 1

def get_daily_fuel(speed, vessel, i):
    if loading_port_ids.__contains__(i): # Laden speed profile
        lower_speed = vessel_min_speed[vessel]
        lower_fuel = vessel_laden_speed_profile[vessel][0]['fuelConsumption']
        for laden_speed in vessel_laden_speed_profile[vessel][1:]:
            if speed > laden_speed['speed']:
                lower_speed = laden_speed['speed']
                lower_fuel = laden_speed['fuelConsumption']
            elif speed == laden_speed['speed']:
                return laden_speed['fuelConsumption']
            else: 
                interpol_fuel = np.interp(speed, [lower_speed, laden_speed['speed']], [lower_fuel, laden_speed['fuelConsumption']])
                return interpol_fuel
    else: # Ballast speed profile
        lower_speed = vessel_min_speed[vessel]
        lower_fuel = vessel_ballast_speed_profile[vessel][0]['fuelConsumption']
        for ballast_speed in vessel_ballast_speed_profile[vessel][1:]:
            if speed > ballast_speed['speed']:
                lower_speed = ballast_speed['speed']
                lower_fuel = ballast_speed['fuelConsumption']
            elif speed == ballast_speed['speed']:
                return ballast_speed['fuelConsumption']
            else:
                interpol_fuel = np.interp(speed, [lower_speed, ballast_speed['speed']], [lower_fuel, ballast_speed['fuelConsumption']])
                return interpol_fuel

def get_maintenance_arcs(vessel):
    maintenance_arcs = []
    for unloading in vessel_port_acceptances[vessel]:
        if des_contract_ids.__contains__(unloading):
            for t in range(vessel_available_days[vessel][0], maintenance_start_times[vessel]+1):
                m_to_arc = (vessel, unloading, t, maintenance_vessel_ports[vessel], maintenance_start_times[vessel])
                distance = distances[port_locations[unloading],port_locations[maintenance_vessel_ports[vessel]]]
                operational_time = maintenance_durations[maintenance_vessel_ports[vessel]]
                sailing_waiting_time = maintenance_start_times[vessel]-t-operational_time
                if ((sailing_waiting_time>0) and (distance/(sailing_waiting_time*24) <= vessel_max_speed[vessel])):
                    estimated_speed = distance/(sailing_waiting_time*24)
                    exit_arc = (vessel,maintenance_vessel_ports[vessel],maintenance_start_times[vessel],0,all_days[-1]+1)
                    if estimated_speed >= vessel_min_speed[vessel]:
                        arc_speeds[m_to_arc] = math.floor(estimated_speed)
                        arc_waiting_times[m_to_arc] = 0
                        arc_saililng_times[m_to_arc] = sailing_waiting_time
                        sailing_costs[m_to_arc] = sailing_waiting_time*(get_daily_fuel(estimated_speed,vessel,unloading))*fuel_price
                        maintenance_arcs.append(m_to_arc)
                        if exit_arc not in maintenance_arcs:
                            maintenance_arcs.append(exit_arc)
                            sailing_costs[exit_arc]=0
                    else: 
                        estimated_waiting = sailing_waiting_time-math.floor(distance/(vessel_min_speed[vessel]*24))
                        if estimated_waiting <= allowed_waiting:
                            arc_waiting_times[m_to_arc] = estimated_waiting
                            arc_saililng_times[m_to_arc] = sailing_waiting_time-estimated_waiting
                            maintenance_arcs.append(m_to_arc)
                            arc_speeds[m_to_arc] = vessel_min_speed
                            sailing_costs[m_to_arc] = (math.floor(distance/(vessel_min_speed[vessel]*24)))*(get_daily_fuel(vessel_min_speed[vessel], vessel, unloading))*fuel_price
                            maintenance_arcs.append(m_to_arc)
                            if exit_arc not in maintenance_arcs:
                                maintenance_arcs.append(exit_arc)
                                sailing_costs[exit_arc]=0
    for loading in loading_port_ids:
        if maintenance_start_times[vessel]==all_days[-1]:
            exit_arc = (vessel,maintenance_vessel_ports[vessel],all_days[-1],0,all_days[-1]+1)
            if exit_arc not in maintenance_arcs:
                maintenance_arcs.append(exit_arc)
                sailing_costs[exit_arc]=0
        else:
            for t in range(maintenance_start_times[vessel], len(unloading_days)):
                m_from_arc = (vessel, maintenance_vessel_ports[vessel], maintenance_start_times[vessel]+1, loading, t)
                distance = distances[port_locations[maintenance_vessel_ports[vessel], loading]]
                operational_time = operational_times[vessel, maintenance_vessel_ports[vessel],loading]
                sailing_waiting_time = t-maintenance_start_times[vessel]
                if ((sailing_waiting_time>0) and (distance/(sailing_waiting_time*24) <= vessel_max_speed[vessel])):
                    estimated_speed = distance/(sailing_waiting_time*24)
                    if estimated_speed >= vessel_min_speed[vessel]:
                        arc_speeds[m_from_arc] = math.floor(estimated_speed)
                        arc_waiting_times[m_from_arc] = 0
                        arc_saililng_times[m_from_arc] = sailing_waiting_time
                        sailing_costs[m_from_arc] = sailing_waiting_time*(get_daily_fuel(estimated_speed,vessel,maintenance_vessel_ports[vessel]))*fuel_price
                        maintenance_arcs.append(m_from_arc)
                    else: 
                        estimated_waiting = sailing_waiting_time-math.floor(distance/(vessel_min_speed[vessel]*24))
                        if estimated_waiting <= allowed_waiting:
                            arc_waiting_times[m_from_arc] = estimated_waiting
                            arc_saililng_times[m_from_arc] = sailing_waiting_time-estimated_waiting
                            maintenance_arcs.append(m_from_arc)
                            arc_speeds[m_from_arc] = vessel_min_speed[vessel]
                            sailing_costs[m_from_arc] = (math.floor(distance/(vessel_min_speed[vessel]*24)))*(get_daily_fuel(vessel_min_speed[vessel], vessel, maintenance_vessel_ports[vessel]))*fuel_price
                        maintenance_arcs.append(m_from_arc)
                
    maintenance_arcs = list(set(maintenance_arcs))
    return sorted(maintenance_arcs, key=itemgetter(2,4))
            
fuel_price = data['products'][1]['prices'][0]['price']
operational_times = {(v,i,j): set_operational_time(v,i,j) for v,i,j in list(itertools.product(vessel_ids, node_ids, node_ids))}
charter_boil_off = 0.0012 # Hardkodet 
tank_leftover_value={'NGBON':40} # Hardkodet
allowed_waiting = 7
total_feasible_arcs = []

def find_feasible_arcs(vessel, allowed_waiting):
    feasible_arcs = []
    # Arc from artificial node
    feasible_arcs.append((vessel,'ART_START',0,vessel_start_ports[vessel], vessel_available_days[vessel][0]))
    sailing_costs[(vessel,'ART_START',0,vessel_start_ports[vessel], vessel_available_days[vessel][0])] = 0
    arc_saililng_times[(vessel,'ART_START',0,vessel_start_ports[vessel], vessel_available_days[vessel][0])] = 0
    # Arc indicating that a vessel is not used
    feasible_arcs.append((vessel,'ART_START',0,'ART_START',all_days[-1]+1))
    sailing_costs[(vessel,'ART_START',0,'ART_START',all_days[-1]+1)] = 0
    arc_saililng_times[(vessel,0,0,0,all_days[-1]+1)]=0
    # exit_arcs[vessel].append((vessel,0,0,0,all_days[-1]+1))
    if maintenance_vessels.__contains__(vessel):
        maintenance_arcs = get_maintenance_arcs(vessel)
        feasible_arcs.extend(maintenance_arcs)
    port_alternatives = {}
    for t in (vessel_available_days[vessel]+[vessel_available_days[vessel][-1]+1]):
        port_alternatives[t] = []
    for t in (vessel_available_days[vessel]+[vessel_available_days[vessel][-1]+1]):
        if t==vessel_available_days[vessel][0]:
            port_alternatives[t].append(vessel_start_ports[vessel])
        for i in vessel_port_acceptances[vessel]:
            if i in port_alternatives[t]:
                for j in vessel_port_acceptances[vessel]:
                    # Cannot travel to node of same type
                    if port_types[i]==port_types[j]:
                        continue
                    # Cannot travel from loading node to maintenance node, feasible the other way
                    if (loading_port_ids.__contains__(i) and maintenance_ids.__contains__(j)):
                        continue
                    # Cannot travel from maintenance node to unloading node
                    if (maintenance_ids.__contains__(i) and des_contract_ids.__contains__(j)):
                        continue
                    # Cannot travel from unloading to spot or from spot to unloading
                    if (des_contract_ids.__contains__(i or j) and spot_port_ids.__contains__(i or j)):
                        continue
                    for t_ in range(t+1, min(t+65,len(all_days))):
                        if loading_port_ids.__contains__(j) and t_>len(loading_days)+1:
                            continue
                        a = (vessel, i, t, j, t_)
                        distance = distances[port_locations[i],port_locations[j]]
                        arc_operational_time = operational_times[vessel,i,j]
                        sailing_waiting_time = t_-t-arc_operational_time
                        if ((sailing_waiting_time>0) and (distance/(sailing_waiting_time*24) <= vessel_max_speed[vessel])):
                            estimated_speed = distance/(sailing_waiting_time*24)
                            exit_arc = (vessel,j,t_,'ART_START',all_days[-1]+1)
                            if estimated_speed >= vessel_min_speed[vessel]:
                                arc_speeds[a] = math.floor(estimated_speed)
                                arc_waiting_times[a] = 0
                                arc_saililng_times[a] = sailing_waiting_time
                                sailing_costs[a] = sailing_waiting_time*(get_daily_fuel(estimated_speed,vessel,i))*fuel_price
                                feasible_arcs.append(a)
                                if (exit_arc not in feasible_arcs) and (not loading_port_ids.__contains__(j)):
                                    feasible_arcs.append(exit_arc)
                                    sailing_costs[exit_arc]=0
                                    arc_saililng_times[exit_arc]=0
                            else: 
                                estimated_waiting = sailing_waiting_time-math.floor(distance/(vessel_min_speed[vessel]*24))
                                if estimated_waiting <= allowed_waiting:
                                    arc_waiting_times[a] = estimated_waiting
                                    arc_saililng_times[a] = sailing_waiting_time-estimated_waiting
                                    feasible_arcs.append(a)
                                    arc_speeds[a] = vessel_min_speed[vessel]
                                    sailing_costs[a] = (math.floor(distance/(vessel_min_speed[vessel]*24)))*(get_daily_fuel(vessel_min_speed[vessel], vessel, i))*fuel_price
                                    if (exit_arc not in feasible_arcs) and (not loading_port_ids.__contains__(j)):
                                        feasible_arcs.append(exit_arc)
                                        sailing_costs[exit_arc]=0
                                        arc_saililng_times[exit_arc]=0
                            if t_ in loading_days:
                                port_alternatives[t_].append(j)
    print(vessel + ' number of arcs:' +str(len(feasible_arcs)))
    total_feasible_arcs.extend(feasible_arcs)
    return feasible_arcs


vessel_feasible_arcs = {vessel: find_feasible_arcs(vessel, allowed_waiting) for vessel in vessel_ids}

#total_feasible_arcs = list(set(functools.reduce(lambda l1, l2: l1+l2, list(vessel_feasible_arcs.values()))))

# Model
model = gp.Model()

# Variables
x = model.addVars(total_feasible_arcs, vtype='B', name='x')

fob_dimensions = [(f,t) for f in fob_ids for t in fob_days[f]] # Each fob contract has a specific loading node 
z = model.addVars(fob_dimensions, vtype ='B', name='z')

charter_dimensions = [(i,t,j) for i in loading_port_ids for t in loading_days for j in (des_contract_ids + spot_port_ids)]
w = model.addVars(charter_dimensions, vtype ='B', name='w')

g = model.addVars(charter_dimensions, vtype='C', name='g')

s = model.addVars(production_quantities, vtype='C', name='s')


# Objective 5.1
# Ledd 1: FOB-spot hentet
# Ledd 2: DES-spot levert med egne vessels
# Ledd 3: DES-spot levert med charter
# Ledd 4: Inntekt fra tank left-over value
# Ledd 5: Over-delivery-inntekt fra faste kontrakter
# Ledd 6: Transportkostnader for egne vessels
# Ledd 7: Kostnader av å bruke charter

model.setObjective(
    (gp.quicksum(fob_revenues[f,t]*fob_demands[f]*z[f,t] 
    for f in fob_ids for t in fob_days[f]) + 
    gp.quicksum(des_contract_revenues[j,t_]*vessel_capacities[v]*(1-(t_-t)*vessel_boil_off_rate[v])*x[v,i,t,j,t_] 
    for v in vessel_ids for i in loading_port_ids for t in loading_days for j in spot_port_ids for t_ in all_days 
    if (v,i,t,j,t_) in x.keys()) + 
    gp.quicksum(des_contract_revenues[j,min(t+sailing_time_charter[i,j], len(unloading_days[j]))]*g[i,t,j]*(1-sailing_time_charter[i,j]*charter_boil_off)
    for i in loading_port_ids for j in spot_port_ids for t in unloading_days[j]) + 
    gp.quicksum(tank_leftover_value[i]*s[i, len(loading_days)] for i in loading_port_ids) +
    gp.quicksum(vessel_capacities[v]*(1-(t_-t)*vessel_boil_off_rate[v])*des_contract_revenues[j,t_]*x[v,i,t,j,t_]
    for j in des_contract_ids for v in vessel_ids for i in loading_port_ids for t in vessel_available_days[v] for t_ in unloading_days[j] # Left-hand sums
    if (v,i,t,j,t_) in x.keys()) + 
    gp.quicksum(g[i,t,j]*(1-sailing_time_charter[i,j]*charter_boil_off)*des_contract_revenues[j,t+sailing_time_charter[i,j]] 
    for j in des_contract_ids for i in loading_port_ids for t in loading_days if (t+sailing_time_charter[i,j]) in unloading_days[j])-
    gp.quicksum(sailing_costs[v,i,t,j,t_]*x[v,i,t,j,t_] for v,i,t,j,t_ in x.keys())-
    gp.quicksum(charter_total_cost[i,t,j]*w[i,t,j] for i in loading_port_ids for t in loading_days for j in (des_contract_ids+des_spot_ids)))
    ,GRB.MAXIMIZE)


# Constraint 5.2
model.addConstrs(
    (s[i,t]==initial_inventory[i]+production_quantities[i,t]-gp.quicksum(vessel_capacities[v]*x[v,i,t,j,t_] 
    for v in vessel_ids for j in des_contract_ids for t_ in all_days if (v,i,t,j,t_) in x.keys())
    - gp.quicksum(g[i,t,j] for j in des_contract_ids)
    - gp.quicksum(fob_demands[f]*z[f,t] 
    for f in fob_ids if (f,t) in z.keys())
    for i in loading_port_ids for t in loading_days[:1]), name='initital_inventory_control')


# Constraint 5.3
model.addConstrs(
    (s[i,t]==s[i,(t-1)]+production_quantities[i,t]-gp.quicksum(vessel_capacities[v]*x[v,i,t,j,t_] 
    for v in vessel_ids for j in des_contract_ids for t_ in all_days if (v,i,t,j,t_) in x.keys())
    - gp.quicksum(g[i,t,j] for j in des_contract_ids)
    - gp.quicksum(fob_demands[f]*z[f,t] 
    for f in (fob_ids) if (f,t) in z.keys())
    for i in loading_port_ids for t in loading_days[1:]), name='inventory_control')


# Constraint 5.4
model.addConstrs((s[i,t] <= max_inventory[i] for i,t in s.keys()),name='upper_inventory')
model.addConstrs((min_inventory[i] <= s[i,t] for i,t in s.keys()),name='lower_inventory')

# Constraint 5.5
model.addConstrs((x.sum(v,'*','*',maintenance_vessel_ports[v],'*') == 1 for v in maintenance_vessels),name='maintenance')

# Constraint 5.6
model.addConstrs((x.sum(v,'*', [0]+all_days[:t],j,t)== x.sum(v,j,t,'*',all_days[t+1:]+[all_days[-1]+1]) for v in vessel_ids for j in node_ids for t in all_days), name='flow')


# Constraint 5.61
model.addConstrs((x[v,'ART_START',0,vessel_start_ports[v],vessel_available_days[v][0]]+x[v,'ART_START',0,'ART_START',all_days[-1]+1]==1 for v in vessel_ids), name='artificial_node')


# Constraint 5.7
a = model.addConstrs((gp.quicksum(vessel_capacities[v]*(1-(t_-t)*vessel_boil_off_rate[v])*x[v,i,t,j,t_]
    for v in vessel_ids for i in node_ids for t in loading_days for t_ in partition_days[p] # Left-hand sums
    if (v,i,t,j,t_) in x.keys()) +
     gp.quicksum(g[i,t,j]*(1-sailing_time_charter[i,j]*charter_boil_off) 
    for i in loading_port_ids for t in loading_days if t+sailing_time_charter[i,j] in partition_days[p]) # Only if the arc is feasible
    <=upper_partition_demand[j,p] #
    for j in des_contract_ids for p in des_contract_partitions[j]), name='upper_demand')
model.addConstrs((
    lower_partition_demand[j,p]<=(gp.quicksum(vessel_capacities[v]*(1-(t_-t)*vessel_boil_off_rate[v])*x[v,i,t,j,t_]
    for v in vessel_ids for i in node_ids for t in loading_days for t_ in partition_days[p] # Left-hand sums
    if (v,i,t,j,t_) in x.keys())
    +gp.quicksum(g[i,t,j]*(1-sailing_time_charter[i,j]*charter_boil_off) for i in loading_port_ids for t in loading_days 
    if t+sailing_time_charter[i,j] in partition_days[p])) # Only if the arc is feasible
    for j in des_contract_ids for p in des_contract_partitions[j]), name='lower_demand')


# Constraint 5.8
model.addConstrs(
    (z.sum(f,fob_days[f])==1 for f in fob_contract_ids), name = 'fob_max_contracts')


# Constraint 5.9
model.addConstrs((z.sum(f,fob_days[f])<=1 
for f in list(set(fob_spot_ids) - set([fob_spot_art_port]))) , name='fob_order')


# Constraint 5.11
model.addConstrs((gp.quicksum(x[v,i,t,j,tau] for v in vessel_ids for i in node_ids for t in loading_days 
for tau in range(t_,t_+operational_times[v,i,j]+1) if (v,i,t,j,tau) in x.keys())
+ gp.quicksum(w[j,t_,j_] for j_ in des_contract_ids)
+ gp.quicksum(z[f_v,j,f_tau] for f_v in fob_ids 
for f_tau in range(t_,t_+fob_operational_times[f_v,j]) if (f_v,j,f_tau) in x.keys())
<=number_of_berths[j] for j in loading_port_ids for t_ in loading_days),name='berth_constraint')


# Constraint 5.12 
model.addConstrs((charter_vessel_lower_capacity*w[i,t,j]<= g[i,t,j] for i in loading_port_ids for t in loading_days 
for j in (spot_port_ids+des_contract_ids)), name='charter_lower_capacity')
model.addConstrs((g[i,t,j]<=(charter_vessel_upper_capacity)*w[i,t,j] for i in loading_port_ids for t in loading_days
for j in (spot_port_ids+des_contract_ids)), name='charter_upper_capacity')


# Solve model
model.setParam('TimeLimit', 3*60*60)
model.setParam('LogFile', f'solution/{group}/{filename}.log')
model.optimize()
#model.computeIIS()
#model.write("solution/model.ilp")

# Variables saved
vessel_solution_arcs = {(vessel): [] for vessel in vessel_ids}
loading_port_inventory = {(loading_port): [] for loading_port in loading_port_ids}  
charter_cargoes = {(loading_port): [] for loading_port in loading_port_ids}
fob_deliveries = {}
fob_deliveries[fob_spot_art_port]=[]
for var in model.getVars():
    if var.x != 0:
        if var.varName[0]=='x':
            arc = var.varName[6:-1].split(',')
            #arc[1], arc[3] = int(arc[1]), int(arc[3])
            #arc = [arc[i] for i in [1,3,0,2]]
            vessel_solution_arcs[var.varName[2:5]].append(arc)
        elif var.varName[0]=='s':
            loading_port, day = var.varName[2:-1].split(',')
            loading_port_inventory[loading_port].append((int(day),var.x))
        elif var.varName[0]=='g':
            day, customer = var.varName[8:-1].split(',')
            amount = var.x
            charter_cargoes[var.varName[2:7]].append((int(day), customer, amount))
        elif var.varName[0]=='z': 
            customer, day = var.varName[2:-1].split(',')
            if customer==fob_spot_art_port:
                fob_deliveries[customer].append((int(day), fob_demands[customer]))
            else :
                fob_deliveries[customer]=((int(day), fob_demands[customer]))
        else: 
            continue
            

with open(f'solution/{group}/{filename}_x.json', 'w') as f:
    for vessel in vessel_solution_arcs:
        vessel_solution_arcs[vessel] = sorted(vessel_solution_arcs[vessel], key=itemgetter(0))
    json.dump(vessel_solution_arcs, f)

with open(f'solution/{group}/{filename}_s.json', 'w') as f:
    json.dump(loading_port_inventory,f)

with open(f'solution/{group}/{filename}_g.json', 'w') as f:
    json.dump(charter_cargoes, f)

with open(f'solution/{group}/{filename}_z.json', 'w') as f:
    json.dump(fob_deliveries,f)
            
for v in model.getVars():
    if v.x!=0:
        print(v.varName, v.x)

        
"""
#PLOTTING 

for v in model.getVars():
    #print('Var: ', v.x) # v.x is a float
    #print('Variable Name: ', v.varName) # v.varName is a string
    # FIKS PLOTT:
    # MAKING A LIST OUT OF VARIABLE NAME SO WE CAN PLOT:
    if round(v.x,0) == 1.0:
        split = v.varName.split(",")
        split2 = []
        done_splitting = []
        for i in split: 
            p = i.split("[")
            for e in p: 
                split2.append(e)
        for i in split2: 
            p = i.split("]")
            for e in p: 
                done_splitting.append(e)
        var_type = done_splitting[0]
        if var_type == 'x':
            arc_as_list = done_splitting[1:-1]
            arc_as_float_list = []
            #print("Arc_as_list: ", arc_as_list)
            for i in arc_as_list[0:2]:
                arc_as_float_list.append(i)
            for i in arc_as_list[2:3]:
                arc_as_float_list.append(float(i))
            for i in arc_as_list[3:4]:
                arc_as_float_list.append(i)
            for i in arc_as_list[4:]:
                arc_as_float_list.append(float(i))
            #print("Arc_as_float_list: ", arc_as_float_list)
            x_list = [arc_as_float_list[2],arc_as_float_list[4]] #[int(v.varName[4]),int(v.varName[6])]
            #print(x_list)
            y_list = [arc_as_float_list[1],arc_as_float_list[3]] #[int(v.varName[3]),int(v.varName[5])]
            #print(y_list)
            plt.plot(x_list,y_list, color = "lime", linewidth=1.8)
color = ["wheat", "skyblue", "darksalmon", "magenta","pink"]
i = 0
for vessel in vessel_ids:
    data = find_feasible_arcs(vessel,allowed_waiting)
    #print(data)
    for a in data:
        x_list = [a[2],a[4]]
        y_list = [a[1],a[3]]
        plt.plot(x_list,y_list, color = color[i], linewidth=0.4)
    if i > 3:
        i=0
    else: 
        i+=1
plt.xlim([0, (last_unloading_day-loading_from_time).days+1])
plt.ylim([0, 4])
plt.show()
#"""
