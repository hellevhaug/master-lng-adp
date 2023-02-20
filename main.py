import csv

from runModel.runModel import *
from runModel.initModel import *
from supportFiles.writeToTxt import *
from supportFiles.writeToJson import *
from supportFiles.convertVars import *


def run_one_instance(group, filename, runtime):
    # Running the model with given group, filename and runtime (including logging the file, this is done in run_model)
    model = run_model(group, filename, runtime, f'Running file: {filename}')

    # Converting gurobi variables to dictionaries, because they are easier to work with
    x,s,g,z = convert_vars_to_dicts(model)

    # Writing to txt-file, not necessary per now
    # write_to_txt(group, filename, runtime, x, s, g, z)

    # Writing variables to json-file
    write_to_json(group, filename, runtime, x, s, g, z)
    

# Running all instances in a group, not testet yet 
def run_group(group):
    directory = f'testData/{group}'
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isFile(f):
            filestring, type = str(filename).split('.')
            if type=='json':
                map, directory = directory.split('/')
                run_one_instance(directory, filestring)


# Function for initialize a model without running it with a solver
def test_init_model(group, filename):
    model = initialize_model(group, filename)
    return model


"""
Call whatever functions you'll like below here
"""

# An example for how to run the code 
group1 = 'A-1L-60D'
filename1 = 'A-1L-6U-11F-7V-60D-a'
runtime = 60

run_one_instance(group1, filename1, runtime)

