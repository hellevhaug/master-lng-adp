from readData.readOtherData import *
from readData.readContractData import *
from readData.readLocationData import *
from readData.readVesselData import *
from readData.readSpotData import *


def explore_instance(group, filename):

    loading_port_ids = set_loading_port_ids(filename)

    ## Initializing data
    data = read_data_file(group, filename)

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
    port_types, des_contract_ids, des_contract_revenues, des_contract_partitions, partition_names, partition_days, upper_partition_demand, lower_partition_demand, des_biggest_partition, des_biggest_demand, fob_ids, fob_contract_ids, fob_revenues, fob_demands, fob_days, fob_loading_port, unloading_days, last_unloading_day, all_days= read_all_contracts(data, port_types, port_locations, location_ports, loading_to_time, loading_from_time)

    ## Initalize distances 
    distances = set_distances(data)

    ## Initialize spot stuffz
    spot_port_ids, des_spot_ids, fob_spot_ids = initialize_spot_sets()
    days_between_delivery = {(j): set_minimum_days_between() for j in (des_contract_ids+des_spot_ids)}

    ## Initialize fake fob stuffz + set fob_operational_times
    fob_spot_art_ports = read_fake_fob(loading_port_ids, fob_ids, fob_spot_ids, fob_days, loading_days, port_types, fob_demands, fob_revenues, fake_fob_quantity)
    fob_operational_times = set_fob_operational_times(fob_ids, loading_port_ids)

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
    minimum_charter_period = set_minimum_charter_time()

    sailing_time_charter = set_sailing_time_charter(loading_port_ids, spot_port_ids, des_contract_ids, distances, port_locations, charter_vessel_speed)
    charter_total_cost = set_charter_total_cost(sailing_time_charter, charter_vessel_prices, loading_port_ids, des_contract_ids, loading_days)
    
    #####################################################################
    ##################### NEW STUFFZ BELOW HERE #########################
    #####################################################################

    #   Production of LNG
    total_production = sum(production_quantities.values())
    print(f'Total produced LNG in the planning period: {total_production}\n')

    #   Demands, both DES and FOB
    total_fob_demands = sum(fob_demands.values()) - sum(fake_fob_quantity.values())
    total_des_lower_demands = sum(lower_partition_demand.values())
    print(f'Total lower DES-demands: {total_des_lower_demands}\n')

    total_des_upper_demands = sum(upper_partition_demand.values())
    max_total_demand = total_fob_demands + total_des_upper_demands
    min_total_demand = total_fob_demands + total_des_lower_demands
    print(f'Total lower demand {min_total_demand}\n')
    print(f'Total upper demand {max_total_demand}\n')

    #   Cumulative demand check 



