#PLOTTING 
import matplotlib as plt
from runModel.initArcs import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import colors



def plot_time_space(model, loading_days_length): 
    for v in model.getVars():
        #print('Var: ', v.x) # v.x is a float
        #print('Variable Name: ', v.varName) # v.varName is a string
        # FIKS PLOTT:
        # MAKING A LIST OUT OF VARIABLE NAME SO WE CAN PLOT:
        if round(v.X,0) == 1.0:
            split = v.varName.split(",")
            split2 = []
            done_splitting = []
            for i in split: 
                p = i.split("[")
                for e in p: 
                    split2.append(e)
            for i in split2: 
                p = i.split("]")
                for e in p: 
                    done_splitting.append(e)
            var_type = done_splitting[0]
            if var_type == 'x':
                arc_as_list = done_splitting[1:-1]
                arc_as_float_list = []
                #print("Arc_as_list: ", arc_as_list)
                for i in arc_as_list[0:2]:
                    arc_as_float_list.append(i)
                for i in arc_as_list[2:3]:
                    arc_as_float_list.append(float(i))
                for i in arc_as_list[3:4]:
                    arc_as_float_list.append(i)
                for i in arc_as_list[4:]:
                    arc_as_float_list.append(float(i))
                #print("Arc_as_float_list: ", arc_as_float_list)
                x_list = [arc_as_float_list[2],arc_as_float_list[4]] #[int(v.varName[4]),int(v.varName[6])]
                #print(x_list)
                y_list = [arc_as_float_list[1],arc_as_float_list[3]] #[int(v.varName[3]),int(v.varName[5])]
                #print(y_list)
                color_vessel = ["wheat", "skyblue", "darksalmon", "magenta","pink"]
                plt.plot(x_list, y_list, color=[np.random.rand(), np.random.rand(), np.random.rand()], linewidth=1)

    plt.xlim([0, loading_days_length+20])
    plt.ylim([0, 19])
    plt.show()

def plot_all_feasible_arcs(vessel_ids, allowed_waiting, last_unloading_day, loading_from_time):
    i = 0
    for vessel in vessel_ids:
        data = find_feasible_arcs(vessel,allowed_waiting)
        #print(data)
        for a in data:
            x_list = [a[2],a[4]]
            y_list = [a[1],a[3]]
            plt.plot(x_list,y_list, color = color[i], linewidth=0.4)
        if i > 3:
            i=0
        else: 
            i+=1
    plt.xlim([0, (last_unloading_day-loading_from_time).days+1])
    plt.ylim([0, 4])
    plt.show()