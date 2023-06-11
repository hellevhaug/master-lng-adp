import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd


from analysis.plotSolutions import *
from readData.readLocationData import *
from readData.readOtherData import *
from analysis.exploreSolution import *

from datetime import datetime, timedelta
from readData.readContractData import *
from readData.readVesselData import *
from readData.readSpotData import *
from supportFiles.constants import *

"""
File defining helper-functions for plotting different aspects of a solution
"""

def get_coordinates_dataframe():
    path = 'analysis/coordinates.csv'
    df = pd.read_csv(path, delimiter=',')
    return df


def get_contract_dataframe(group, filename):
    
    df = get_coordinates_dataframe()
    data = read_data_file(group, filename)

    loading_port_ids = set_loading_port_ids(filename)

    loading_from_time, loading_to_time, loading_days = read_planning_horizion(data)
    location_ids, location_names, location_types, location_ports, port_types, port_locations = initialize_location_sets() 
    read_all_locations(data, location_ids, location_names)
    unloading_locations_ids = [location for location in location_ids if location not in loading_port_ids]
    set_unloading_ports(unloading_locations_ids, location_types, location_ports)
    port_types, des_contract_ids, des_contract_revenues, des_contract_partitions, partition_names, partition_days, upper_partition_demand, lower_partition_demand, des_biggest_partition, des_biggest_demand, fob_ids, fob_contract_ids, fob_revenues, fob_demands, fob_days, fob_loading_ports, unloading_days, last_unloading_day, all_days= read_all_contracts(data, port_types, port_locations, location_ports, loading_to_time, loading_from_time)
    
    relevant_locations = list(port_locations.values())
    print(relevant_locations)
    df = df[df['ID'].isin(relevant_locations)]
    df = df.set_index(['ID'])

    return df


def reformat_coordinates_dataframe(df):
    longitude = {}
    latitude = {}
    for index, row in df.iterrows(): 
        latitude[row['ID']] = row['Latitude']
        longitude[row['ID']] = row['Longitude']
    return longitude, latitude

def plot_ports_for_instance(group, filename):
    countries = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    countries = countries.drop(159) # Antartica
    fig, ax = plt.subplots(figsize=(8,6))

    countries.plot(color="lightgrey",ax=ax)

    df = get_contract_dataframe(group, filename)

    df.plot(x="longitude", y="latitude", kind="scatter", 
            c="red", colormap="YlOrRd", 
            title="All loading- and unloading ports", 
            ax=ax)

    plt.show()


def plot_vessel_routes(group, filename, solutionPIT):
    df = get_coordinates_dataframe()

    return 0


def plot_inventory_levels(solutionData, group, dataFile):

    loading_port_ids = set_loading_port_ids(dataFile)
    data = read_data_file(group, dataFile)
    loading_from_time, loading_to_time, loading_days = read_planning_horizion(data)
    location_ids, location_names, location_types, location_ports, port_types, port_locations = initialize_location_sets() 
    read_all_locations(data, location_ids, location_names)
    unloading_locations_ids = [location for location in location_ids if location not in loading_port_ids]
    set_unloading_ports(unloading_locations_ids, location_types, location_ports)

    ## Initialize loading ports 
    min_inventory, max_inventory, initial_inventory, number_of_berths, production_quantity, fake_fob_quantity, loading_port_fobs = initialize_loading_port_sets()
    read_loading_ports(data, loading_port_ids, location_types, port_types, port_locations, location_ports, min_inventory, 
                       max_inventory, initial_inventory, number_of_berths, loading_days, loading_port_fobs, production_quantity,
                       fake_fob_quantity)

    s_dict = get_s_vars(solutionData)

    inventory_dict = {(loading_id):[] for loading_id in loading_port_ids}

    for (i,t), value in s_dict.items():
        t_inventory_date = loading_from_time+timedelta(days=t)
        inventory_dict[i].append(dict(LoadingPort=i, Date=t_inventory_date, Volume=value))

    for loading_id in loading_port_ids:
        df = pd.DataFrame(inventory_dict[loading_id])
        df['Volume'].plot(label=loading_id)
        plt.axhline(y=min_inventory[loading_id], color='r', linestyle='-')
        plt.axhline(y=max_inventory[loading_id], color='r', linestyle='-')
        plt.title('Inventory level plot for '+ loading_id)
        plt.ylim(0,max_inventory[loading_id]+100000)
        plt.show()
    


