from runModel.runModel import *
from runModel.initModel import *
from readData.readVesselData import *

group = 'N-1L-60D'
filename = 'N-1L-5U-21F-18V-60D-c'

# An example for how to run the code 
# run_model(group, filename, 3*60*60)

data = initialize_model(group, filename)

print(initialize_vessel_sets(data))