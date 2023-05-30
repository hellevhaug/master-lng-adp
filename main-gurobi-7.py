from main import*

runtime = 60*60*3
modelType = BASIC_MODEL

try:
    run_one_instance('N-1L-D', 'N-1L-14U-21F-23V-180D', runtime, modelType)
except: 
    print('krasj1')

try:
    run_one_instance('A-2L-C', 'A-2L-6U-8F-15V-120D', runtime, VARIABLE_PRODUCTION_MODEL)
except: 
    print('krasj1')

try:
    run_one_instance('A-2L-C', 'A-2L-6U-8F-15V-120D', runtime, CHARTER_OUT_MODEL)
except: 
    print('krasj1')

try:
    run_one_instance('A-2L-C', 'A-2L-6U-8F-15V-120D', runtime, COMBINED_MODEL)
except: 
    print('krasj1')