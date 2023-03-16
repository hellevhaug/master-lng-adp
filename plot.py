

import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd


from analysis.plotSolutions import *
from readData.readLocationData import *
from readData.readOtherData import *
from analysis.exploreSolution import *

from datetime import datetime
from readData.readContractData import *
from readData.readVesselData import *
from readData.readSpotData import *
from supportFiles.constants import *


'''
"""
File for plotting different stuffz
"""

def plot_ports(df):
    countries = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    countries = countries.drop(159) # Antartica
    fig, ax = plt.subplots(figsize=(8,6))

    countries.plot(color="lightgrey",ax=ax)

    df.plot(x="longitude", y="latitude", kind="scatter", 
            c="red", colormap="YlOrRd", 
            title="All loading- and unloading ports", 
            ax=ax)

    plt.show()


def plot_vessel_routes(group, filename, solutionPIT):
    df = get_coordinates_dataframe()

    return 0


def plot_inventory_storage():

    return 0


def plot_full_solution(group, filename, solutionPIT):

    data = read_data_file(group, filename)
    

    return 0

"""
countries = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
for index, row in countries.iterrows():
    print(index, row['name'])
countries = countries.drop(23)
"""

df = get_coordinates_dataframe()
#plot_ports(df)

'''

### Gantt Chart ###

#Eays to make one for loading as well

def contract_gant_chart(logDataPath, group, testDataFile):

###
    loading_port_ids = set_loading_port_ids(testDataFile)

    ## Initializing data
    data = read_data_file(group, testDataFile)

    # Planning horizion
    loading_from_time, loading_to_time, loading_days = read_planning_horizion(testDataFile)

    ## Initialize lists for locations and ports
    location_ids, location_names, location_types, location_ports, port_types, port_locations = initialize_location_sets() 
    read_all_locations(data, location_ids, location_names)
    unloading_locations_ids = [location for location in location_ids if location not in loading_port_ids]
    set_unloading_ports(unloading_locations_ids, location_types, location_ports)

    ## Initialize loading ports 
    min_inventory, max_inventory, initial_inventory, number_of_berths, production_quantity, fake_fob_quantity, loading_port_fobs = initialize_loading_port_sets()
    read_loading_ports(data, loading_port_ids, location_types, port_types, port_locations, location_ports, min_inventory, 
                       max_inventory, initial_inventory, number_of_berths, loading_days, loading_port_fobs, production_quantity,
                       fake_fob_quantity)
    production_quantities = set_production_quantities(production_quantity, loading_days)

    ## Initialize lists for contracts
    port_types, des_contract_ids, des_contract_revenues, des_contract_partitions, partition_names, partition_days, upper_partition_demand, lower_partition_demand, des_biggest_partition, des_biggest_demand, fob_ids, fob_contract_ids, fob_revenues, fob_demands, fob_days, fob_loading_port, unloading_days, last_unloading_day, all_days= read_all_contracts(data, port_types, port_locations, location_ports, loading_to_time, loading_from_time)

    ## Initalize distances 
    distances = set_distances(testDataFile)

    ## Initialize spot stuffz
    spot_port_ids, des_spot_ids, fob_spot_ids = initialize_spot_sets()
    #ays_between_delivery = {(j): set_minimum_days_between() for j in (des_contract_ids+des_spot_ids)}

    ## Initialize fake fob stuffz + set fob_operational_times
    #fob_spot_art_ports = read_fake_fob(loading_port_ids, fob_ids, fob_spot_ids, fob_days, loading_days, port_types, fob_demands, fob_revenues, fake_fob_quantity)
    #fob_operational_times = set_fob_operational_times(fob_ids, loading_port_ids)

    ## Initialize lists for vessels
    vessel_ids, vessel_names, vessel_available_days, vessel_capacities = initialize_vessel_sets(testDataFile)
    vessel_start_ports,vessel_location_acceptances, vessel_port_acceptances = initialize_vessel_location_sets(testDataFile)
    vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, vessel_boil_off_rate = initialize_vessel_speed_sets()
    maintenance_ids, maintenance_vessels, maintenance_vessel_ports, maintenance_durations, maintenance_start_times, maintenance_end_times  = initialize_maintenance_sets()

    # Producer vessels
    vessel_ids, vessel_capacities, location_ports, port_locations, port_types, vessel_start_ports, vessel_location_acceptances, vessel_port_acceptances, vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, vessel_boil_off_rate, vessel_available_days, maintenance_ids, maintenance_vessels, maintenance_vessel_ports, maintenance_start_times, maintenance_durations = read_producer_vessels(testDataFile, vessel_ids, vessel_capacities, location_ports, port_locations, port_types, vessel_start_ports, vessel_location_acceptances,
                        vessel_port_acceptances, loading_port_ids, vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, 
                        vessel_boil_off_rate, vessel_available_days, loading_from_time, loading_to_time, maintenance_ids, maintenance_vessels, maintenance_vessel_ports, 
                        maintenance_start_times, maintenance_durations, last_unloading_day, des_contract_ids)

    # Now all ports is defined, should include DES-contracts, DES-spot, loading- and maintenance ports :')
    port_ids = [port_id for port_id in port_locations]

    # Charter vessels
    # Initialize lists for charter vessels
    charter_vessel_port_acceptances, charter_vessel_node_acceptances, charter_vessel_upper_capacity, charter_vessel_lower_capacity, charter_vessel_prices = initialize_charter_sets(data)
    charter_vessel_id, charter_vessel_loading_quantity, charter_vessel_speed, charter_vessel_prices, charter_vessel_node_acceptances, charter_vessel_port_acceptances = read_charter_vessels(data, loading_days, loading_from_time, loading_to_time, charter_vessel_prices, loading_port_ids, charter_vessel_node_acceptances, charter_vessel_port_acceptances, des_contract_ids)

    sailing_time_charter = set_sailing_time_charter(loading_port_ids, spot_port_ids, des_contract_ids, distances, port_locations, charter_vessel_speed)
    #charter_total_cost = set_charter_total_cost(sailing_time_charter, charter_vessel_prices, loading_port_ids, des_contract_ids, loading_days)

