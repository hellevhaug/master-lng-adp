import gurobipy as gp

"""
File for creating different methods for converting vars to different file formats
"""

def convert_vars_to_dicts(model):
    x = {}
    s = {}
    g = {}
    z = {}
    q = {}
    for var in model.getVars():
        if var.x != 0:
            if var.varName[0]=='x':
                x[var.varName] = var.x
            if var.varName[0]=='s':
                s[var.varName] = var.x
            if var.varName[0]=='g':
                g[var.varName] = var.x
            if var.varName[0]=='z':
                z[var.varName] = var.x
            if var.varName[0]=='q':
                q[var.varName] = var.x

    return x,s,g,z,q


def aggregate_vars_to_dict(x, s, g, z, q):
    aggregated_vars_dict = {}
    aggregated_vars_dict['x'] = x
    aggregated_vars_dict['s'] = s
    aggregated_vars_dict['g'] = g
    aggregated_vars_dict['z'] = z
    aggregated_vars_dict['q'] = q

    return aggregated_vars_dict

