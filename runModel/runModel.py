from readData.readOtherData import *
from readData.readContractData import *
from readData.readLocationData import *
from readData.readVesselData import *
from supportFiles.constants import *

def run_model(group, filename):

    # Finding out if it is data from Nigeria or Abu Dabi
    loading_port_ids = set_loading_port_ids(filename)

    # Initializing data
    data = read_data_file(group, filename)

    # Planning horizion
    loading_from_time, loading_to_time, loading_days = read_planning_horizion(data)

    # Initiaize lists for locations and ports
    location_ids, location_names, location_types, location_ports, port_types, port_locations = initialize_location_sets() 


group = 'N-1L-45D'
filename = 'N-1L-6U-13F-18V-45D-a'

run_model(group, filename)

    
