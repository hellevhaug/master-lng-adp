import os
import datetime

"""
File for writing to txt
"""

def write_to_txt(group, filename, runtime, x, s, g, z):
    path = f'logFiles/{group}/{filename}.txt'
    
    # if the log file does not exist
    if not os.path.exists(path):
        with open(path, "x") as init_txt:
            pass

    # open file and create the csv writer
    with open(path, 'a') as f:
        f.write(f'Group: {group}, File: {filename}, Runtime: {runtime} \n')
        now = datetime.datetime.now()
        f.write(f'Current time: {now.strftime("%Y-%m-%d %H:%M:%S")} \n')
        f.write('\n')
        f.write('--------- X-variables ---------- \n')
        f.write(str(x)+ '\n')
        f.write('\n')
        f.write('--------- S-variables ---------- \n')
        f.write(str(s)+ '\n')
        f.write('\n')
        f.write('--------- G-variables ---------- \n')
        f.write(str(g)+ '\n')
        f.write('\n')
        f.write('--------- Z-variables ---------- \n')
        f.write(str(z)+ '\n')
        f.write('\n\n\n\n\n')
