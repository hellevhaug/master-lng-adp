import os
import datetime
import json


folder = f'analysis'

# if the log file does not exist
if not os.path.exists(folder):
    raise FileNotFoundError('This path does not exists, you should check the json-log-folders')

now = datetime.datetime.now()
filename = now.strftime("%m-%d-%Y, %H-%M")
path = f'{folder}/{filename}.json'


try: 
    with open(path, "x") as init_json:
        pass
except FileExistsError: 
    open(path, 'w').close()


with open(path, 'w') as f:
    main_dict = {}
    main_dict['info'] = 'hei hei dette r en tst2'
    json.dump(main_dict, f, indent=3)