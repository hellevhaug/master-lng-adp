NIG = ['NGBON']
ABU1 = ['FU']
ABU2 = ['FU','DI']
FAKEFOB = 'ART_FIC'

CHARTER_BOIL_OFF = 0.0012 # Hardkodet 
TANK_LEFTOVER_VALUE = {'NGBON':40, 'FU':40, 'DI':40} # Hardkodet

CHARTER_VESSEL_UPPER_CAPACITY = 160000
CHARTER_VESSEL_LOWER_CAPACITY = 135000

############# The important constants ################

MINIMUM_CHARTER_PERIOD = 60 #Number of days a vessel at least must be chartered out (if chartered out)
MINIMUM_DAYS_BETWEEN_DELIVERY = 4
ALLOWED_WAITING = 7
PRODUCTION_SCALE_RATE = 0.3
CHARTER_OUT_FRICTION = 0.05

######################################################

BASIC_MODEL = 'basic'
VARIABLE_PRODUCTION_MODEL = 'variableProduction'
CHARTER_OUT_MODEL = 'charterOut'
MODEL_TYPES = [BASIC_MODEL,VARIABLE_PRODUCTION_MODEL,CHARTER_OUT_MODEL]

################## Plot constants ####################
UNLOADING = 'unloading'
LOADING = 'loading'


def read_important_constants():
    return MINIMUM_CHARTER_PERIOD,MINIMUM_DAYS_BETWEEN_DELIVERY,ALLOWED_WAITING,PRODUCTION_SCALE_RATE,CHARTER_OUT_FRICTION
