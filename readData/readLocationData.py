import json
from datetime import datetime
from readData.readOtherData import *
from readData.readContractData import *
from readData.readVesselData import *

def initialize_location_sets():
    location_ids = []
    location_names = {}
    location_types = {}
    location_ports = {}
    port_types = {}
    port_locations = {}
    return location_ids, location_names, location_types, location_ports, port_types, port_locations


def read_loading_ports(data):


    return 0


def read_all_locations(data, location_ids, location_names):
    for location in data['network']['ports']:
        location_ids.append(location['id'])
        location_names[location['id']] = location['name']


def read_locations_and_ports(data):


    return 0