import gurobipy as gp
from gurobipy import GRB
import itertools

from readData.readOtherData import *
from readData.readContractData import *
from readData.readLocationData import *
from readData.readVesselData import *
from readData.readSpotData import *
from supportFiles.constants import *
from runModel.initConstraints import *
from runModel.initArcs import *

### Basic model
def initialize_basic_model(group, filename):

    # Finding out if it is data from Nigeria or Abu Dabi
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
    vessels_has_loading_port_data = DES_HAS_LOADING_PORT
    try:
        des_loading_ports = read_des_loading_ports(data, vessels_has_loading_port_data, loading_port_ids)
        convert_des_loading_ports(des_loading_ports)
    except:
        des_loading_ports = read_des_loading_ports(data, False, loading_port_ids)

    ## Initalize distances 
    distances = set_distances(data)

    ## Initialize spot stuffz
    spot_port_ids, des_spot_ids, fob_spot_ids = initialize_spot_sets()
    # Not all datasets have spot :)
    try:
        des_spot_ids, port_locations, port_types, des_contract_partitions, upper_partition_demand, lower_partition_demand, partition_days, unloading_days, des_contract_revenues= read_spot_des_contracts(data, spot_port_ids, des_spot_ids, port_locations, port_types, des_contract_partitions,
        loading_from_time, loading_to_time, upper_partition_demand, lower_partition_demand, partition_days, unloading_days,des_contract_revenues)
        fob_ids, fob_spot_ids, fob_demands, fob_days, fob_revenues = read_spot_fob_contracts(data, fob_spot_ids, fob_ids, fob_demands, fob_days, fob_revenues, loading_from_time)
    except:
        pass
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

    sailing_time_charter = set_sailing_time_charter(loading_port_ids, des_spot_ids, des_contract_ids, distances, port_locations, charter_vessel_speed)
    charter_total_cost = set_charter_total_cost(sailing_time_charter, charter_vessel_prices, loading_port_ids, des_contract_ids, loading_days, des_spot_ids)

    ## Initializing arcs
    arc_speeds, arc_waiting_times, arc_sailing_times, sailing_costs, total_feasible_arcs = init_arc_sets()
    fuel_price, charter_boil_off, tank_leftover_value, allowed_waiting = set_external_data(data)

    # Setting operational times for vessel-port-combinations
    operational_times = {(v,i,j): set_operational_time(v,i,j, maintenance_ids, maintenance_durations) 
    for v,i,j in list(itertools.product(vessel_ids, port_ids, port_ids))}

    vessel_feasible_arcs = {vessel: find_feasible_arcs(vessel, allowed_waiting, vessel_start_ports, vessel_available_days, sailing_costs, arc_sailing_times, all_days, 
    maintenance_vessels, vessel_port_acceptances, port_types, loading_port_ids, maintenance_ids, des_contract_ids, distances, 
    des_spot_ids, loading_days, port_locations, vessel_max_speed, vessel_min_speed, arc_speeds, arc_waiting_times, operational_times,
    fuel_price, total_feasible_arcs, maintenance_start_times, maintenance_durations, maintenance_vessel_ports, unloading_days, vessel_laden_speed_profile,
    vessel_ballast_speed_profile, BASIC_MODEL, des_loading_ports) 
    for vessel in vessel_ids}
        

    #######################  INITIALIZING GUROBI ########################
    model = gp.Model()

    # Initializing variables
    
    x = model.addVars(total_feasible_arcs, vtype='B', name='x')

    fob_dimensions = [(f,t) for f in fob_ids for t in fob_days[f]] # Each fob contract has a specific loading node 
    z = model.addVars(fob_dimensions, vtype ='B', name='z')

    charter_dimensions = [(i,t,j) for i in loading_port_ids for t in loading_days for j in (des_contract_ids + des_spot_ids)]
    w = model.addVars(charter_dimensions, vtype ='B', name='w')

    g = model.addVars(charter_dimensions, vtype='C', name='g')

    s = model.addVars(production_quantities, vtype='C', name='s')

    # Initializing constraints

    model.setObjective(init_objective(x, z, s, w, g, fob_revenues, fob_demands, fob_ids, fob_days,
    des_contract_revenues, vessel_capacities, vessel_boil_off_rate, vessel_ids, loading_port_ids, loading_days, 
    spot_port_ids, all_days, sailing_time_charter, unloading_days, charter_boil_off, tank_leftover_value, 
    vessel_available_days, des_contract_ids, sailing_costs, charter_total_cost, des_spot_ids),GRB.MAXIMIZE)


    # Constraint 5.2
    model.addConstrs(init_initial_loading_inventory_constr(s, g, z, x, production_quantities, vessel_capacities, 
    vessel_ids, des_contract_ids, all_days,fob_demands, fob_ids, loading_port_ids, loading_days, initial_inventory),
    name='initital_inventory_control')


    # Constraint 5.3
    model.addConstrs(init_loading_inventory_constr(s, g, z, x, production_quantities, vessel_capacities, vessel_ids,
    des_contract_ids, all_days,fob_demands, fob_ids, loading_port_ids, loading_days), name='inventory_control')


    # Constraint 5.4
    model.addConstrs(init_upper_inventory_constr(s, max_inventory),name='upper_inventory')

    model.addConstrs(init_lower_inventory_constr(s, min_inventory),name='lower_inventory')


    # Constraint 5.5
    model.addConstrs(init_maintenance_constr(x, maintenance_vessel_ports, maintenance_vessels), name='maintenance')


    # Constraint 5.6
    model.addConstrs(init_flow_constr(x, all_days, vessel_ids, port_ids), name='flow')


    # Constraint 5.61
    model.addConstrs(init_artificial_flow_constr(x, vessel_start_ports, vessel_available_days, all_days, vessel_ids),
    name='artificial_node')


    # Constraint 5.8
    model.addConstrs(init_upper_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, port_ids, loading_days,
    partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, upper_partition_demand, des_contract_ids, des_spot_ids,
    des_contract_partitions), name='upper_demand')

    model.addConstrs(init_lower_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, port_ids, loading_days,
    partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, lower_partition_demand, des_contract_ids, des_spot_ids,
    des_contract_partitions), name='lower_demand')

    #Constraint 5.9 
    model.addConstrs(init_spread_delivery_constraints(x, w, vessel_ids, loading_port_ids, vessel_available_days, des_contract_ids, unloading_days,
    days_between_delivery, des_spot_ids, sailing_time_charter), name='spread_delivery')


    # Constraint 5.10
    model.addConstrs(init_fob_max_contracts_constr(z, fob_days, fob_contract_ids), name='fob_max_contracts')


    # Constraint 5.11
    model.addConstrs(init_fob_max_order_constr(z, fob_days, fob_spot_ids, fob_spot_art_ports), name='fob_order')


    # Constraint 5.12
    model.addConstrs(init_berth_constr(x, z, w, vessel_ids, port_ids, loading_days, operational_times, des_contract_ids, fob_ids, 
    fob_operational_times, number_of_berths, loading_port_ids), name='berth_constraint')


    # Constraint 5.13 
    model.addConstrs(init_charter_upper_capacity_constr(g, w, charter_vessel_upper_capacity, loading_port_ids, loading_days, 
    des_spot_ids, des_contract_ids), name='charter_upper_capacity')

    model.addConstrs(init_charter_lower_capacity_constr(g, w, charter_vessel_lower_capacity, loading_port_ids, loading_days, 
    des_spot_ids, des_contract_ids), name='charter_lower_capacity') # This should be the last thing happening here

    return model # This line must be moved to activate the extensions


