import json
from datetime import datetime
from readData.readOtherData import *
from readData.readLocationData import *
from readData.readVesselData import *


unloading_port_ids = []

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


def read_all_contracts(data, port_types, port_locations, location_ports, loading_to_time, loading_from_time):
    for contract in data['contracts']:
        last_unloading_day = loading_to_time
        earliest_unloading_day = loading_to_time
        des_contract_ids = []
        des_contract_revenues = {}
        des_contract_partitions = {}
        # Defining ordinary contracts
        if contract['id'][:3]=='DES':
            port_types[contract['id']] = 'u'
            port_locations[contract['id']] = contract['desRequests'][0]['portId']
            location_ports[contract['desRequests'][0]['portId']].append(contract['id'])
            des_contract_ids.append(contract['id'])

            read_des_contract(data)
        elif contract['id'][:3]=='FOB':
            
    if len(des_contract_ids)!=len(set(des_contract_ids)):
        raise ValueError('There is duplicates in long-term DES contracts, fix data')

    if len(fob_ids)!=len(set(fob_ids)):
        raise ValueError('There is duplicates in long-term FOB contracts, fix data')

    return unloading_port_ids, des_contract_ids, des_contract_revenues, des_contract_partitions, \
    partition_names, partition_days, upper_partition_demand, lower_partition_demand, des_biggest_partition, \ 
    des_biggest_demand, fob_ids, fob_contract_ids, fob_revenues, fob_demands, fob_days, fob_loading_port = 'NGBON', 
unloading_days = {}
last_day = loading_to_time


def read_des_contract(contract, loading_from_time, des_contract_partitions, des_contract_revenues):
    des_contract_partitions[contract['id']] = []
    des_biggest_demand[contract['id']] = 0
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
    return 0


def read_fob_contract(data, contract, loading_from_time):
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

    return 0
