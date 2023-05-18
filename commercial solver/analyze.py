from analysis.exploreSolution import *
from analysis.exploreInstance import *

"""
File for analyzing stuffz
How to find path for file: right-click, and then choose "copy relative path"
"""

def analyze_solution(path):

    print('----------------------------------------------------------------------------')
    print(f'Analyzing soltion for instance with location: {path}\n')
    print('----------------------------------------------------------------------------')

    return 0


def analyze_instance(group, filename):

    print('-------------------------------------------')
    print(f'Analyzing instance {filename}')
    print('-------------------------------------------\n')

    explore_instance(group, filename)

    return 0


#########################################################
############### Run stuffz below here ###################
#########################################################


#group1 = 'N-1L-180D'
#filename1 = 'N-1L-7U-44F-23V-180D-a'
group1 = 'A-2L-180D'
filename1 = 'A-2L-6U-18F-15V-180D-b'

#analyze_instance(group1, filename1)



################## EXAMPLE FOR READING DATA FROM A SOLUTION ###################################

data = read_solved_json_file('jsonFiles/N-1L-45D/N-1L-6U-13F-18V-45D-a/03-14-2023, 13-30.json')
x_dict = get_x_vars(data)
s_dict = get_s_vars(data)
g_dict = get_g_vars(data)
z_dict = get_z_vars(data)


# Reading through x-variable (arcs)
for (v, i, t, j, t_), value in x_dict.items():
    print(f'Vessel {v} sailed from port {i} to port {j} from time {t} to time {t_}')
print('\n')

# Reading through s-variable (inventory level)
for (i, t), value in s_dict.items():
    print(f'Inventory level for loading port {i} in time {t}: {value}')
print('\n')

# Reading through g-variable (amount chartered)
for (i, t, j), value in g_dict.items():
    print(f'Chartered from loading port {i} to contract {j} in time {t}, amount: {value}')
print('\n')

# Reading through z-variable (fob contracts)
for (f, t), value in z_dict.items():
    print(f'FOB-contract {f} was picked up at time {t}')
print('\n')