def plot_produced_lng(solutionData, group, dataFile):

    loading_port_ids = set_loading_port_ids(dataFile)
    data = read_data_file(group, dataFile)
    loading_from_time, loading_to_time, loading_days = read_planning_horizion(data)
    location_ids, location_names, location_types, location_ports, port_types, port_locations = initialize_location_sets() 
    read_all_locations(data, location_ids, location_names)
    unloading_locations_ids = [location for location in location_ids if location not in loading_port_ids]
    set_unloading_ports(unloading_locations_ids, location_types, location_ports)

    ## Initialize loading ports 
    min_inventory, max_inventory, initial_inventory, number_of_berths, production_quantity, fake_fob_quantity, loading_port_fobs = initialize_loading_port_sets()
    read_loading_ports(data, loading_port_ids, location_types, port_types, port_locations, location_ports, min_inventory, 
                       max_inventory, initial_inventory, number_of_berths, loading_days, loading_port_fobs, production_quantity,
                       fake_fob_quantity)
    
    info = get_solution_info(solutionData)
    parameters = get_solution_parameters(solutionData)

    if info['ModelType'] == 'Model with variable production':
        q_dict = get_q_vars(solutionData)
        produced_lng_dict = {(loading_id):[] for loading_id in loading_port_ids}

        for (i,t), volume in q_dict.items():
            t_inventory_date = loading_from_time+timedelta(days=t)
            produced_lng_dict[i].append(dict(LoadingPort=i, Date=t_inventory_date, Volume=volume))

        for loading_id in loading_port_ids:
            df = pd.DataFrame(produced_lng_dict[loading_id])
            df['Volume'].plot(label=loading_id)
            #plt.axhline(y=production_quantity[loading_id], color='r', linestyle='-')
            #plt.axhline(y=production_quantity[loading_id]*parameters['ProductionScaleRate'], color='r', linestyle='-')
            plt.title('Inventory level plot for '+ loading_id)
            plt.ylim(0,production_quantity[loading_id]+100000)
            plt.show()

    else: 
        print('This soltion was run with a model without variable production')
    



def plot_full_solution(group, filename, solutionPIT):

    data = read_data_file(group, filename)
    

    return 0

def contract_gant_chart(logDataPath, group, testDataFile, chartType):

