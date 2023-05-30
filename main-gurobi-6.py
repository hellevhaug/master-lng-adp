from main import*

runtime = 60*60*3
modelType = BASIC_MODEL

try:
    run_one_instance('A-2L-B', 'A-2L-6U-30F-15V-180D', runtime, modelType)
except:
    print('krasj1')
try:
    run_one_instance('N-1L-B', 'N-1L-13U-10F-23V-120D', runtime, VARIABLE_PRODUCTION_MODEL)
except: 
    print('krasj1')

try:
    run_one_instance('N-1L-B', 'N-1L-13U-10F-23V-120D', runtime, CHARTER_OUT_MODEL)
except: 
    print('krasj1')

try:
    run_one_instance('N-1L-B', 'N-1L-13U-10F-23V-120D', runtime, COMBINED_MODEL)
except: 
    print('krasj1')