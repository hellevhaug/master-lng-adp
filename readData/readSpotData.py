import json


def initialize_spot_sets():
    spot_port_ids = []
    des_spot_ids = []
    fob_spot_ids = []

    return spot_port_ids, des_spot_ids, fob_spot_ids

def read_spot_des_contracts(data, spot_port_ids, des_spot_ids):

    for spot_des_contract in data['spotDesRequests']:
        des_spot_ids.append(spot_des_contract['id'])
        if spot_des_contract['portId'] not in spot_port_ids:
            spot_port_ids.append(spot_des_contract['portId'])
        
        0

    return 0

def read_spot_fob_contracts(data, spot_port_ids, fob_spot_ids):

    for spot_fob_contract in data['spotFobRequests']:
        0

    return 0 