### Dummy model?
def initialize_model_dummy(group, filename):

    # Finding out if it is data from Nigeria or Abu Dabi
    loading_port_ids = set_loading_port_ids(filename)

    ## Initializing data
    data = read_data_file(group, filename)

    return data


### Extension 1 - Variable production
def initialize_variable_production_model(group, filename):
    
    # Finding out if it is data from Nigeria or Abu Dabi
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
    production_scale_rate = set_production_scale_rate()
    min_production_quantity = set_min_production_quantity(production_quantity, production_scale_rate)


    ## Initialize lists for contracts
    port_types, des_contract_ids, des_contract_revenues, des_contract_partitions, partition_names, partition_days, upper_partition_demand, lower_partition_demand, des_biggest_partition, des_biggest_demand, fob_ids, fob_contract_ids, fob_revenues, fob_demands, fob_days, fob_loading_port, unloading_days, last_unloading_day, all_days= read_all_contracts(data, port_types, port_locations, location_ports, loading_to_time, loading_from_time)
    vessels_has_loading_port_data = DES_HAS_LOADING_PORT
    try:
        des_loading_ports = read_des_loading_ports(data, vessels_has_loading_port_data, loading_port_ids)
        convert_des_loading_ports(des_loading_ports)
    except:
        des_loading_ports = read_des_loading_ports(data, False, loading_port_ids)

    ## Initalize distances 
    distances = set_distances(data)

    ## Initialize spot stuffz
    spot_port_ids, des_spot_ids, fob_spot_ids = initialize_spot_sets()
    # Not all datasets have spot :)
    try:
        des_spot_ids, port_locations, port_types, des_contract_partitions, upper_partition_demand, lower_partition_demand, partition_days, unloading_days, des_contract_revenues= read_spot_des_contracts(data, spot_port_ids, des_spot_ids, port_locations, port_types, des_contract_partitions,
        loading_from_time, loading_to_time, upper_partition_demand, lower_partition_demand, partition_days, unloading_days,des_contract_revenues)
        fob_ids, fob_spot_ids, fob_demands, fob_days, fob_revenues = read_spot_fob_contracts(data, fob_spot_ids, fob_ids, fob_demands, fob_days, fob_revenues, loading_from_time)
    except:
        pass
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

    sailing_time_charter = set_sailing_time_charter(loading_port_ids, des_spot_ids, des_contract_ids, distances, port_locations, charter_vessel_speed)
    charter_total_cost = set_charter_total_cost(sailing_time_charter, charter_vessel_prices, loading_port_ids, des_contract_ids, loading_days, des_spot_ids)

    ## Initializing arcs
    arc_speeds, arc_waiting_times, arc_sailing_times, sailing_costs, total_feasible_arcs = init_arc_sets()
    fuel_price, charter_boil_off, tank_leftover_value, allowed_waiting = set_external_data(data)

    # Setting operational times for vessel-port-combinations
    operational_times = {(v,i,j): set_operational_time(v,i,j, maintenance_ids, maintenance_durations) 
    for v,i,j in list(itertools.product(vessel_ids, port_ids, port_ids))}

    vessel_feasible_arcs = {vessel: find_feasible_arcs(vessel, allowed_waiting, vessel_start_ports, vessel_available_days, sailing_costs, arc_sailing_times, all_days, 
    maintenance_vessels, vessel_port_acceptances, port_types, loading_port_ids, maintenance_ids, des_contract_ids, distances, 
    des_spot_ids, loading_days, port_locations, vessel_max_speed, vessel_min_speed, arc_speeds, arc_waiting_times, operational_times,
    fuel_price, total_feasible_arcs, maintenance_start_times, maintenance_durations, maintenance_vessel_ports, unloading_days, vessel_laden_speed_profile,
    vessel_ballast_speed_profile, VARIABLE_PRODUCTION_MODEL, des_loading_ports) 
    for vessel in vessel_ids}


    #######################  INITIALIZING GUROBI ########################
    model = gp.Model()

    # Initializing variables
    
    x = model.addVars(total_feasible_arcs, vtype='B', name='x')

    fob_dimensions = [(f,t) for f in fob_ids for t in fob_days[f]] # Each fob contract has a specific loading node 
    z = model.addVars(fob_dimensions, vtype ='B', name='z')

    charter_dimensions = [(i,t,j) for i in loading_port_ids for t in loading_days for j in (des_contract_ids + des_spot_ids)]
    w = model.addVars(charter_dimensions, vtype ='B', name='w')

    g = model.addVars(charter_dimensions, vtype='C', name='g')

    production_quantities = set_production_quantities(production_quantity, loading_days) # Creating dimensions for production quantities
    s = model.addVars(production_quantities, vtype='C', name='s')

    q = model.addVars(production_quantities, vtype='C', name='q')

    # Initializing constraints

    model.setObjective(init_objective(x, z, s, w, g, fob_revenues, fob_demands, fob_ids, fob_days,
    des_contract_revenues, vessel_capacities, vessel_boil_off_rate, vessel_ids, loading_port_ids, loading_days, 
    spot_port_ids, all_days, sailing_time_charter, unloading_days, charter_boil_off, tank_leftover_value, 
    vessel_available_days, des_contract_ids, sailing_costs, charter_total_cost, des_spot_ids),GRB.MAXIMIZE)


    # Constraint 5.2
    model.addConstrs(init_initial_loading_inventory_constr(s, g, z, x, q, vessel_capacities, 
    vessel_ids, des_contract_ids, all_days,fob_demands, fob_ids, loading_port_ids, loading_days, initial_inventory),
    name='initital_inventory_control')


    # Constraint 5.3
    model.addConstrs(init_loading_inventory_constr(s, g, z, x, q, vessel_capacities, vessel_ids,
    des_contract_ids, all_days,fob_demands, fob_ids, loading_port_ids, loading_days), name='inventory_control')


    # Constraint 5.4
    model.addConstrs(init_upper_inventory_constr(s, max_inventory),name='upper_inventory')

    model.addConstrs(init_lower_inventory_constr(s, min_inventory),name='lower_inventory')


    # Constraint 5.5
    model.addConstrs(init_maintenance_constr(x, maintenance_vessel_ports, maintenance_vessels), name='maintenance')


    # Constraint 5.6
    model.addConstrs(init_flow_constr(x, all_days, vessel_ids, port_ids), name='flow')


    # Constraint 5.61
    model.addConstrs(init_artificial_flow_constr(x, vessel_start_ports, vessel_available_days, all_days, vessel_ids),
    name='artificial_node')


    # Constraint 5.8
    model.addConstrs(init_upper_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, port_ids, loading_days,
    partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, upper_partition_demand, des_contract_ids, des_spot_ids,
    des_contract_partitions), name='upper_demand')

    model.addConstrs(init_lower_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, port_ids, loading_days,
    partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, lower_partition_demand, des_contract_ids, des_spot_ids,
    des_contract_partitions), name='lower_demand')

    #Constraint 5.9 
    model.addConstrs(init_spread_delivery_constraints(x, w, vessel_ids, loading_port_ids, vessel_available_days, des_contract_ids, unloading_days,
    days_between_delivery, des_spot_ids, sailing_time_charter), name='spread_delivery')


    # Constraint 5.10
    model.addConstrs(init_fob_max_contracts_constr(z, fob_days, fob_contract_ids), name='fob_max_contracts')


    # Constraint 5.11
    model.addConstrs(init_fob_max_order_constr(z, fob_days, fob_spot_ids, fob_spot_art_ports), name='fob_order')


    # Constraint 5.12
    model.addConstrs(init_berth_constr(x, z, w, vessel_ids, port_ids, loading_days, operational_times, des_contract_ids, fob_ids, 
    fob_operational_times, number_of_berths, loading_port_ids), name='berth_constraint')


    # Constraint 5.13 
    model.addConstrs(init_charter_upper_capacity_constr(g, w, charter_vessel_upper_capacity, loading_port_ids, loading_days, 
    des_spot_ids, des_contract_ids), name='charter_upper_capacity')

    model.addConstrs(init_charter_lower_capacity_constr(g, w, charter_vessel_lower_capacity, loading_port_ids, loading_days, 
    des_spot_ids, des_contract_ids), name='charter_lower_capacity') # This should be the last thing happening here


    # Constraint 5.19
    model.addConstrs(init_lower_prod_rate_constr(q, min_production_quantity, loading_days, loading_port_ids), name='lower_prod_rate')
    model.addConstrs(init_upper_prod_rate_constr(q, production_quantity, loading_days, loading_port_ids), name='upper_prod_rate')

    #NB! The parameter minimum and maximum production rate for each loading port must be defined; Maximum can be set to the default amount from data.


    return model # This line must be moved to activate the extensions

