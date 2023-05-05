import json
from datetime import datetime


def initialize_spot_sets():
    spot_port_ids = []
    des_spot_ids = []
    fob_spot_ids = []

    return spot_port_ids, des_spot_ids, fob_spot_ids


# Need to pretend that des-spot-contracts have partitions

def read_spot_des_contracts(data, spot_port_ids, des_spot_ids, port_locations, port_types, des_contract_partitions,
    loading_from_time, loading_to_time, upper_partition_demand, lower_partition_demand, partition_days, 
    unloading_days, des_contract_revenues):

    for spot_des_contract in data['spotDesRequests']:

        # General info about locations and stuffz
        des_spot_ids.append(spot_des_contract['id'])
        if spot_des_contract['portId'] not in spot_port_ids:
            spot_port_ids.append(spot_des_contract['portId'])
        port_locations[spot_des_contract['id']] = spot_des_contract['portId']
        port_types[spot_des_contract['id']] = 's'
        des_contract_partitions[spot_des_contract['id']] = [spot_des_contract['id']]

        # Demand
        upper_partition_demand[spot_des_contract['id'],spot_des_contract['id']] = spot_des_contract['quantity']
        lower_partition_demand[spot_des_contract['id'],spot_des_contract['id']] = 0

        # Time 
        last_unloading_day = loading_to_time
        earliest_unloading_day = loading_to_time

        partition_from_time = datetime.strptime(spot_des_contract['fromDateTime'].split('T')[0], '%Y-%m-%d') # Start time of contract
        print(spot_des_contract['id'],partition_from_time)
        if partition_from_time < earliest_unloading_day:
            earliest_unloading_day = partition_from_time
        if partition_from_time > last_unloading_day:
            id = spot_des_contract['id']
            raise ValueError(f'There is a contract that starts after last unloading day ({id}), fix data')
        
        partition_to_time = datetime.strptime(spot_des_contract['toDateTime'].split('T')[0], '%Y-%m-%d') # End time of contract
        print(spot_des_contract['id'],partition_to_time)
        if partition_to_time>last_unloading_day:
            last_unloading_day = partition_to_time
        partition_start_time = (partition_from_time-loading_from_time).days
        partition_delta_time = (partition_to_time-partition_from_time).days
        print(spot_des_contract['id'],partition_delta_time)
        if partition_start_time < 0:
            partition_start_time = 0 
        
        partition_days[spot_des_contract['id']] = [
            i for i in range(partition_start_time+1,partition_start_time+partition_delta_time+1)]
        
        unloading_days[spot_des_contract['id']] = partition_days[spot_des_contract['id']]

        # Price
        if len(spot_des_contract['salesPrices'])==1:
            for t in unloading_days[spot_des_contract['id']]:
                des_contract_revenues[spot_des_contract['id'], t] = spot_des_contract['salesPrices'][0]['price']
        else: 
            for price in spot_des_contract['salesPrices']:
                price_from_time = datetime.strptime(price['fromDateTime'].split('T')[0], '%Y-%m-%d')
                if price_from_time < earliest_unloading_day:
                    price_from_time = earliest_unloading_day
                price_start_time = (price_from_time-earliest_unloading_day).days
                for t in unloading_days[spot_des_contract['id']]:
                    des_contract_revenues[spot_des_contract['id'], t] = price['price']
    
    return des_spot_ids, port_locations, port_types, des_contract_partitions, upper_partition_demand, lower_partition_demand, partition_days, unloading_days, des_contract_revenues



def read_spot_fob_contracts(data, fob_spot_ids, fob_ids, fob_demands, fob_days, fob_revenues, loading_from_time, fob_loading_ports):

    for spot_fob_contract in data['spotFobRequests']:
        fob_ids.append(spot_fob_contract['name'])
        fob_spot_ids.append(spot_fob_contract['name'])
        fob_demands[spot_fob_contract['name']] = spot_fob_contract['quantity']

        partition_from_time = datetime.strptime(spot_fob_contract['fromDateTime'].split('T')[0], '%Y-%m-%d') # Start time of contract
        partition_to_time = datetime.strptime(spot_fob_contract['toDateTime'].split('T')[0], '%Y-%m-%d') # End time of contract
        partition_start_time = (partition_from_time-loading_from_time).days
        partition_delta_time = (partition_to_time-partition_from_time).days
        fob_loading_ports[spot_fob_contract['name']] = spot_fob_contract['storageId']
        if partition_start_time < 0:
            partition_start_time = 0
        fob_days[spot_fob_contract['name']] = [
            i for i in range(partition_start_time+1,partition_start_time+partition_delta_time+2)]

        if len(spot_fob_contract['salesPrices'])==1:
            for t in fob_days[spot_fob_contract['name']]:
                fob_revenues[spot_fob_contract['name'], t] = spot_fob_contract['salesPrices'][0]['price']
        else: 
            for price in spot_fob_contract['salesPrices']:
                price_from_time = datetime.strptime(price['fromDateTime'].split('T')[0], '%Y-%m-%d')
                if price_from_time >= partition_to_time:
                    price_from_time = partition_to_time
                elif price_from_time < partition_from_time:
                    price_from_time = partition_from_time
                price_start_time = (price_from_time-loading_from_time).days
                for t in range(price_start_time+1, partition_start_time+partition_delta_time+2):
                    fob_revenues[spot_fob_contract['name'], t] = price['price']

    return fob_ids, fob_spot_ids, fob_demands, fob_days, fob_revenues, fob_loading_ports