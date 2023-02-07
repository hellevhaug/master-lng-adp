import json
from datetime import datetime
from readData.readContractData import *
from readData.readLocationData import *
from readData.readVesselData import *
from supportFiles.constants import *


def set_loading_port_ids(filename):
    
    customer = filename[0]
    if customer == 'N':
        return NIG
    elif customer == 'A':
        return ABU
    else: 
        raise ValueError('Unknown origin of data')


def read_data_file(group, filename):

    file = open(f'testData/{group}/{filename}.json')
    data = json.load(file)

    return data


def read_planning_horizion(data):

    loading_from_time = datetime.strptime(data['forecast']['fromDateTime'].split('T')[0], '%Y-%m-%d')
    loading_to_time = datetime.strptime(data['forecast']['toDateTime'].split('T')[0], '%Y-%m-%d')
    loading_days = [i for i in range(1,(loading_to_time-loading_from_time).days+1)]
    
    return loading_from_time, loading_to_time, loading_days



