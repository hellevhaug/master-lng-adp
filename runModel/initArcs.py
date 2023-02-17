import numpy as np
import math
from operator import itemgetter
from supportFiles.constants import *

"""
File containting function for creating arcs
"""


# Initializing empty sets for arcs
def init_arc_sets():
    arc_speeds = {}
    arc_waiting_times = {}
    arc_sailing_times = {}
    sailing_costs = {}
    total_feasible_arcs = []
    return arc_speeds, arc_waiting_times, arc_sailing_times, sailing_costs, total_feasible_arcs


# Setting operational times for port combinations
def set_operational_time(v,i,j, maintenance_ids, maintenance_durations):
    if maintenance_ids.__contains__(j): # If the boat sails to a maintenance node
        return maintenance_durations[j]
    elif maintenance_ids.__contains__(i): # If the boat sails frorm a maintenance node
        return 2
    # Legge inn at dersom distance (i,j) er over en viss grense må vi også legge til xtra op-time
    else:
        return 1


# Calculating daily fuel consumption for a vessel given a speed
def get_daily_fuel(speed, vessel, i, loading_port_ids, vessel_min_speed, vessel_laden_speed_profile, vessel_ballast_speed_profile):
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


# Finding maintenance arcs for vessels needing maintenance
def get_maintenance_arcs(vessel, vessel_port_acceptances, des_contract_ids, vessel_available_days, maintenance_start_times, 
    maintenance_vessel_ports, distances, port_locations, maintenance_durations, vessel_max_speed, all_days, vessel_min_speed, arc_speeds, 
    arc_waiting_times, arc_sailing_times, sailing_costs, loading_port_ids, unloading_days, allowed_waiting, operational_times, fuel_price):
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
                        arc_sailing_times[m_to_arc] = sailing_waiting_time
                        sailing_costs[m_to_arc] = sailing_waiting_time*(get_daily_fuel(estimated_speed,vessel,unloading))*fuel_price
                        maintenance_arcs.append(m_to_arc)
                        if exit_arc not in maintenance_arcs:
                            maintenance_arcs.append(exit_arc)
                            sailing_costs[exit_arc]=0
                    else: 
                        estimated_waiting = sailing_waiting_time-math.floor(distance/(vessel_min_speed[vessel]*24))
                        if estimated_waiting <= allowed_waiting:
                            arc_waiting_times[m_to_arc] = estimated_waiting
                            arc_sailing_times[m_to_arc] = sailing_waiting_time-estimated_waiting
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
                        arc_sailing_times[m_from_arc] = sailing_waiting_time
                        sailing_costs[m_from_arc] = sailing_waiting_time*(get_daily_fuel(estimated_speed,vessel,maintenance_vessel_ports[vessel]))*fuel_price
                        maintenance_arcs.append(m_from_arc)
                    else: 
                        estimated_waiting = sailing_waiting_time-math.floor(distance/(vessel_min_speed[vessel]*24))
                        if estimated_waiting <= allowed_waiting:
                            arc_waiting_times[m_from_arc] = estimated_waiting
                            arc_sailing_times[m_from_arc] = sailing_waiting_time-estimated_waiting
                            maintenance_arcs.append(m_from_arc)
                            arc_speeds[m_from_arc] = vessel_min_speed[vessel]
                            sailing_costs[m_from_arc] = (math.floor(distance/(vessel_min_speed[vessel]*24)))*(get_daily_fuel(vessel_min_speed[vessel], vessel, maintenance_vessel_ports[vessel]))*fuel_price
                        maintenance_arcs.append(m_from_arc)
                
    maintenance_arcs = list(set(maintenance_arcs))
    return sorted(maintenance_arcs, key=itemgetter(2,4))


def set_external_data(data):
    fuel_price = data['products'][1]['prices'][0]['price']
    charter_boil_off = CHARTER_BOIL_OFF
    tank_leftover_value = TANK_LEFTOVER_VALUE
    allowed_waiting = ALLOWED_WAITING
    return fuel_price, charter_boil_off, tank_leftover_value, allowed_waiting


def find_feasible_arcs(vessel, allowed_waiting, vessel_start_ports, vessel_available_days, sailing_costs, arc_sailing_times, all_days, 
    maintenance_vessels, vessel_port_acceptances, port_types, loading_port_ids, maintenance_ids, des_contract_ids, distances, 
    spot_port_ids, loading_days, port_locations, vessel_max_speed, vessel_min_speed, arc_speeds, arc_waiting_times, operational_times,
    fuel_price, total_feasible_arcs, maintenance_start_times, maintenance_durations, maintenance_vessel_ports, unloading_days):
    feasible_arcs = []
    # Arc from artificial node
    feasible_arcs.append((vessel,'ART_START',0,vessel_start_ports[vessel], vessel_available_days[vessel][0]))
    sailing_costs[(vessel,'ART_START',0,vessel_start_ports[vessel], vessel_available_days[vessel][0])] = 0
    arc_sailing_times[(vessel,'ART_START',0,vessel_start_ports[vessel], vessel_available_days[vessel][0])] = 0
    # Arc indicating that a vessel is not used
    feasible_arcs.append((vessel,'ART_START',0,'ART_START',all_days[-1]+1))
    sailing_costs[(vessel,'ART_START',0,'ART_START',all_days[-1]+1)] = 0
    arc_sailing_times[(vessel,0,0,0,all_days[-1]+1)]=0
    # exit_arcs[vessel].append((vessel,0,0,0,all_days[-1]+1))
    if maintenance_vessels.__contains__(vessel):
        maintenance_arcs = get_maintenance_arcs(vessel, vessel_port_acceptances, des_contract_ids, vessel_available_days, maintenance_start_times, 
    maintenance_vessel_ports, distances, port_locations, maintenance_durations, vessel_max_speed, all_days, vessel_min_speed, arc_speeds, 
    arc_waiting_times, arc_sailing_times, sailing_costs, loading_port_ids, unloading_days, allowed_waiting, operational_times, fuel_price)
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
                                arc_sailing_times[a] = sailing_waiting_time
                                sailing_costs[a] = sailing_waiting_time*(get_daily_fuel(estimated_speed,vessel,i))*fuel_price
                                feasible_arcs.append(a)
                                if (exit_arc not in feasible_arcs) and (not loading_port_ids.__contains__(j)):
                                    feasible_arcs.append(exit_arc)
                                    sailing_costs[exit_arc]=0
                                    arc_sailing_times[exit_arc]=0
                            else: 
                                estimated_waiting = sailing_waiting_time-math.floor(distance/(vessel_min_speed[vessel]*24))
                                if estimated_waiting <= allowed_waiting:
                                    arc_waiting_times[a] = estimated_waiting
                                    arc_sailing_times[a] = sailing_waiting_time-estimated_waiting
                                    feasible_arcs.append(a)
                                    arc_speeds[a] = vessel_min_speed[vessel]
                                    sailing_costs[a] = (math.floor(distance/(vessel_min_speed[vessel]*24)))*(get_daily_fuel(vessel_min_speed[vessel], vessel, i))*fuel_price
                                    if (exit_arc not in feasible_arcs) and (not loading_port_ids.__contains__(j)):
                                        feasible_arcs.append(exit_arc)
                                        sailing_costs[exit_arc]=0
                                        arc_sailing_times[exit_arc]=0
                            if t_ in loading_days:
                                port_alternatives[t_].append(j)
    print(vessel + ' number of arcs:' +str(len(feasible_arcs)))
    total_feasible_arcs.extend(feasible_arcs)
    return feasible_arcs