### Extension 2 - Charter out vessels
def initialize_charter_out_model(group, filename):

    # Finding out if it is data from Nigeria or Abu Dabi
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
    vessels_has_loading_port_data = DES_HAS_LOADING_PORT
    try:
        des_loading_ports = read_des_loading_ports(data, vessels_has_loading_port_data, loading_port_ids)
        convert_des_loading_ports(des_loading_ports)
    except:
        des_loading_ports = read_des_loading_ports(data, False, loading_port_ids)

    ## Initalize distances 
    distances = set_distances(data)

    ## Initialize spot stuffz
    spot_port_ids, des_spot_ids, fob_spot_ids = initialize_spot_sets()
    # Not all datasets have spot :)
    try:
        des_spot_ids, port_locations, port_types, des_contract_partitions, upper_partition_demand, lower_partition_demand, partition_days, unloading_days, des_contract_revenues= read_spot_des_contracts(data, spot_port_ids, des_spot_ids, port_locations, port_types, des_contract_partitions,
        loading_from_time, loading_to_time, upper_partition_demand, lower_partition_demand, partition_days, unloading_days,des_contract_revenues)
        fob_ids, fob_spot_ids, fob_demands, fob_days, fob_revenues = read_spot_fob_contracts(data, fob_spot_ids, fob_ids, fob_demands, fob_days, fob_revenues, loading_from_time)
    except:
        pass
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
    charter_out_friction = set_charter_out_friction()
    scaled_charter_out_prices = scale_charter_out_prices(charter_vessel_prices, charter_out_friction)

    sailing_time_charter = set_sailing_time_charter(loading_port_ids, des_spot_ids, des_contract_ids, distances, port_locations, charter_vessel_speed)
    charter_total_cost = set_charter_total_cost(sailing_time_charter, charter_vessel_prices, loading_port_ids, des_contract_ids, loading_days, des_spot_ids)

    ## Initializing arcs
    arc_speeds, arc_waiting_times, arc_sailing_times, sailing_costs, total_feasible_arcs = init_arc_sets()
    fuel_price, charter_boil_off, tank_leftover_value, allowed_waiting = set_external_data(data)

    # Setting operational times for vessel-port-combinations
    operational_times = {(v,i,j): set_operational_time(v,i,j, maintenance_ids, maintenance_durations) 
    for v,i,j in list(itertools.product(vessel_ids, port_ids, port_ids))}

    vessel_feasible_arcs = {vessel: find_feasible_arcs(vessel, allowed_waiting, vessel_start_ports, vessel_available_days, sailing_costs, arc_sailing_times, all_days, 
    maintenance_vessels, vessel_port_acceptances, port_types, loading_port_ids, maintenance_ids, des_contract_ids, distances, 
    des_spot_ids, loading_days, port_locations, vessel_max_speed, vessel_min_speed, arc_speeds, arc_waiting_times, operational_times,
    fuel_price, total_feasible_arcs, maintenance_start_times, maintenance_durations, maintenance_vessel_ports, unloading_days, vessel_laden_speed_profile,
    vessel_ballast_speed_profile, CHARTER_OUT_MODEL, des_loading_ports) 
    for vessel in vessel_ids}


    #######################  INITIALIZING GUROBI ########################
    model = gp.Model()

    # Initializing variables
    
    x = model.addVars(total_feasible_arcs, vtype='B', name='x')

    fob_dimensions = [(f,t) for f in fob_ids for t in fob_days[f]] # Each fob contract has a specific loading node 
    z = model.addVars(fob_dimensions, vtype ='B', name='z')

    charter_dimensions = [(i,t,j) for i in loading_port_ids for t in loading_days for j in (des_contract_ids + des_spot_ids)]
    w = model.addVars(charter_dimensions, vtype ='B', name='w')

    g = model.addVars(charter_dimensions, vtype='C', name='g')

    s = model.addVars(production_quantities, vtype='C', name='s')

    y = model.addVars(vessel_ids, vtype='B', name='y')
   

    # Initializing constraints

    model.setObjective(init_objective_charter(x, z, s, w, g, fob_revenues, fob_demands, fob_ids, fob_days, des_contract_revenues,
    vessel_capacities, vessel_boil_off_rate, vessel_ids, loading_port_ids, loading_days, spot_port_ids, all_days, sailing_time_charter,
    unloading_days, charter_boil_off, tank_leftover_value, vessel_available_days, des_contract_ids, sailing_costs, charter_total_cost,
    des_spot_ids, scaled_charter_out_prices),GRB.MAXIMIZE)
    

    # Constraint 5.2
    model.addConstrs(init_initial_loading_inventory_constr(s, g, z, x, production_quantities, vessel_capacities, 
    vessel_ids, des_contract_ids, all_days,fob_demands, fob_ids, loading_port_ids, loading_days, initial_inventory),
    name='initital_inventory_control')


    # Constraint 5.3
    model.addConstrs(init_loading_inventory_constr(s, g, z, x, production_quantities, vessel_capacities, vessel_ids,
    des_contract_ids, all_days,fob_demands, fob_ids, loading_port_ids, loading_days), name='inventory_control')


    # Constraint 5.4
    model.addConstrs(init_upper_inventory_constr(s, max_inventory),name='upper_inventory')

    model.addConstrs(init_lower_inventory_constr(s, min_inventory),name='lower_inventory')


    # Constraint 5.5
    model.addConstrs(init_maintenance_constr(x, maintenance_vessel_ports, maintenance_vessels), name='maintenance')

    """"
    # Constraint 5.6
    model.addConstrs(init_flow_constr(x, all_days, vessel_ids, port_ids), name='flow')


    # Constraint 5.61
    model.addConstrs(init_artificial_flow_constr(x, vessel_start_ports, vessel_available_days, all_days, vessel_ids),
    name='artificial_node')
    """

    # Constraint 5.8
    model.addConstrs(init_upper_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, port_ids, loading_days,
    partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, upper_partition_demand, des_contract_ids, des_spot_ids,
    des_contract_partitions), name='upper_demand')

    model.addConstrs(init_lower_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, port_ids, loading_days,
    partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, lower_partition_demand, des_contract_ids, des_spot_ids,
    des_contract_partitions), name='lower_demand')

    #Constraint 5.9 
    model.addConstrs(init_spread_delivery_constraints(x, w, vessel_ids, loading_port_ids, vessel_available_days, des_contract_ids, unloading_days,
    days_between_delivery, des_spot_ids, sailing_time_charter), name='spread_delivery')


    # Constraint 5.10
    model.addConstrs(init_fob_max_contracts_constr(z, fob_days, fob_contract_ids), name='fob_max_contracts')


    # Constraint 5.11
    model.addConstrs(init_fob_max_order_constr(z, fob_days, fob_spot_ids, fob_spot_art_ports), name='fob_order')


    # Constraint 5.12
    model.addConstrs(init_berth_constr(x, z, w, vessel_ids, port_ids, loading_days, operational_times, des_contract_ids, fob_ids, 
    fob_operational_times, number_of_berths, loading_port_ids), name='berth_constraint')


    # Constraint 5.13 
    model.addConstrs(init_charter_upper_capacity_constr(g, w, charter_vessel_upper_capacity, loading_port_ids, loading_days, 
    des_spot_ids, des_contract_ids), name='charter_upper_capacity')

    model.addConstrs(init_charter_lower_capacity_constr(g, w, charter_vessel_lower_capacity, loading_port_ids, loading_days, 
    des_spot_ids, des_contract_ids), name='charter_lower_capacity') # This should be the last thing happening here

    # NEW CONSTRAINT (5.22, only chartered out one time)
    model.addConstrs(init_charter_one_time_constr(x, y, loading_days, port_ids, vessel_ids, vessel_available_days),
                     name='charrter_one_time')

    # NEW CONSTRAINT (5.23, chartered out at least M days)
    model.addConstrs(init_charter_min_time_constr(x, y, vessel_available_days, minimum_charter_period, vessel_ids), name='charter_min_time')

    # NEW CONSTRAINT (changes to flow constraints)
    model.addConstrs(init_charter_flow_constr(x, all_days, vessel_ids, port_ids), name='charter_flow')

    # NEW CONSTRAINT (changes to initial flow constraints)
    model.addConstrs(init_charter_artificial_flow(x, vessel_start_ports, vessel_available_days, vessel_ids, all_days), name='charter_initial_flow')

    # NEW CONSTRAINT (5.26, must return to loading port after being chartered out)
    model.addConstrs(init_charter_return_to_loading_constr(x, loading_days, loading_port_ids, vessel_ids, port_ids), name='charter_return')

    return model # This line must be moved to activate the extensions

