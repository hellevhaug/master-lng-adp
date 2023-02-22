import gurobipy as gp

## Basic model 

# Initialize objective
def init_objective(x, z, s, w, g, fob_revenues, fob_demands, fob_ids, fob_days, des_contract_revenues, vessel_capacities, vessel_boil_off_rate,
vessel_ids, loading_port_ids, loading_days, spot_port_ids, all_days, sailing_time_charter, unloading_days, charter_boil_off, 
tank_leftover_value, vessel_available_days, des_contract_ids, sailing_costs, charter_total_cost, des_spot_ids):

    objective = (gp.quicksum(fob_revenues[f,t]*fob_demands[f]*z[f,t] 
    for f in fob_ids for t in fob_days[f]) + 
    gp.quicksum(des_contract_revenues[j,t_]*vessel_capacities[v]*(1-(t_-t)*vessel_boil_off_rate[v])*x[v,i,t,j,t_] 
    for v in vessel_ids for i in loading_port_ids for t in loading_days for j in spot_port_ids for t_ in all_days 
    if (v,i,t,j,t_) in x.keys()) + 
    gp.quicksum(des_contract_revenues[j,min(t+sailing_time_charter[i,j], len(unloading_days[j]))]*g[i,t,j]*(1-sailing_time_charter[i,j]*charter_boil_off)
    for i in loading_port_ids for j in spot_port_ids for t in unloading_days[j]) + 
    gp.quicksum(tank_leftover_value[i]*s[i, len(loading_days)] for i in loading_port_ids) +
    gp.quicksum(vessel_capacities[v]*(1-(t_-t)*vessel_boil_off_rate[v])*des_contract_revenues[j,t_]*x[v,i,t,j,t_]
    for j in des_contract_ids for v in vessel_ids for i in loading_port_ids for t in vessel_available_days[v] for t_ in unloading_days[j] # Left-hand sums
    if (v,i,t,j,t_) in x.keys()) + 
    gp.quicksum(g[i,t,j]*(1-sailing_time_charter[i,j]*charter_boil_off)*des_contract_revenues[j,t+sailing_time_charter[i,j]] 
    for j in des_contract_ids for i in loading_port_ids for t in loading_days if (t+sailing_time_charter[i,j]) in unloading_days[j])-
    gp.quicksum(sailing_costs[v,i,t,j,t_]*x[v,i,t,j,t_] for v,i,t,j,t_ in x.keys())-
    gp.quicksum(charter_total_cost[i,t,j]*w[i,t,j] for i in loading_port_ids for t in loading_days for j in (des_contract_ids+des_spot_ids)))

    return objective


# Initialize initial inventory constraints for loading ports 
def init_initial_loading_inventory_constr(s, g, z, x, production_quantities, vessel_capacities, vessel_ids,
    des_contract_ids, all_days,fob_demands, fob_ids, loading_port_ids, loading_days, initial_inventory):

    initial_loading_inventory_constraints = (s[i,t]==initial_inventory[i]+production_quantities[i,t]
    -gp.quicksum(vessel_capacities[v]*x[v,i,t,j,t_] 
    for v in vessel_ids for j in des_contract_ids for t_ in all_days if (v,i,t,j,t_) in x.keys())
    - gp.quicksum(g[i,t,j] for j in des_contract_ids)
    - gp.quicksum(fob_demands[f]*z[f,t] 
    for f in fob_ids if (f,t) in z.keys())
    for i in loading_port_ids for t in loading_days[:1])

    return initial_loading_inventory_constraints


# Initialize loading inventory constraints
def init_loading_inventory_constr(s, g, z, x, production_quantities, vessel_capacities, vessel_ids,
    des_contract_ids, all_days,fob_demands, fob_ids, loading_port_ids, loading_days):

    loading_inventory_constraints = (s[i,t]==s[i,(t-1)]+production_quantities[i,t]-gp.quicksum(vessel_capacities[v]*x[v,i,t,j,t_] 
    for v in vessel_ids for j in des_contract_ids for t_ in all_days if (v,i,t,j,t_) in x.keys())
    - gp.quicksum(g[i,t,j] for j in des_contract_ids)
    - gp.quicksum(fob_demands[f]*z[f,t] 
    for f in (fob_ids) if (f,t) in z.keys())
    for i in loading_port_ids for t in loading_days[1:])

    return loading_inventory_constraints


