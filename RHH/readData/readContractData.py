import json
from datetime import datetime
from readData.readOtherData import *
from readData.readLocationData import *
from readData.readVesselData import *
from supportFiles.constants import *


# Might want to generalize fob_loading_port = 'NGBON', can check method in last years' work


def read_all_contracts(data, port_types, port_locations, location_ports, loading_to_time, loading_from_time):
    
    last_day = loading_to_time # unloading_to_time? Is is actually converted to las unloading day in read_des_contracts
    
    partition_names = {}
    partition_days = {}
    upper_partition_demand = {}
    lower_partition_demand = {}
    unloading_days = {}

    des_biggest_demand = {}
    des_biggest_partition = {}
    des_contract_ids = []
    des_contract_revenues = {}
    des_contract_partitions = {}

    fob_ids = []
    fob_contract_ids = []
    fob_revenues = {}
    fob_demands = {}
    fob_days = {}
    fob_loading_ports = {}

    for contract in data['contracts']:

        last_unloading_day = loading_to_time
        earliest_unloading_day = loading_to_time

        if contract['id'][:3]=='DES':

            port_types[contract['id']] = 'u'
            port_locations[contract['id']] = contract['desRequests'][0]['portId']
            location_ports[contract['desRequests'][0]['portId']].append(contract['id'])
            des_contract_ids.append(contract['id'])
            des_contract_partitions[contract['id']] = []
            des_biggest_demand[contract['id']] = 0
            partition_names, partition_days, contract, des_contract_partitions, des_contract_revenues, upper_partition_demand, \
            lower_partition_demand, des_biggest_partition, des_biggest_demand, last_day, last_unloading_day = read_des_contracts(contract, last_day, loading_from_time, partition_names, partition_days, upper_partition_demand, 
            lower_partition_demand, unloading_days, des_biggest_demand, des_biggest_partition, des_contract_revenues, 
            des_contract_partitions, earliest_unloading_day, last_unloading_day)
            if len(des_contract_partitions[contract['id']])!=len(set(des_contract_partitions[contract['id']])):
                contract_id = contract['id']
                raise ValueError(f'There is duplicates in long-term DES partitions for {contract_id}, fix data')

        elif contract['id'][:3]=='FOB':

            fob_ids, fob_contract_ids, fob_revenues, fob_demands, fob_days, fob_loading_ports = read_fob_contracts(contract, loading_from_time, fob_ids, fob_contract_ids, fob_demands, fob_days, fob_revenues, fob_loading_ports)

    if len(des_contract_ids)!=len(set(des_contract_ids)):
        raise ValueError('There is duplicates in long-term DES contracts, fix data')

    if len(fob_ids)!=len(set(fob_ids)):
        raise ValueError('There is duplicates in long-term FOB contracts, fix data')
    
    last_unloading_day = last_day
    last_day = (last_day-loading_from_time).days + 1
    all_days = [i for i in range(1, last_day+1)]

    return port_types, des_contract_ids, des_contract_revenues, des_contract_partitions, partition_names, partition_days, upper_partition_demand, lower_partition_demand, des_biggest_partition, des_biggest_demand, fob_ids, fob_contract_ids, fob_revenues, fob_demands, fob_days, fob_loading_ports, unloading_days, last_unloading_day, all_days