### Extension 1 + 2
def initialize_combined_model(group, filename):

    # Finding out if it is data from Nigeria or Abu Dabi
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
    production_scale_rate = set_production_scale_rate()
    min_production_quantity = set_min_production_quantity(production_quantity, production_scale_rate)
    

    ## Initialize lists for contracts
    port_types, des_contract_ids, des_contract_revenues, des_contract_partitions, partition_names, partition_days, upper_partition_demand, lower_partition_demand, des_biggest_partition, des_biggest_demand, fob_ids, fob_contract_ids, fob_revenues, fob_demands, fob_days, fob_loading_port, unloading_days, last_unloading_day, all_days= read_all_contracts(data, port_types, port_locations, location_ports, loading_to_time, loading_from_time)
    vessels_has_loading_port_data = DES_HAS_LOADING_PORT
    try:
        des_loading_ports = read_des_loading_ports(data, vessels_has_loading_port_data, loading_port_ids)
        convert_des_loading_ports(des_loading_ports)
    except:
        des_loading_ports = read_des_loading_ports(data, False, loading_port_ids)

    ## Initalize distances 
    distances = set_distances(data)

    ## Initialize spot stuffz
    spot_port_ids, des_spot_ids, fob_spot_ids = initialize_spot_sets()
    # Not all datasets have spot :)
    try:
        des_spot_ids, port_locations, port_types, des_contract_partitions, upper_partition_demand, lower_partition_demand, partition_days, unloading_days, des_contract_revenues= read_spot_des_contracts(data, spot_port_ids, des_spot_ids, port_locations, port_types, des_contract_partitions,
        loading_from_time, loading_to_time, upper_partition_demand, lower_partition_demand, partition_days, unloading_days,des_contract_revenues)
        fob_ids, fob_spot_ids, fob_demands, fob_days, fob_revenues = read_spot_fob_contracts(data, fob_spot_ids, fob_ids, fob_demands, fob_days, fob_revenues, loading_from_time)
    except:
        pass
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
    charter_out_friction = set_charter_out_friction()
    scaled_charter_out_prices = scale_charter_out_prices(charter_vessel_prices, charter_out_friction)

    sailing_time_charter = set_sailing_time_charter(loading_port_ids, des_spot_ids, des_contract_ids, distances, port_locations, charter_vessel_speed)
    charter_total_cost = set_charter_total_cost(sailing_time_charter, charter_vessel_prices, loading_port_ids, des_contract_ids, loading_days, des_spot_ids)

    ## Initializing arcs
    arc_speeds, arc_waiting_times, arc_sailing_times, sailing_costs, total_feasible_arcs = init_arc_sets()
    fuel_price, charter_boil_off, tank_leftover_value, allowed_waiting = set_external_data(data)

    # Setting operational times for vessel-port-combinations
    operational_times = {(v,i,j): set_operational_time(v,i,j, maintenance_ids, maintenance_durations) 
    for v,i,j in list(itertools.product(vessel_ids, port_ids, port_ids))}

    vessel_feasible_arcs = {vessel: find_feasible_arcs(vessel, allowed_waiting, vessel_start_ports, vessel_available_days, sailing_costs, arc_sailing_times, all_days, 
    maintenance_vessels, vessel_port_acceptances, port_types, loading_port_ids, maintenance_ids, des_contract_ids, distances, 
    des_spot_ids, loading_days, port_locations, vessel_max_speed, vessel_min_speed, arc_speeds, arc_waiting_times, operational_times,
    fuel_price, total_feasible_arcs, maintenance_start_times, maintenance_durations, maintenance_vessel_ports, unloading_days, vessel_laden_speed_profile,
    vessel_ballast_speed_profile, CHARTER_OUT_MODEL, des_loading_ports) 
    for vessel in vessel_ids}


    #######################  INITIALIZING GUROBI ########################
    model = gp.Model()

    # Initializing variables
    
    x = model.addVars(total_feasible_arcs, vtype='B', name='x')

    fob_dimensions = [(f,t) for f in fob_ids for t in fob_days[f]] # Each fob contract has a specific loading node 
    z = model.addVars(fob_dimensions, vtype ='B', name='z')

    charter_dimensions = [(i,t,j) for i in loading_port_ids for t in loading_days for j in (des_contract_ids + des_spot_ids)]
    w = model.addVars(charter_dimensions, vtype ='B', name='w')

    g = model.addVars(charter_dimensions, vtype='C', name='g')

    y = model.addVars(vessel_ids, vtype='B', name='y')

    production_quantities = set_production_quantities(production_quantity, loading_days)

    q = model.addVars(production_quantities, vtype='C', name='q')

    s = model.addVars(production_quantities, vtype='C', name='s')
   

    # Initializing constraints

    model.setObjective(init_objective_charter(x, z, s, w, g, fob_revenues, fob_demands, fob_ids, fob_days, des_contract_revenues,
    vessel_capacities, vessel_boil_off_rate, vessel_ids, loading_port_ids, loading_days, spot_port_ids, all_days, sailing_time_charter,
    unloading_days, charter_boil_off, tank_leftover_value, vessel_available_days, des_contract_ids, sailing_costs, charter_total_cost,
    des_spot_ids, scaled_charter_out_prices),GRB.MAXIMIZE)
    

    # Constraint 5.2
    model.addConstrs(init_initial_loading_inventory_constr(s, g, z, x, production_quantities, vessel_capacities, 
    vessel_ids, des_contract_ids, all_days,fob_demands, fob_ids, loading_port_ids, loading_days, initial_inventory),
    name='initital_inventory_control')


    # Constraint 5.3
    model.addConstrs(init_loading_inventory_constr(s, g, z, x, production_quantities, vessel_capacities, vessel_ids,
    des_contract_ids, all_days,fob_demands, fob_ids, loading_port_ids, loading_days), name='inventory_control')


    # Constraint 5.4
    model.addConstrs(init_upper_inventory_constr(s, max_inventory),name='upper_inventory')

    model.addConstrs(init_lower_inventory_constr(s, min_inventory),name='lower_inventory')


    # Constraint 5.5
    model.addConstrs(init_maintenance_constr(x, maintenance_vessel_ports, maintenance_vessels), name='maintenance')

    """"
    # Constraint 5.6
    model.addConstrs(init_flow_constr(x, all_days, vessel_ids, port_ids), name='flow')


    # Constraint 5.61
    model.addConstrs(init_artificial_flow_constr(x, vessel_start_ports, vessel_available_days, all_days, vessel_ids),
    name='artificial_node')
    """

    # Constraint 5.8
    model.addConstrs(init_upper_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, port_ids, loading_days,
    partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, upper_partition_demand, des_contract_ids, des_spot_ids,
    des_contract_partitions), name='upper_demand')

    model.addConstrs(init_lower_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, port_ids, loading_days,
    partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, lower_partition_demand, des_contract_ids, des_spot_ids,
    des_contract_partitions), name='lower_demand')

    #Constraint 5.9 
    model.addConstrs(init_spread_delivery_constraints(x, w, vessel_ids, loading_port_ids, vessel_available_days, des_contract_ids, unloading_days,
    days_between_delivery, des_spot_ids, sailing_time_charter), name='spread_delivery')


    # Constraint 5.10
    model.addConstrs(init_fob_max_contracts_constr(z, fob_days, fob_contract_ids), name='fob_max_contracts')


    # Constraint 5.11
    model.addConstrs(init_fob_max_order_constr(z, fob_days, fob_spot_ids, fob_spot_art_ports), name='fob_order')


    # Constraint 5.12
    model.addConstrs(init_berth_constr(x, z, w, vessel_ids, port_ids, loading_days, operational_times, des_contract_ids, fob_ids, 
    fob_operational_times, number_of_berths, loading_port_ids), name='berth_constraint')


    # Constraint 5.13 
    model.addConstrs(init_charter_upper_capacity_constr(g, w, charter_vessel_upper_capacity, loading_port_ids, loading_days, 
    des_spot_ids, des_contract_ids), name='charter_upper_capacity')

    model.addConstrs(init_charter_lower_capacity_constr(g, w, charter_vessel_lower_capacity, loading_port_ids, loading_days, 
    des_spot_ids, des_contract_ids), name='charter_lower_capacity') # This should be the last thing happening here

    # NEW CONSTRAINT (5.22, only chartered out one time)
    model.addConstrs(init_charter_one_time_constr(x, y, loading_days, port_ids, vessel_ids, vessel_available_days),
                     name='charrter_one_time')

    # NEW CONSTRAINT (5.23, chartered out at least M days)
    model.addConstrs(init_charter_min_time_constr(x, y, vessel_available_days, minimum_charter_period, vessel_ids), name='charter_min_time')

    # NEW CONSTRAINT (changes to flow constraints)
    model.addConstrs(init_charter_flow_constr(x, all_days, vessel_ids, port_ids), name='charter_flow')

    # NEW CONSTRAINT (changes to initial flow constraints)
    model.addConstrs(init_charter_artificial_flow(x, vessel_start_ports, vessel_available_days, vessel_ids, all_days), name='charter_initial_flow')

    # NEW CONSTRAINT (5.26, must return to loading port after being chartered out)
    model.addConstrs(init_charter_return_to_loading_constr(x, loading_days, loading_port_ids, vessel_ids, port_ids), name='charter_return')

     # Constraint 5.19
    model.addConstrs(init_lower_prod_rate_constr(q, min_production_quantity, loading_days, loading_port_ids), name='lower_prod_rate')
    model.addConstrs(init_upper_prod_rate_constr(q, production_quantity, loading_days, loading_port_ids), name='upper_prod_rate')

    #NB! The parameter minimum and maximum production rate for each loading port must be defined; Maximum can be set to the default amount from data.

    return model # This line must be moved to activate the extensions