# Initialize upper inventory constraints
def init_upper_inventory_constr(s, max_inventory):

    upper_inventory_constraints = (s[i,t] <= max_inventory[i] for i,t in s.keys())

    return upper_inventory_constraints


# Initialize lower inventory constraints
def init_lower_inventory_constr(s, min_inventory):

    lower_inventory_constraints = (min_inventory[i] <= s[i,t] for i,t in s.keys())

    return lower_inventory_constraints


# Initialize maintenance constraints
def init_maintenance_constr(x, maintenance_vessel_ports, maintenance_vessels):

    maintenance_constraints = (x.sum(v,'*','*',maintenance_vessel_ports[v],'*') == 1 for v in maintenance_vessels)
    
    return maintenance_constraints


# Initialize flow constraints
def init_flow_constr(x, all_days, vessel_ids, node_ids):

    flow_constraints = (x.sum(v,'*', [0]+all_days[:t],j,t)== x.sum(v,j,t,'*',all_days[t+1:]+[all_days[-1]+1]) 
    for v in vessel_ids for j in node_ids for t in all_days)

    return flow_constraints


# Initialize artificial flow constraints
def init_artificial_flow_constr(x, vessel_start_ports, vessel_available_days, all_days, vessel_ids):

    artificial_flow_constraints = (x[v,'ART_START',0,vessel_start_ports[v],vessel_available_days[v][0]]+
    x[v,'ART_START',0,'ART_START',all_days[-1]+1]==1 for v in vessel_ids)

    return artificial_flow_constraints


# Initialize upper demand constraints
def init_upper_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, node_ids, loading_days, partition_days, 
    sailing_time_charter, charter_boil_off, loading_port_ids, upper_partition_demand, des_contract_ids, des_spot_ids,
    des_contract_partitions):

    upper_demand_constraints = (gp.quicksum(vessel_capacities[v]*(1-(t_-t)*vessel_boil_off_rate[v])*x[v,i,t,j,t_]
    for v in vessel_ids for i in node_ids for t in loading_days for t_ in partition_days[p] # Left-hand sums
    if (v,i,t,j,t_) in x.keys()) +
     gp.quicksum(g[i,t,j]*(1-sailing_time_charter[i,j]*charter_boil_off) 
    for i in loading_port_ids for t in loading_days if t+sailing_time_charter[i,j] in partition_days[p]) # Only if the arc is feasible
    <=upper_partition_demand[j,p] #
    for j in (des_contract_ids+des_spot_ids) for p in des_contract_partitions[j])

    return upper_demand_constraints


# Initialize lower demand constraints
def init_lower_demand_constr(x, g, vessel_capacities, vessel_boil_off_rate, vessel_ids, node_ids, loading_days, partition_days, 
    sailing_time_charter, charter_boil_off, loading_port_ids, lower_partition_demand, des_contract_ids, des_spot_ids,
    des_contract_partitions):

    lower_demand_constraints = (
    lower_partition_demand[j,p]<=(gp.quicksum(vessel_capacities[v]*(1-(t_-t)*vessel_boil_off_rate[v])*x[v,i,t,j,t_]
    for v in vessel_ids for i in node_ids for t in loading_days for t_ in partition_days[p] # Left-hand sums
    if (v,i,t,j,t_) in x.keys())
    +gp.quicksum(g[i,t,j]*(1-sailing_time_charter[i,j]*charter_boil_off) for i in loading_port_ids for t in loading_days 
    if t+sailing_time_charter[i,j] in partition_days[p])) # Only if the arc is feasible
    for j in (des_contract_ids+des_spot_ids) for p in des_contract_partitions[j])

    return lower_demand_constraints