###
    loading_port_ids = set_loading_port_ids(testDataFile)

    ## Initializing data
    data = read_data_file(group, testDataFile)

    # Planning horizion
    loading_from_time, loading_to_time, loading_days = read_planning_horizion(data)

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
    port_types, des_contract_ids, des_contract_revenues, des_contract_partitions, partition_names, partition_days, upper_partition_demand, lower_partition_demand, des_biggest_partition, des_biggest_demand, fob_ids, fob_contract_ids, fob_revenues, fob_demands, fob_days, fob_loading_ports, unloading_days, last_unloading_day, all_days= read_all_contracts(data, port_types, port_locations, location_ports, loading_to_time, loading_from_time)

    ## Initalize distances 
    distances = set_distances(data)

    ## Initialize spot stuffz
    spot_port_ids, des_spot_ids, fob_spot_ids = initialize_spot_sets()
    # Not all datasets have spot :)
    try:
        des_spot_ids, port_locations, port_types, des_contract_partitions, upper_partition_demand, lower_partition_demand, partition_days, unloading_days, des_contract_revenues= read_spot_des_contracts(data, spot_port_ids, des_spot_ids, port_locations, port_types, des_contract_partitions,
        loading_from_time, loading_to_time, upper_partition_demand, lower_partition_demand, partition_days, unloading_days,des_contract_revenues)
        fob_ids, fob_spot_ids, fob_demands, fob_days, fob_revenues, fob_loading_ports = read_spot_fob_contracts(data, fob_spot_ids, fob_ids, fob_demands, fob_days, fob_revenues, loading_from_time, fob_loading_ports)
        if len(fob_spot_ids+des_spot_ids)!=len(set(fob_spot_ids+des_spot_ids)):
            raise ValueError('There are duplicates in spot data')
    except KeyError:
        print('This dataset does not have spot ')
    except:
        print('Something went wrong!')
        pass
    #ays_between_delivery = {(j): set_minimum_days_between() for j in (des_contract_ids+des_spot_ids)}

    ## Initialize fake fob stuffz + set fob_operational_times
    #fob_spot_art_ports = read_fake_fob(loading_port_ids, fob_ids, fob_spot_ids, fob_days, loading_days, port_types, fob_demands, fob_revenues, fake_fob_quantity)
    #fob_operational_times = set_fob_operational_times(fob_ids, loading_port_ids)

    ## Initialize lists for vessels
    vessel_ids, vessel_names, vessel_available_days, vessel_capacities = initialize_vessel_sets(data)
    vessel_start_ports,vessel_location_acceptances, vessel_port_acceptances = initialize_vessel_location_sets(data)
    vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, vessel_boil_off_rate = initialize_vessel_speed_sets()
    maintenance_ids, maintenance_vessels, maintenance_vessel_ports, maintenance_durations, maintenance_start_times, maintenance_end_times  = initialize_maintenance_sets()

    # Producer vessels
    vessel_ids, vessel_capacities, location_ports, port_locations, port_types, vessel_start_ports, vessel_location_acceptances, vessel_port_acceptances, vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, vessel_boil_off_rate, vessel_available_days, maintenance_ids, maintenance_vessels, maintenance_vessel_ports, maintenance_start_times, maintenance_durations = read_producer_vessels(data, vessel_ids, vessel_capacities, location_ports, port_locations, port_types, vessel_start_ports, vessel_location_acceptances,
                        vessel_port_acceptances, loading_port_ids, vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, 
                        vessel_boil_off_rate, vessel_available_days, loading_from_time, loading_to_time, maintenance_ids, maintenance_vessels, maintenance_vessel_ports, 
                        maintenance_start_times, maintenance_durations, last_unloading_day, des_contract_ids)

    # Now all ports is defined, should include DES-contracts, DES-spot, loading- and maintenance ports :')
    port_ids = [port_id for port_id in port_locations]

    # Charter vessels
    # Initialize lists for charter vessels
    charter_vessel_port_acceptances, charter_vessel_node_acceptances, charter_vessel_upper_capacity, charter_vessel_lower_capacity, charter_vessel_prices = initialize_charter_sets(data)
    charter_vessel_id, charter_vessel_loading_quantity, charter_vessel_speed, charter_vessel_prices, charter_vessel_node_acceptances, charter_vessel_port_acceptances = read_charter_vessels(data, loading_days, loading_from_time, loading_to_time, charter_vessel_prices, loading_port_ids, charter_vessel_node_acceptances, charter_vessel_port_acceptances, des_contract_ids)

    sailing_time_charter = set_sailing_time_charter(loading_port_ids, des_spot_ids, des_contract_ids, distances, port_locations, charter_vessel_speed)
    #charter_total_cost = set_charter_total_cost(sailing_time_charter, charter_vessel_prices, loading_port_ids, des_contract_ids, loading_days)

    
    ## Creating gantt chart

    x_dict = get_x_vars(logDataPath) #dobbeltsjekke hva som skal puttes inn her
    g_dict = get_g_vars(logDataPath)
    z_dict = get_z_vars(logDataPath)

    df_list = []

    if chartType == "unloading":
            #DES-kontrakter
        for (v,i,t,j,t_), value in x_dict.items():
            if round(value, 0) == 1 and j in des_contract_ids and i != 'ART_PORT':
                t_marked_date = loading_from_time+timedelta(days=t_)
                df_list.append(dict(Contract=j, Start=t_marked_date-timedelta(days=1), Finish=t_marked_date, Type='Own vessel'))
        
        #DES-kontrakter som blir chartret
        for (i,t,j), value in g_dict.items(): 
            if round(value, 0) != 0: 
                t_date = loading_from_time+timedelta(days=t)
                sailing_time = sailing_time_charter[(i,j)]
                unloading_date = t_date+timedelta(days=sailing_time)
                df_list.append(dict(Contract=j, Start=unloading_date-timedelta(days=1), Finish=unloading_date, Type='Charter'))
        
        #FOB-kontrakter mottar LNG den dagen de løfter cargoen
        for (f,t_), value in z_dict.items(): 
            if round(value, 0) != 0:
                if f[3:4]=='S':
                    contract_name = "FOBSPOT "+f[8:9]
                elif f[0:1]=='A':
                    contract_name = "ARTFOB "
                else:
                    contract_name = "FOBCON "+f[7:8]
                t_marked_date = loading_from_time+timedelta(days=t_)
                df_list.append(dict(Contract=contract_name, Start=t_marked_date, Finish=t_marked_date+timedelta(days=1), Type='FOB'))

    if chartType == "loading": 
            #DES-kontrakter
        for (v,i,t,j,t_), value in x_dict.items():
            if round(value, 0) == 1 and j in des_contract_ids and i != 'ART_PORT':
                t_date = loading_from_time+timedelta(days=t)
                df_list.append(dict(Contract=j, Start=t_date-timedelta(days=1), Finish=t_date, Type='Own vessel'))
        
        #DES-kontrakter som blir chartret
        for (i,t,j), value in g_dict.items(): 
            if round(value, 0) != 0: 
                t_date = loading_from_time+timedelta(days=t)
                df_list.append(dict(Contract=j, Start=t_date-timedelta(days=1), Finish=t_date, Type='Charter'))
        
        #FOB-kontrakter mottar LNG den dagen de løfter cargoen
        for (f,t_), value in z_dict.items(): 
            if round(value, 0) != 0:
                if f[3:4]=='S':
                    contract_name = "FOBSPOT "+f[8:9]
                elif f[0:1]=='A':
                    contract_name = "ARTFOB "
                else:
                    contract_name = "FOBCON "+f[7:8]
                t_marked_date = loading_from_time+timedelta(days=t_)
                df_list.append(dict(Contract=contract_name, Start=t_marked_date, Finish=t_marked_date+timedelta(days=1), Type='FOB'))
        #print('df_list:', df_list)

    df = pd.DataFrame(df_list)
    print('DataFrame:', df)
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Contract", color="Contract", title=chartType+" chart for "+testDataFile)
    #fig = px.timeline(df, x_start="Start", x_end="Finish", y="Contract", color="Type", title=chartType+" chart for "+testDataFile)
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
    fig.show()
        