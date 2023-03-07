import csv

from runModel.runModel import *
from runModel.initModel import *
from supportFiles.writeToTxt import *
from supportFiles.writeToJson import *
from supportFiles.convertVars import *


def run_one_instance_basic(group, filename, runtime):
    # Running the model with given group, filename and runtime (including logging the file, this is done in run_model)
    model = run_basic_model(group, filename, runtime, f'Running file: {filename}')
    #model.computeIIS()
    #model.write('solution.ilp')

    # Converting gurobi variables to dictionaries, because they are easier to work with
    x,s,g,z = convert_vars_to_dicts(model)

    # Writing to txt-file, not necessary per now
    # write_to_txt(group, filename, runtime, x, s, g, z)

    # Writing variables to json-file
    write_to_json(group, filename, runtime, x, s, g, z, 'Basic model with minimum spread')
    

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

def run_one_instance_variable_production(group, filename, runtime):
    # Running the model with given group, filename and runtime (including logging the file, this is done in run_model)
    model = run_variable_production_model(group, filename, runtime, f'Running file: {filename}')

    # Converting gurobi variables to dictionaries, because they are easier to work with
    x,s,g,z = convert_vars_to_dicts(model)

    # Writing to txt-file, not necessary per now
    # write_to_txt(group, filename, runtime, x, s, g, z)

    # Writing variables to json-file
    write_to_json(group, filename, runtime, x, s, g, z, 'Model with variable production')


"""
Call whatever functions you'll like below here
"""

# An example for how to run the code 
group1 = 'A-1L-60D'
filename1 = 'A-1L-6U-11F-12V-60D-b'
runtime = 60*5

#run_one_instance_basic(group1, filename1, runtime)
run_one_instance_basic(group1, filename1, runtime)
#run_one_instance_variable_production(group1, filename1, runtime)

