from runModel.runModel import *
from runModel.initModel import *
from supportFiles.writeToTxt import *
from supportFiles.writeToJson import *
from supportFiles.convertVars import *
from supportFiles.constants import *


# Function for writing variables to file
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


# Function for running a specific instance
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
    elif modelType=='combinedModel':
        model = run_combined_model(group, filename, runtime, f'Running file: {filename}')
        write_vars_to_file(group, filename, model, 'Model with combined extensions')
    else:
        raise ValueError('Uknown model type for running')


# Running all instances in a group, not testet yet 
def run_group(group, runTime, modelType):
    root = f'testData/{group}'
    for filename in os.listdir(root):
        path = root + '/' + filename
        if os.path.isfile(path):
            filestring, type = str(filename).split('.')
            if type=='json':
                try:
                    run_one_instance(group, filestring, runTime, modelType)
                except:
                    pass


# Running all files in testData-directory
def run_all_files(runTime, modelType):
    root = 'testData/'
    for group in os.listdir(root):
        path = root + group
        if os.path.isdir(path):
            try: 
                run_group(group, runTime, modelType)
            except:
                pass
    print('All files ran successfully')


# Oppdatering: Denne funker! Runs all model types one one instance
def run_all_model_types(group, file, runtime):
    if group=='N-1L-30D':
        print('Please do not do this, this model is actually too fast')
    else:
        modelTypes = MODEL_TYPES
        for modelType in modelTypes:
            try:
                run_one_instance(group, file, runtime, modelType)
            except:
                pass



# Function for initialize a model without running it with a solver
def test_init_model(group, filename, modelType):
    if modelType=='basic':
        model = initialize_basic_model(group, filename)
    elif modelType=='variableProduction':
        model = initialize_variable_production_model(group, filename)
    elif modelType=='charterOut':
        model = initialize_charter_out_model(group, filename)
    elif modelType=='combinedModel':
        model = initialize_combined_model(group, filename)
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

#run_one_instance(group1, filename1, runtime, modelType)
#test_init_model(group1, filename1, modelType)

#run_all_model_types(group1, filename1, runtime)
run_group(group1, runtime, modelType)

