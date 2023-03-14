# This is a testfile to test random things

print('Hello, this String is written by Helle')


#
#  Hei
#             ...           ...
#        ..      ..     ..      ..
#      ..            .            ..
#     ..                            ..
#     .                             .
#      ..            Hei          ..
#        ..                     ..
#          ..                 ..
#            ..             ..
#              ..         ..
#                ..     ..
#                  .. ..
#                    .

print('Feel free to add more things')
print("Dette er så pent")


"""

def run_one_instance_basic(group, filename, runtime):
    # Running the model with given group, filename and runtime (including logging the file, this is done in run_model)
    model = run_basic_model(group, filename, runtime, f'Running file: {filename}')
    #model.computeIIS()
    #model.write('solution.ilp')

    # Converting gurobi variables to dictionaries, because they are easier to work with
    x,s,g,z,q,y = convert_vars_to_dicts(model)

    # Writing to txt-file, not necessary per now
    # write_to_txt(group, filename, runtime, x, s, g, z)

    # Writing variables to json-file
    write_to_json(group, filename, runtime, x, s, g, z, q, y, 'Basic model with minimum spread')


def run_one_instance_variable_production(group, filename, runtime):
    # Running the model with given group, filename and runtime (including logging the file, this is done in run_model)
    model = run_variable_production_model(group, filename, runtime, f'Running file: {filename}')

    # Converting gurobi variables to dictionaries, because they are easier to work with
    x,s,g,z,q,y = convert_vars_to_dicts(model)

    # Writing to txt-file, not necessary per now
    # write_to_txt(group, filename, runtime, x, s, g, z)

    # Writing variables to json-file
    write_to_json(group, filename, runtime, x, s, g, z, q, y, 'Model with variable production')


def run_one_instance_charter_out(group, filename, runtime):
    # Running the model with given group, filename and runtime (including logging the file, this is done in run_model)
    model = run_charter_out_model(group, filename, runtime, f'Running file: {filename}')
    #model.computeIIS()
    #model.write('solution.ilp')

    # Converting gurobi variables to dictionaries, because they are easier to work with
    x,s,g,z,q,y = convert_vars_to_dicts(model)

    # Writing to txt-file, not necessary per now
    # write_to_txt(group, filename, runtime, x, s, g, z)

    # Writing variables to json-file
    write_to_json(group, filename, runtime, x, s, g, z, q, y,'Model with chartering out')

"""