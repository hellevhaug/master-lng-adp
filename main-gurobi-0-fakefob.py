from main import*

runtime = 60*60*3
modelType = BASIC_MODEL

try: 
    run_one_instance('A-2L-C', 'A-2L-6U-8F-15V-120D', runtime, VARIABLE_PRODUCTION_MODEL)
except: 
    print('krasj')
try:
    run_one_instance('N-1L-B', 'N-1L-13U-10F-23V-120D', runtime, VARIABLE_PRODUCTION_MODEL)
except:
    print('krasj2')