def read_des_contracts(contract, last_day, loading_from_time, partition_names, partition_days, upper_partition_demand, 
lower_partition_demand, unloading_days, des_biggest_demand, des_biggest_partition, des_contract_revenues, 
des_contract_partitions, earliest_unloading_day, last_unloading_day):

    # Sets for unloading days sets per contract 
    earliest_partition_unloading_day = earliest_unloading_day
    last_partition_unloading_day = loading_from_time
    
    for partition in contract['desRequests']:

        #Demand and stuff
        des_contract_partitions[contract['id']].append(partition['id'])
        partition_names[partition['id']] = partition['name']
        upper_partition_demand[contract['id'], partition['id']] = partition['quantity']
        lower_partition_demand[contract['id'], partition['id']] = partition['minQuantity']
        
        # Biggest demand
        if (partition['minQuantity']> des_biggest_demand[contract['id']]):
            des_biggest_demand[contract['id']] = partition['minQuantity']
            des_biggest_partition[contract['id']] = partition['id']
       
        # 
        partition_from_time = datetime.strptime(partition['from'].split('T')[0], '%Y-%m-%d') # Start time of contract
        if partition_from_time < earliest_unloading_day:
            earliest_unloading_day = partition_from_time
        elif partition_from_time > last_unloading_day:
            id = partition['id']
            raise ValueError(f'There is a contract that starts after last unloading day ({id}), fix data')
        
        if partition_from_time < earliest_partition_unloading_day:
            earliest_partition_unloading_day = partition_from_time

        partition_to_time = datetime.strptime(partition['to'].split('T')[0], '%Y-%m-%d') # End time of contract
        if partition_to_time>last_unloading_day:
            last_unloading_day = partition_to_time
        
        if partition_to_time > last_partition_unloading_day:
            last_partition_unloading_day = partition_to_time

        partition_start_time = (partition_from_time-loading_from_time).days
        partition_delta_time = (partition_to_time-partition_from_time).days
        if partition_start_time < 0:
            partition_start_time = 0 
        
        partition_days[partition['id']] = [
            i for i in range(partition_start_time+1,partition_start_time+partition_delta_time+1)]

    if(last_unloading_day>last_day):
        last_day=last_unloading_day
    
    unloading_days[contract['id']] = [i for i in range((earliest_partition_unloading_day-loading_from_time).days + 1,
    (earliest_partition_unloading_day-loading_from_time).days + 2 + (last_partition_unloading_day-earliest_partition_unloading_day).days)]
    
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
   
    return partition_names, partition_days, contract, des_contract_partitions, des_contract_revenues, upper_partition_demand, \
    lower_partition_demand, des_biggest_partition, des_biggest_demand, last_day, last_unloading_day

def read_fob_contracts(contract, loading_from_time, fob_ids, fob_contract_ids, fob_demands, fob_days, fob_revenues, fob_loading_ports):
    for partition in contract['fobRequests']:

        fob_ids.append(partition['name'])
        fob_contract_ids.append(partition['name'])
        fob_demands[partition['name']] = partition['quantity']
        fob_loading_ports[partition['name']] = partition['storageId']
        partition_from_time = datetime.strptime(partition['from'].split('T')[0], '%Y-%m-%d') # Start time of contract
        partition_to_time = datetime.strptime(partition['to'].split('T')[0], '%Y-%m-%d') # End time of contract
        partition_start_time = (partition_from_time-loading_from_time).days
        partition_delta_time = (partition_to_time-partition_from_time).days
        if partition_start_time < 0:
            partition_start_time = 0
        fob_days[partition['name']] = [
            i for i in range(partition_start_time+1,partition_start_time+partition_delta_time+2)]

        if len(contract['salesPrices'])==1:
            for t in fob_days[partition['name']]:
                fob_revenues[partition['name'], t] = contract['salesPrices'][0]['price']
        else: 
            for price in contract['salesPrices']:
                price_from_time = datetime.strptime(price['fromDateTime'].split('T')[0], '%Y-%m-%d')
                if price_from_time >= partition_to_time:
                    price_from_time = partition_to_time
                elif price_from_time < partition_from_time:
                    price_from_time = partition_from_time
                price_start_time = (price_from_time-loading_from_time).days
                for t in range(price_start_time+1, partition_start_time+partition_delta_time+2):
                    fob_revenues[partition['name'], t] = price['price']

    return fob_ids, fob_contract_ids, fob_revenues, fob_demands, fob_days, fob_loading_ports

def set_minimum_days_between():
    return MINIMUM_DAYS_BETWEEN_DELIVERY


def read_des_loading_ports(data, hasLoadingPortDesData, loading_port_ids):

    des_loading_ports = {}

    for contract in data['contracts']:
        if contract['id'][:3]=='DES':
            for partition in contract['desRequests']:
                if not contract['id'] in des_loading_ports:
                    if hasLoadingPortDesData == True:
                        des_loading_ports[contract['id']] = partition['storageId']
                    elif hasLoadingPortDesData == False:
                        des_loading_ports[contract['id']] = loading_port_ids
                else:
                    pass
    
    return des_loading_ports


def convert_loading_ports(des_loading_ports):

    for contract,loading_port in des_loading_ports.items():
        if loading_port == LOADING_NGBON:
            des_loading_ports[contract] = ['NGBON']
        elif loading_port == LOADING_FU:
            des_loading_ports[contract] = ['FU']
        elif loading_port == LOADING_DI:
            des_loading_ports[contract] = ['DI']
        else:
            raise ValueError('This is not a valid loading port')


def set_des_loading_ports(des_spot_ids, des_loading_ports, loading_port_ids):
    for des_spot_id in des_spot_ids:
        des_loading_ports[des_spot_id] = loading_port_ids