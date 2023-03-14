import json 

from readData.readOtherData import *

"""
Functions for analyzing a solved model and its optimal variable values 
"""

# example: path = 'jsonFiles/A-1L-60D/A-1L-6U-11F-7V-60D-a/02-20-2023 22:00.json'
# right-click and choose "copy relative path"


def read_solved_json_file(path):
    
    file = open(path)
    data = json.load(file)
    
    return data

def get_x_vars(data):

    x = {}
    x_data = data['vars']['x']
    for x_var in x_data:
        v, i, t, j, t_ = x_var[2:-1].split(',')
        t = int(t)
        t_ = int(t_)
        value = x_data[x_var]
        if round(value, 0) == 1:
            x[v,i,t,j,t_] = value
    
    return x

def get_s_vars(data):

    s = {}
    s_data = data['vars']['s']
    for s_var in s_data:
        i, t = s_var[2:-1].split(',')
        t = int(t)
        value = s_data[s_var]
        s[i,t] = value 

    return s

def get_g_vars(data):

    g = {}
    g_data = data['vars']['g']
    for g_var in g_data:
        i, t, j = g_var[2:-1].split(',')
        t = int(t)
        value = g_data[g_var]
        if round(value, 0) != 0:
            g[i,t,j] = value

    return g

def get_z_vars(data):

    z = {}
    z_data = data['vars']['z']
    for z_var in z_data:
        f, t = z_var[2:-1].split(',')
        t = int(t)
        value = z_data[z_var]
        if round(value, 0) == 1:
            z[f,t] = value

    return z

def get_q_vars(data):

    q = {}
    q_data = data['vars']['q']
    for q_var in q_data:
        i, t = q_var[2:-1].split(',')
        t = int(t)
        value = q_data[q_var]
        q[i,t] = value 

    return q

def get_y_vars(data):

    y = {}
    y_data = data['vars']['y']
    for y_var in y_data:
        v = y_var[2:-1]
        value = y_data[y_var]
        if round(value,0) == 1:
            y[v] = value

    return y





