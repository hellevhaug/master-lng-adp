import numpy as np 

from datetime import datetime
from readData.readOtherData import *
from readData.readContractData import *
from readData.readLocationData import *
from supportFiles.constants import *

def initialize_vessel_sets(data):
    vessel_ids = []
    vessel_names = [vessel['id'] for vessel in data['vessels']]
    vessel_available_days = {}
    vessel_capacities = {}
    return vessel_ids, vessel_names, vessel_available_days, vessel_capacities 


def initialize_vessel_location_sets(data):
    vessel_start_ports = {}
    vessel_location_acceptances = {vessel['id']: [] for vessel in data['vessels']}
    vessel_port_acceptances = {vessel['id']: [] for vessel in data['vessels']}
    return vessel_start_ports,vessel_location_acceptances, vessel_port_acceptances


def initialize_vessel_speed_sets():
    vessel_min_speed = {}
    vessel_max_speed = {}
    vessel_ballast_speed_profile = {}
    vessel_laden_speed_profile = {}
    vessel_boil_off_rate = {}
    return vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, vessel_boil_off_rate


def initialize_maintenance_sets():
    maintenance_ids = []
    maintenance_vessels = []
    maintenance_vessel_ports = {}
    maintenance_durations = {}
    maintenance_start_times = {}
    maintenance_end_times = {}
    return maintenance_ids, maintenance_vessels, maintenance_vessel_ports, maintenance_durations, maintenance_start_times, maintenance_end_times

def initialize_charter_sets(data):
    charter_vessel_port_acceptances = {vessel['id']: [] for vessel in data['charterVessels']}
    charter_vessel_node_acceptances = {vessel['id']: [] for vessel in data['charterVessels']}
    charter_vessel_upper_capacity = CHARTER_VESSEL_UPPER_CAPACITY 
    charter_vessel_lower_capacity = CHARTER_VESSEL_LOWER_CAPACITY
    charter_vessel_prices = {}
    return charter_vessel_port_acceptances, charter_vessel_node_acceptances, charter_vessel_upper_capacity, charter_vessel_lower_capacity, charter_vessel_prices

def read_producer_vessels(data, vessel_ids, vessel_capacities, location_ports, port_locations, port_types, vessel_start_ports, vessel_location_acceptances,
                        vessel_port_acceptances, loading_port_ids, vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, 
                        vessel_boil_off_rate, vessel_available_days, loading_from_time, loading_to_time, maintenance_ids, maintenance_vessels, maintenance_vessel_ports, 
                        maintenance_start_times, maintenance_durations, last_unloading_day, des_contract_ids):
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
        vessel_delta_time = (vessel_to_time-vessel_from_time).days+1
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
                            if maintenance_durations[maintenance_id]>(last_unloading_day-maintenance_start_date).days +1 :
                                maintenance_durations[maintenance_id] =(last_unloading_day-maintenance_start_date).days +1
                            maintenance_start_times[vessel['id']] = (maintenance_start_date-loading_from_time).days + 1 + maintenance_durations[maintenance_id]
        
    return vessel_ids, vessel_capacities, location_ports, port_locations, port_types, vessel_start_ports, vessel_location_acceptances, vessel_port_acceptances, vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, vessel_boil_off_rate, vessel_available_days, maintenance_ids, maintenance_vessels, maintenance_vessel_ports, maintenance_start_times, maintenance_durations


def read_charter_vessels(data, loading_days, loading_from_time, loading_to_time, charter_vessel_prices, loading_port_ids, charter_vessel_node_acceptances, 
                        charter_vessel_port_acceptances, des_contract_ids):
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
    
    return charter_vessel_id, charter_vessel_loading_quantity, charter_vessel_speed, charter_vessel_prices, charter_vessel_node_acceptances, charter_vessel_port_acceptances


def calculate_charter_sailing_time(i, j, distances, port_locations, charter_vessel_speed):
    distance = distances[port_locations[i],port_locations[j]]
    time = np.ceil(distance/(charter_vessel_speed*24))
    return time


def set_minimum_charter_time():
    return MINIMUM_CHARTER_PERIOD

def set_charter_out_friction():
    return CHARTER_OUT_FRICTION

def scale_charter_out_prices(charter_vessel_prices, charter_out_friction):
    scaled_charter_out_prices = charter_vessel_prices.copy()
    for t in charter_vessel_prices.keys():
        scaled_charter_out_prices[t] = charter_vessel_prices[t]*charter_out_friction
    
    return scaled_charter_out_prices

def add_spot_to_vessel_acceptances(vessel_port_acceptances, des_spot_ids):
    for vessel, acceptances in vessel_port_acceptances.items():
        vessel_port_acceptances[vessel].extend(des_spot_ids)
