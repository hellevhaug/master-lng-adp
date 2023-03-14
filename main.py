from runModel.runModel import *
from runModel.initModel import *
from supportFiles.writeToTxt import *
from supportFiles.writeToJson import *
from supportFiles.convertVars import *
from supportFiles.constants import *


def write_vars_to_file(group, filename, model, message):

    try:
        x,s,g,z,q,y = convert_vars_to_dicts(model)
        write_to_json(group, filename, runtime, x, s, g, z, q, y, message)
        print('Variables written to file successfully.')
    
    except:
        model.computeIIS()
        model.write('solution.ilp')
        print('Could not write variables to file, infeasible model.')


def run_one_instance(group, filename, runtime, modelType):

    if modelType=='basic':
        model = run_basic_model(group, filename, runtime, f'Running file: {filename}')
        write_vars_to_file(group, filename, model, 'Basic model with minimum spread')
    elif modelType=='variableProduction':
        model = run_variable_production_model(group, filename, runtime, f'Running file: {filename}')
        write_vars_to_file(group, filename, model, 'Model with variable production')
    elif modelType=='charterOut':
        model = run_charter_out_model(group, filename, runtime, f'Running file: {filename}')
        write_vars_to_file(group, filename, model, 'Model with chartering out')
    else:
        raise ValueError('Uknown model type for running')

    

# Running all instances in a group, not testet yet 
def run_group(group, runtime, modelType):
    directory = f'testData/{group}'
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isFile(f):
            filestring, type = str(filename).split('.')
            if type=='json':
                map, directory = directory.split('/')
                run_one_instance(directory, filestring, runtime, modelType)


# Function for initialize a model without running it with a solver
def test_init_model(group, filename, modelType):
    if modelType=='basic':
        model = initialize_basic_model(group, filename)
    elif modelType=='variableProduction':
        model = initialize_variable_production_model(group, filename)
    elif modelType=='charterOut':
        model = initialize_charter_out_model(group, filename)
    else:
        raise ValueError('Uknown model type for running')
    return model
    

"""
Call whatever functions you'll like below here
"""

# An example for how to run the code 
group1 = 'N-1L-45D'
filename1 = 'N-1L-6U-18F-18V-45D-b'
runtime = 60*2
modelType = CHARTER_OUT_MODEL

run_one_instance(group1, filename1, runtime, modelType)
#test_init_model(group1, filename1, modelType)




