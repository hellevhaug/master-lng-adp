import csv

from runModel.runModel import *
from runModel.initModel import *
from supportFiles.writeToTxt import *
from supportFiles.writeToJson import *
from supportFiles.convertVars import *
from supportFiles.constants import *


def run_one_instance_basic(group, filename, runtime):
    # Running the model with given group, filename and runtime (including logging the file, this is done in run_model)
    model = run_basic_model(group, filename, runtime, f'Running file: {filename}')
    #model.computeIIS()
    #model.write('solution.ilp')

    # Converting gurobi variables to dictionaries, because they are easier to work with
    x,s,g,z,q,y = convert_vars_to_dicts(model)

    # Writing to txt-file, not necessary per now
    # write_to_txt(group, filename, runtime, x, s, g, z)

    # Writing variables to json-file
    write_to_json(group, filename, runtime, x, s, g, z, q, y, 'Basic model with minimum spread')


def run_one_instance_variable_production(group, filename, runtime):
    # Running the model with given group, filename and runtime (including logging the file, this is done in run_model)
    model = run_variable_production_model(group, filename, runtime, f'Running file: {filename}')

    # Converting gurobi variables to dictionaries, because they are easier to work with
    x,s,g,z,q,y = convert_vars_to_dicts(model)

    # Writing to txt-file, not necessary per now
    # write_to_txt(group, filename, runtime, x, s, g, z)

    # Writing variables to json-file
    write_to_json(group, filename, runtime, x, s, g, z, q, y, 'Model with variable production')


def run_one_instance_charter_out(group, filename, runtime):
    # Running the model with given group, filename and runtime (including logging the file, this is done in run_model)
    model = run_charter_out_model(group, filename, runtime, f'Running file: {filename}')
    model.computeIIS()
    model.write('solution.ilp')

    # Converting gurobi variables to dictionaries, because they are easier to work with
    x,s,g,z,q,y = convert_vars_to_dicts(model)

    # Writing to txt-file, not necessary per now
    # write_to_txt(group, filename, runtime, x, s, g, z)

    # Writing variables to json-file
    write_to_json(group, filename, runtime, x, s, g, z, q, y,'Model with chartering out')


def run_one_instance(group, filename, runtime, modelType):

    if modelType=='basic':
        run_one_instance_basic(group, filename, runtime)
    elif modelType=='variableProduction':
        run_one_instance_variable_production(group, filename, runtime)
    elif modelType=='charterOut':
        run_one_instance_charter_out(group, filename, runtime)
    else:
        raise ValueError('Uknown model type for running')

    

# Running all instances in a group, not testet yet 
def run_group(group):
    directory = f'testData/{group}'
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isFile(f):
            filestring, type = str(filename).split('.')
            if type=='json':
                map, directory = directory.split('/')
                run_one_instance_basic(directory, filestring)


# Function for initialize a model without running it with a solver
def test_init_basic_model(group, filename):
    model = initialize_basic_model(group, filename)
    return model


"""
Call whatever functions you'll like below here
"""

# An example for how to run the code 
group1 = 'N-1L-45D'
filename1 = 'N-1L-6U-18F-18V-45D-b'

runtime = 60*5
modelType = CHARTER_OUT_MODEL

run_one_instance(group1, filename1, runtime, modelType)



# Infeasible: 
# Group: A-2L-180D days et eller anna skjer her...
# Group: N-1L-30D, Filename: N-1L-2U-2F-18V-30D-a INFEASIBLE 
# Group: N-1L-30D, Filename: N-1L-2U-2F-18V-30D-b INFEASIBLE 
# Group: N-1L-30D, Filename: N-1L-2U-2F-18V-30D-c INFEASIBLE 
# Group: N-1L-45D, Extremely small GAP


