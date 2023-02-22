import json
from datetime import datetime
from readData.readOtherData import *
from readData.readContractData import *
from readData.readVesselData import *
from supportFiles.constants import *

def initialize_location_sets():
    location_ids = []
    location_names = {}
    location_types = {}
    location_ports = {}
    port_types = {}
    port_locations = {}
    return location_ids, location_names, location_types, location_ports, port_types, port_locations


def initialize_loading_port_sets():
    min_inventory = {}
    max_inventory = {}
    initial_inventory = {}
    number_of_berths = {}
    production_quantities = {}
    fake_fob_quantity = {}
    loading_port_fobs = {}
    return min_inventory, max_inventory, initial_inventory, number_of_berths, production_quantities, fake_fob_quantity, loading_port_fobs


def read_loading_ports(data, loading_port_ids, location_types, port_types, port_locations, location_ports, min_inventory, 
                       max_inventory, initial_inventory, number_of_berths, loading_days, loading_port_fobs, production_quantity,
                       fake_fob_quantity):
    for location in data['network']['ports']:
        if location['id'] in loading_port_ids:
            location_types[location['id']]='l'
            loading_port_fobs[location['id']] = []
            port_types[location['id']]='l'
            port_locations[location['id']] = location['id']
            location_ports[location['id']] = location['id']
            for info in location['export']['storages']:
                min_inventory[location['id']] = info['minSafeLimit']
                max_inventory[location['id']] = info['maxSafeLimit']
                initial_inventory[location['id']] = info['tankLevel'][0]['level']
                number_of_berths[location['id']] = len(info['compatibleBerths'])
                production_quantity[location['id']] = info['production'][0]['rate']
                fake_fob_quantity[location['id']] = info['defaultLoadingQuantity']


def set_unloading_ports(unloading_locations_ids, location_types, location_ports):
    for u_id in unloading_locations_ids:
        location_types[u_id] = 'u'
        location_ports[u_id] = []


def read_all_locations(data, location_ids, location_names):
    for location in data['network']['ports']:
        location_ids.append(location['id'])
        location_names[location['id']] = location['name']


def set_min_production_quantity(production_quantity, production_scale_rate):
    min_production_quantity = production_quantity.copy()
    for loading_port in production_quantity.keys():
        min_production_quantity[loading_port] = production_quantity[loading_port]*production_scale_rate
        
    return min_production_quantity


def set_production_quantities(production_quantity, loading_days):
    production_quantities = {}
    for loading_port in production_quantity.keys():
        for day in loading_days:
            production_quantities[loading_port, day] = production_quantity[loading_port]
    
    return production_quantities


def set_production_scale_rate():

    return PRODUCTION_SCALE_RATE