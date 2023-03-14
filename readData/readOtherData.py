import json
from datetime import datetime
from readData.readContractData import *
from readData.readLocationData import *
from readData.readVesselData import *
from supportFiles.constants import *
import itertools


def set_loading_port_ids(filename):
    
    customer = filename[0]
    if customer == 'N':
        return NIG
    
    elif customer == 'A':

        if filename[2]=='1':
            return ABU1
        elif filename[2]=='2':
            return ABU2
        else: 
            raise ValueError('Uknown number of loading ports')
    
    else: 
        raise ValueError('Unknown origin of data')


def read_data_file(group, filename):

    file = open(f'testData/{group}/{filename}.json')
    data = json.load(file)

    return data


def read_planning_horizion(data):

    loading_from_time = datetime.strptime(data['forecast']['fromDateTime'].split('T')[0], '%Y-%m-%d')
    loading_to_time = datetime.strptime(data['forecast']['toDateTime'].split('T')[0], '%Y-%m-%d')
    loading_days = [i for i in range(1,(loading_to_time-loading_from_time).days+2)]
    
    return loading_from_time, loading_to_time, loading_days


def set_distances(data):
    distances = {}
    for pair in data['network']['legDistances']:
        distances[(pair['fromNode'], pair['toNode'])] = pair['distance']

    return distances


def read_fake_fob(loading_port_ids, fob_ids, fob_spot_ids, fob_days, loading_days, port_types, fob_demands, fob_revenues, fake_fob_quantity):
    fob_spot_art_ports = {}
    for loading_port in loading_port_ids:
        fake_fob_id = f'ART_FIC_{loading_port}'
        fob_spot_art_ports[loading_port] = fake_fob_id
        fob_ids.append(fake_fob_id)
        fob_spot_ids.append(fake_fob_id)
        fob_days[fake_fob_id] = loading_days
        port_types[fake_fob_id] = 's'
        for t in loading_days:
            fob_demands[fake_fob_id] = fake_fob_quantity[loading_port]
            fob_revenues[fake_fob_id, t] = 0

    return fob_spot_art_ports


def set_fob_operational_times(fob_ids, loading_port_ids):
    fob_operational_times = {(f,j): 1 for f,j in list(itertools.product(fob_ids, loading_port_ids))}

    return fob_operational_times


def set_sailing_time_charter(loading_port_ids, spot_port_ids, des_contract_ids, distances, port_locations, charter_vessel_speed):
    sailing_time_charter = {(i, j): calculate_charter_sailing_time(i, j, distances, port_locations, charter_vessel_speed) for i in loading_port_ids for j in (spot_port_ids+des_contract_ids)}

    return sailing_time_charter


def set_charter_total_cost(sailing_time_charter, charter_vessel_prices, loading_port_ids, des_contract_ids, loading_days):
    charter_total_cost = {(i,t,j):sailing_time_charter[i,j]*charter_vessel_prices[t]*2 for i in loading_port_ids for j in des_contract_ids for t in loading_days}

    return charter_total_cost
