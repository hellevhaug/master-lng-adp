import json
import os
import datetime

from supportFiles.convertVars import *


def set_info_dict(group, filename, runtime, now, modelType):
    info_dict = {}
    info_dict['Group'] = group
    info_dict['Filename'] = filename
    info_dict['Runtime'] = runtime
    info_dict['Model type'] = modelType
    now = datetime.datetime.now()
    info_dict['Current time'] = now.strftime("%Y-%m-%d %H:%M:%S")
    
    return info_dict


def write_to_json(group, filename, runtime, x, s, g, z, q, y, modelType):
    folder = f'jsonFiles/{group}/{filename}'
    
    # if the log file does not exist
    if not os.path.exists(folder):
        raise FileNotFoundError('This path does not exists, you should check the json-log-folders')
    
    now = datetime.datetime.now()
    filename = now.strftime("%m-%d-%Y, %H-%M")
    path = f'{folder}/{filename}.json'
    
    with open(path, "x") as init_json:
        pass
    
    with open(path, 'a') as f:
        main_dict = {}
        main_dict['info'] = set_info_dict(group, filename, runtime, now, modelType)
        main_dict['vars'] = aggregate_vars_to_dict(x,s,g,z,q,y)
        json.dump(main_dict, f, indent=3)

""""

def write_to_json_basic(group, filename, runtime, x, s, g, z, modelType):

    folder = f'jsonFiles/{group}/{filename}'
    
    # if the log file does not exist
    if not os.path.exists(folder):
        raise FileNotFoundError('This path does not exists, you should check the json-log-folders')
    
    now = datetime.datetime.now()
    filename = now.strftime("%m-%d-%Y, %H-%M")
    path = f'{folder}/{filename}.json'
    
    with open(path, "x") as init_json:
            pass
    
    with open(path, 'a') as f:
        main_dict = {}
        main_dict['info'] = set_info_dict(group, filename, runtime, now, modelType)
        main_dict['vars'] = aggregate_vars_to_dict(x,s,g,z)
        json.dump(main_dict, f, indent=3)


def write_to_json_variable_prod(group, filename, runtime, x, s, g, z, q, modelType):

    folder = f'jsonFiles/{group}/{filename}'
    
    # if the log file does not exist
    if not os.path.exists(folder):
        raise FileNotFoundError('This path does not exists, you should check the json-log-folders')
    
    now = datetime.datetime.now()
    filename = now.strftime("%m-%d-%Y, %H-%M")
    path = f'{folder}/{filename}.json'
    
    with open(path, "x") as init_json:
            pass
    
    with open(path, 'a') as f:
        main_dict = {}
        main_dict['info'] = set_info_dict(group, filename, runtime, now, modelType)
        main_dict['vars'] = aggregate_vars_to_dict(x,s,g,z,q)
        json.dump(main_dict, f, indent=3)
    

def write_to_json_charter_out(group, filename, runtime, x, s, g, z, y, modelType):

    folder = f'jsonFiles/{group}/{filename}'
    
    # if the log file does not exist
    if not os.path.exists(folder):
        raise FileNotFoundError('This path does not exists, you should check the json-log-folders')
    
    now = datetime.datetime.now()
    filename = now.strftime("%m-%d-%Y, %H-%M")
    path = f'{folder}/{filename}.json'
    
    with open(path, "x") as init_json:
            pass
    
    with open(path, 'a') as f:
        main_dict = {}
        main_dict['info'] = set_info_dict(group, filename, runtime, now, modelType)
        main_dict['vars'] = aggregate_vars_to_dict(x,s,g,z,y)
        json.dump(main_dict, f, indent=3)

"""