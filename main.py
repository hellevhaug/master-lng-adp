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
            model.write(f'IIS-{group}-{filename}.ilp')
            print('Could not write variables to file, infeasible model.')
        except:
            print('Model is feasible, but did not find a feasible solution withing the time limits.')


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


# Oppdatering: Denne funker! Runs all model types one one instance
def run_all_model_types(group, filename, runtime):
    if group=='N-1L-30D':
        print('Please do not do this, this model is actually too fast')
    else:
        modelTypes = MODEL_TYPES
        for modelType in modelTypes:
            try:
                run_one_instance(group, filename, runtime, modelType)
            except:
                print(f'Failed to run file: {filename}')
                pass


# Running all instances in a group, not testet yet 
def run_group(group, runTime, modelType):
    root = f'testData/{group}'
    for filename in os.listdir(root):
        path = root + '/' + filename
        if os.path.isfile(path):
            filestring, type = str(filename).split('.')
            if type=='json':
                run_one_instance(group, filestring, runTime, modelType)
                """
                try:
                    run_one_instance(group, filestring, runTime, modelType)
                except:
                    print(f'Failed to run file: {filestring}')
                    pass
                """


# Running all model types for all files in group
def run_all_model_types_for_group(group, runTime):
    root = f'testData/{group}'
    for filename in os.listdir(root):
        path = root + '/' + filename
        if os.path.isfile(path):
            filestring, type = str(filename).split('.')
            if type=='json':
                run_all_model_types(group, filestring, runTime)
                """
                try:
                    run_one_instance(group, filestring, runTime, modelType)
                except:
                    print(f'Failed to run file: {filestring}')
                    pass
                """


# Running all files in testData-directory
def run_all_files(runTime, modelType):
    root = 'testData/'
    for group in os.listdir(root):
        path = root + group
        if os.path.isdir(path):
            try: 
                run_group(group, runTime, modelType)
            except:
                print(f'Failed to run group: {group}')
                pass
    print('All files ran successfully')


# Running all model types for all files in every group
def run_all_files_all_model_types(runTime):
    root = 'testData/'
    for group in os.listdir(root):
        path = root + group
        if os.path.isdir(path):
            run_all_model_types_for_group(group, runTime)
            """
            try: 
                run_all_model_types_for_group(group, runTime)
            except:
                print(f'Failed to run group: {group}')
                pass
             """
    print('All files ran successfully')
    

"""
Call whatever functions you'll like below here
"""

# An example for how to run the code 
group = 'N-1L-A'
filename = 'N-1L-16U-18F-23V-180D'
group1 = 'A-2L-B'
filename1 = 'A-2L-6U-20F-15V-120D'
runtime = 60*60*4
modelType = BASIC_MODEL

run_one_instance(group, filename, runtime, modelType)
#test_init_model(group, filename, modelType)
#run_all_model_types(group1, filename1, runtime)
#run_all_model_types_for_group(group1, runtime)
#run_group(group, runtime, modelType)
#run_all_files(runtime, modelType)
#run_all_files_all_model_types(runtime)
