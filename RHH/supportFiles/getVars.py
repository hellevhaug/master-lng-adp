from supportFiles.convertVars import *

def get_vars(group, filename, model):
    
    try:
        x,s,g,z,q,y = convert_vars_to_dicts(model)
        print('Variables returned after one horizon iteration')
        return x,s,g,z,q,y
    
    except:
        try:
            model.computeIIS()
            model.write('solution.ilp')
            print('Could not retrieve variables, infeasible model.')
        except:
            print('Model is feasible, but did not find a feasible solution withing the time limits.')
