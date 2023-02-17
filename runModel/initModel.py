import gurobipy as gp
import itertools

from readData.readOtherData import *
from readData.readContractData import *
from readData.readLocationData import *
from readData.readVesselData import *
from supportFiles.constants import *
from runModel.initConstraints import *
from runModel.initArcs import *


def initialize_model(group, filename):

    # Finding out if it is data from Nigeria or Abu Dabi
    loading_port_ids = set_loading_port_ids(filename)

    ## Initializing data
    data = read_data_file(group, filename)

    # Planning horizion
    loading_from_time, loading_to_time, loading_days = read_planning_horizion(data)

    ## Initialize lists for locations and ports
    location_ids, location_names, location_types, location_ports, port_types, port_locations = initialize_location_sets() 

    ## Initialize lists for contracts

    ## Initialize lists for vessels
    vessel_ids, vessel_names, vessel_available_days, vessel_capacities = initialize_vessel_sets(data)
    vessel_start_ports,vessel_location_acceptances, vessel_port_acceptances = initialize_vessel_location_sets(data)
    vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, vessel_boil_off_rate = initialize_vessel_speed_sets
    maintenance_ids, maintenance_vessels, maintenance_vessel_ports, maintenance_durations, maintenance_start_times, maintenance_end_times  = initialize_maintenance_sets

    # Producer vessels

    vessel_ids, vessel_capacities, location_ports, port_locations, port_types, vessel_start_ports, vessel_location_acceptances, vessel_port_acceptances, vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, vessel_boil_off_rate, vessel_available_days, maintenance_ids, maintenance_vessels, maintenance_vessel_ports, maintenance_start_times, maintenance_durations = read_producer_vessels(data, vessel_ids, vessel_capacities, location_ports, port_locations, port_types, vessel_start_ports, vessel_location_acceptances,
                        vessel_port_acceptances, loading_port_ids, vessel_min_speed, vessel_max_speed, vessel_ballast_speed_profile, vessel_laden_speed_profile, 
                        vessel_boil_off_rate, vessel_available_days, loading_from_time, loading_to_time, maintenance_ids, maintenance_vessels, maintenance_vessel_ports, 
                        maintenance_start_times, maintenance_durations, last_unloading_day, des_contract_ids)

    # Charter vessels

    # Initialize lists for charter vessels
    charter_vessel_port_acceptances, charter_vessel_node_acceptances, charter_vessel_upper_capacity, charter_vessel_lower_capacity, charter_vessel_prices = initialize_charter_sets()

    charter_vessel_id, charter_vessel_loading_quantity, charter_vessel_speed, charter_vessel_prices, loading_port_ids, charter_vessel_node_acceptances, charter_vessel_port_acceptances = read_charter_vessels(data, loading_days, loading_from_time, loading_to_time, charter_vessel_prices, loading_port_ids, charter_vessel_node_acceptances, charter_vessel_port_acceptances, des_contract_ids)

    sailing_time_charter = {(i, j): calculate_charter_sailing_time(i,j) for i in loading_port_ids for j in (spot_port_ids+des_contract_ids)}
    charter_total_cost = {(i,t,j):sailing_time_charter[i,j]*charter_vessel_prices[t]*2 for i in loading_port_ids for j in des_contract_ids for t in loading_days}

    ## Initializing arcs
    arc_speeds, arc_waiting_times, arc_sailing_times, sailing_costs, total_feasible_arcs = init_arc_sets()

    fuel_price, charter_boil_off, tank_leftover_value, allowed_waiting = set_external_data(data)



    # Setting operational times for vessel-port-combinations
    operational_times = {(v,i,j): set_operational_time(v,i,j, maintenance_ids, maintenance_durations) 
    for v,i,j in list(itertools.product(vessel_ids, node_ids, node_ids))}


    vessel_feasible_arcs = {vessel: find_feasible_arcs(vessel, allowed_waiting, vessel_start_ports, vessel_available_days, sailing_costs, arc_sailing_times, all_days, 
    maintenance_vessels, vessel_port_acceptances, port_types, loading_port_ids, maintenance_ids, des_contract_ids, distances, 
    spot_port_ids, loading_days, port_locations, vessel_max_speed, vessel_min_speed, arc_speeds, arc_waiting_times, operational_times,
    fuel_price, total_feasible_arcs, maintenance_start_times, maintenance_durations, maintenance_vessel_ports, unloading_days) 
    for vessel in vessel_ids}


    #######################  INITIALIZING GUROBI ########################
    model = gp.Model()

    # Initializing variables
    
    x = model.addVars(total_feasible_arcs, vtype='B', name='x')

    fob_dimensions = [(f,t) for f in fob_ids for t in fob_days[f]] # Each fob contract has a specific loading node 
    z = model.addVars(fob_dimensions, vtype ='B', name='z')

    charter_dimensions = [(i,t,j) for i in loading_port_ids for t in loading_days for j in (des_contract_ids + spot_port_ids)]
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
    model.addConstrs(init_flow_constr(x, all_days, vessel_ids, node_ids), name='flow')


    # Constraint 5.61
    model.addConstrs(init_artificial_flow_constr(x, vessel_start_ports, vessel_available_days, all_days, vessel_ids),
    name='artificial_node')


    # Constraint 5.8
    model.addConstrs(init_upper_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, node_ids, loading_days,
    partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, upper_partition_demand, des_contract_ids, 
    des_contract_partitions), name='upper_demand')

    model.addConstrs(init_lower_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, node_ids, loading_days,
    partition_days, sailing_time_charter, charter_boil_off, loading_port_ids, lower_partition_demand, des_contract_ids, 
    des_contract_partitions), name='lower_demand')


    #Constraint 5.9 
    model.addConstrs(init_spread_delivery_constraints(x, days_between_delivery, vessel_ids, des_contract_ids, loading_port_ids, 
    unloading_days, loading_days, vessel_available_days), name='spread_delivery')


    # Constraint 5.10
    model.addConstrs(init_fob_max_contracts_constr(z, fob_days, fob_contract_ids), name='fob_max_contracts')


    # Constraint 5.11
    model.addConstrs(init_fob_max_order_constr(z, fob_days, fob_spot_ids, fob_spot_art_port), name='fob_order')


    # Constraint 5.12
    model.addConstrs(init_berth_constr(x, z, w, vessel_ids, node_ids, loading_days, operational_times, des_contract_ids, fob_ids, 
    fob_operational_times, number_of_berths, loading_port_ids), name='berth_constraint')


    # Constraint 5.13 
    model.addConstrs(init_charter_upper_capacity_constr(g, w, charter_vessel_upper_capacity, loading_port_ids, loading_days, 
    spot_port_ids, des_contract_ids), name='charter_upper_capacity')

    model.addConstrs(init_charter_lower_capacity_constr(g, w, charter_vessel_lower_capacity, loading_port_ids, loading_days, 
    spot_port_ids, des_contract_ids), name='charter_lower_capacity')

    return model


def initialize_model1(group, filename):

    # Finding out if it is data from Nigeria or Abu Dabi
    loading_port_ids = set_loading_port_ids(filename)

    ## Initializing data
    data = read_data_file(group, filename)

    return data