###
# Creating gantt chart
  
    x_dict = get_x_vars(logDataPath) #dobbeltsjekke hva som skal puttes inn her
    g_dict = get_g_vars(logDataPath)
    z_dict = get_z_vars(logDataPath)

    df = pd.DataFrame([])

    #DES-kontrakter
    for (v,i,t,j,t_), value in x_dict.items():
        if round(value, 0) == 1 and j in des_contract_ids:
            t_marked_date = loading_from_time+datetime.timedelta(days=t_)
            
            df.append(dict(Contract=j, Start=t_marked_date-datetime.timedelta(days=-1), Finish=t_))
    
    #DES-kontrakter som blir chartret
    for (i,t,j), value in g_dict.items(): 
        if round(value, 0) != 0: 
            t_date = loading_from_time+datetime.timedelta(days=t)
            sailing_time = sailing_time_charter[(i,j)]
            unloading_date = t_date+datetime.timedelta(days=sailing_time)#FIX
            df.append(dict(Contract=j, Start=t, Finish=t+1))
        
    #FOB-kontrakter mottar LNG den dagen de løfter cargoen
    for (f,t_), value in z_dict.items(): 
        if round(value, 0) != 0:
            t_marked_date = loading_from_time+datetime.timedelta(days=t_)
            df.append(dict(Contract=f, Start=t_, Finish=t_marked_date+datetime.timedelta(days=1)))


    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Contract")
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
    fig.show()


    return 0


## Example of how to plot a gant chart ##
group1 = 'A-2L-60D'
data1 = 'A-2L-6U-11F-7V-60D-a'
logFile1 = 'jsonFiles/A-2L-60D/A-2L-6U-11F-7V-60D-a/03-13-2023, 09-20.json'
logData = read_solved_json_file(logFile1)
contract_gant_chart(logData, group1, data1)


# Oppskrift på gantt chart: 
'''
import plotly.express as px
import pandas as pd

df = pd.DataFrame([
    dict(Task="Job A", Start='2009-01-01', Finish='2009-02-28'),
    dict(Task="Job B", Start='2009-03-05', Finish='2009-04-15'),
    dict(Task="Job C", Start='2009-02-20', Finish='2009-05-30')
])

fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task")
fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
fig.show()
'''