# Initialize spread constraints
def init_spread_delivery_constraints_old(x, days_between_delivery, vessel_ids, des_contract_ids, loading_port_ids, unloading_days, loading_days, vessel_available_days):

    spread_delivery_constraints = (
        x.sum(vessel_ids,loading_days,vessel_available_days, j, unloading_days[j][t_+1:]+[t_+days_between_delivery[j]]) <= 1
        for j in des_contract_ids for t_ in unloading_days[j])
    return spread_delivery_constraints


def init_spread_delivery_constraints(x, vessel_ids, loading_port_ids, vessel_available_days, des_contract_ids, unloading_days,
    days_between_delivery, des_spot_ids):
    spread_delivery_constraints = (gp.quicksum(x[v,i,t,j,tau] for v in vessel_ids for i in loading_port_ids 
    for t in vessel_available_days[v] for tau in unloading_days[j][(t_-1):(t_-1)+days_between_delivery[j]] 
    if (v,i,t,j,tau) in x.keys()) <= 1 
    for j in (des_contract_ids+des_spot_ids) for t_ in unloading_days[j][:len(unloading_days[j])+1-days_between_delivery[j]])

    return spread_delivery_constraints

    
# Initialize fob max contracts constraints
def init_fob_max_contracts_constr(z, fob_days, fob_contract_ids):

    fob_max_contracts_constraints = (z.sum(f,fob_days[f])==1 for f in fob_contract_ids)

    return fob_max_contracts_constraints


# Initialize fob max order constraints
def init_fob_max_order_constr(z, fob_days, fob_spot_ids, fob_spot_art_ports):

    fob_max_order_constraints = (z.sum(f,fob_days[f])<=1 for f in list(set(fob_spot_ids) - set([fob_spot_art_ports.values()])))

    return fob_max_order_constraints


# Initialize berth constraints
def init_berth_constr(x, z, w, vessel_ids, node_ids, loading_days, operational_times, des_contract_ids, fob_ids, fob_operational_times,
    number_of_berths, loading_port_ids):

    berth_constraints = (gp.quicksum(x[v,i,t,j,tau] for v in vessel_ids for i in node_ids for t in loading_days 
    for tau in range(t_,t_+operational_times[v,i,j]+1) if (v,i,t,j,tau) in x.keys())
    + gp.quicksum(w[j,t_,j_] for j_ in des_contract_ids)
    + gp.quicksum(z[f_v,j,f_tau] for f_v in fob_ids 
    for f_tau in range(t_,t_+fob_operational_times[f_v,j]) if (f_v,j,f_tau) in x.keys())
    <= number_of_berths[j] for j in loading_port_ids for t_ in loading_days)

    return berth_constraints


# Initialize charter upper capacity constraints
def init_charter_upper_capacity_constr(g, w, charter_vessel_upper_capacity, loading_port_ids, loading_days, spot_port_ids, des_contract_ids):

    charter_upper_capacity_contraints = (g[i,t,j]<=(charter_vessel_upper_capacity)*w[i,t,j] for i in loading_port_ids for t in loading_days
    for j in (spot_port_ids+des_contract_ids))

    return charter_upper_capacity_contraints


# Initialize charter lower capacity constraints 
def init_charter_lower_capacity_constr(g, w, charter_vessel_lower_capacity, loading_port_ids, loading_days, spot_port_ids, des_contract_ids):

    charter_lower_capacity_contraints = (charter_vessel_lower_capacity*w[i,t,j]<= g[i,t,j] for i in loading_port_ids for t in loading_days 
    for j in (spot_port_ids+des_contract_ids))

    return charter_lower_capacity_contraints


## Extension 1 - Variable production 

# Initialize lower production rate constraints
def init_lower_prod_rate_constr(q, lower_prod_rate, loading_days, loading_port_ids):
    
    lower_prod_rate_constr = (lower_prod_rate[i] <= q[i, t] for i in loading_port_ids for t in loading_days)

    return lower_prod_rate_constr


# Initialize upper production rate constraints
def init_upper_prod_rate_constr(q, upper_prod_rate, loading_days, loading_port_ids):

    upper_prod_rate_constr = (q[i,t]<= upper_prod_rate[i] for i in loading_port_ids for t in loading_days)

    return upper_prod_rate_constr


