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
        try:
            model.computeIIS()
            model.write('solution.ilp')
            print('Could not write variables to file, infeasible model.')
        except:
            print('Model is feasible, but did not find a feasible solution withing the time limits.')


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


def run_all_model_types(group, file, runtime):
    if group=='N-1L-30D':
        print('Please do not do this, this model is actually too fast')
    else:
        modelTypes = MODEL_TYPES
        for modelType in modelTypes:
            run_one_instance(group, file, runtime, modelType)


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
group1 = 'A-2L-60D'
filename1 = 'A-2L-6U-11F-7V-60D-a'
runtime = 60*3
modelType = BASIC_MODEL
spotGroup = 'spotTests'
spotFilename='N-1L-10U-6F-23V-60D'

run_one_instance(spotGroup, spotFilename, runtime, modelType)
#test_init_model(spotGroup, spotFilename, modelType)

#run_all_model_types(group1, filename1, runtime)

