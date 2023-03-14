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

data = read_solved_json_file('jsonFiles/N-1L-45D/N-1L-6U-13F-18V-45D-a/03-14-2023, 13-30.json')
get_x_vars(data)