## Extension 2 - Chartering out own vessels 

# Initialize the objective function with the possibility of chartering out
#NB: charter revenue per vessel must be defined, the parameter is named: daily_charter_revenue and indexed with v

def init_objective_extension_2(x, z, s, w, g, fob_revenues, fob_demands, fob_ids, fob_days, des_contract_revenues, vessel_capacities, vessel_boil_off_rate,
vessel_ids, loading_port_ids, loading_days, spot_port_ids, all_days, sailing_time_charter, unloading_days, charter_boil_off, 
tank_leftover_value, vessel_available_days, des_contract_ids, sailing_costs, charter_total_cost, des_spot_ids, daily_charter_revenue):

    objective_extension_2 = (gp.quicksum(fob_revenues[f,t]*fob_demands[f]*z[f,t] 
    for f in fob_ids for t in fob_days[f]) + 
    gp.quicksum(des_contract_revenues[j,t_]*vessel_capacities[v]*(1-(t_-t)*vessel_boil_off_rate[v])*x[v,i,t,j,t_] 
    for v in vessel_ids for i in loading_port_ids for t in loading_days for j in spot_port_ids for t_ in all_days 
    if (v,i,t,j,t_) in x.keys()) + 
    gp.quicksum(des_contract_revenues[j,min(t+sailing_time_charter[i,j], len(unloading_days[j]))]*g[i,t,j]*(1-sailing_time_charter[i,j]*charter_boil_off)
    for i in loading_port_ids for j in spot_port_ids for t in unloading_days[j]) + 
    gp.quicksum(tank_leftover_value[i]*s[i, len(loading_days)] for i in loading_port_ids) +
    gp.quicksum(vessel_capacities[v]*(1-(t_-t)*vessel_boil_off_rate[v])*des_contract_revenues[j,t_]*x[v,i,t,j,t_]
    for j in des_contract_ids for v in vessel_ids for i in loading_port_ids for t in vessel_available_days[v] for t_ in unloading_days[j] # Left-hand sums
    if (v,i,t,j,t_) in x.keys()) + 
    gp.quicksum(g[i,t,j]*(1-sailing_time_charter[i,j]*charter_boil_off)*des_contract_revenues[j,t+sailing_time_charter[i,j]] 
    for j in des_contract_ids for i in loading_port_ids for t in loading_days if (t+sailing_time_charter[i,j]) in unloading_days[j])-
    gp.quicksum(sailing_costs[v,i,t,j,t_]*x[v,i,t,j,t_] for v,i,t,j,t_ in x.keys())-
    gp.quicksum(charter_total_cost[i,t,j]*w[i,t,j] for i in loading_port_ids for t in loading_days for j in (des_contract_ids+des_spot_ids)))
    + gp.quicksum(daily_charter_revenue[v]*x[v,0,t,0,t_] for v in vessel_ids for t in loading_days for t_ in unloading_days)

    return objective_extension_2

# Initialize chartering out max one period constraints
def init_charter_one_period_constr(x, all_days, node_ids, vessel_ids):
    
    charter_one_period_constr = (x.sum(v,'*','*', 0, '*') <= 1 for v in vessel_ids)

    return charter_one_period_constr

# Initialize charter flow constraints
def init_charter_flow_constraints(x, vessel_ids, node_ids, loading_port_ids, all_days, loading_days):

    charter_flow_constraints = (x.sum('*','*',t,0,t) == x.sum('*',0,t_,j,t_) for t in loading_days for j in loading_port_ids for t_ in all_days)
    
    return charter_flow_constraints

# Initialize minimum number of time periods charter in a row 
def init_min_charter_time_constr(x, vessel_ids, all_days, minimum_charter_period): 

    min_charter_time_constr = (x.sum(v,0,t,0,all_days[t+1:]+[all_days[-1]+1]) >= minimum_charter_period for v in vessel_ids for t in all_days)

    return min_charter_time_constr


## Extension 3 - Split Deliveries 
