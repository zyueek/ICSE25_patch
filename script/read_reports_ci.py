"""
Goes through each SAST report and puts the locations of all the warnings
into a csv called tool_data.csv in the analysis folder.

Example:

| tool  | file              | line_num  | func_name     |
+-------+-------------------+-----------+---------------+
| infer | inflate.c	        | 623       | inflate       |
| rats  | test/infcover.c   | 392       | cover_wrap    |

"""

import json
import os
import pandas as pd
from bs4 import BeautifulSoup
import bisect
from functools import lru_cache
import logging
import time
import sys
from tqdm import *
pd.options.mode.chained_assignment = None

# general expected directory layout:
#
# base_folder
# +-- logs
# +-- projects
#     +-- crit 
#         +-- 443_torque
#             +-- repo
#             +-- analysis

base_folder = '/storage2/yueke/'
sample_folder = os.path.join(base_folder, 'projects')

severity = sys.argv[1]
if severity == 'all':
    severities = ['low', 'crit', 'med', 'high']
else:
    severities = [severity]

@lru_cache(maxsize=None)
def get_func_start_lines(repo_folder: str, c_file: str) -> dict:
    """
    @return func_start_lines - {start_line: func_name, start_line: func_name}
    """

    # run ctags on the changed file
    command = f'/storage2/yueke/tools/ctags -x --c-kinds=f {os.path.join(repo_folder, c_file)}'
    ctags_headers = os.popen(command).readlines()

    # find start lines for each function
    func_start_lines = {}
    for target_func in ctags_headers:
        ctag_tokens = [x.strip() for x in target_func.split()]
        func_name = ctag_tokens[0]
        func_start_line = ctag_tokens[2]
        
        func_start_lines[func_start_line] = func_name

    return func_start_lines
def getfilename(path):
    split_parts = path.split("repo/")
    if len(split_parts) > 1:
        result = split_parts[1]
    else:
        result = None
    return result
def line_in_func(func_start_lines: dict, hit_line: int) -> str:

    dict_keys = [int(x) for x in list(func_start_lines.keys())]
    dict_keys.sort()

    if not dict_keys:
        return None

    if hit_line < min(dict_keys):
        return None
    ind = bisect.bisect_left(dict_keys, hit_line) - 1
    func_key = dict_keys[ind]
    func_name = func_start_lines[str(func_key)]

    return func_name

def read_infer(analysis_folder: str):

    with open(os.path.join(analysis_folder, 'infer', 'report.json'), 'r') as f:
        infer_report = json.load(f)

    df = pd.DataFrame(columns=['tool', 'file', 'line_num', 'func_name','type'])
    
    for report in infer_report:
        c_file = report['file']
        line_num = report['line']
        func_name = report['procedure']
        bugtype=report['bug_type']
        row = {'tool': 'infer', 'file': c_file, 'line_num': line_num, 'func_name': func_name,'type':bugtype}

        df = df.append(row, ignore_index=True)

    return df

def read_clang(analysis_folder: str):

    html_folder = [x[0] for x in os.walk(os.path.join(analysis_folder, 'clang'))][1]
    with open(os.path.join(html_folder, 'index.html'), 'r') as f:
        soup = BeautifulSoup(f, features='lxml')

    table = soup.find('table', attrs={'class':'sortable'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')

    data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [x.text.strip() for x in cols]
        data.append(['clang'] + [x for x in cols if x])
    
    if data:
        df = pd.DataFrame(data)
        df = df[[0, 3, 5, 4,2]]
#        print(data)
        df.columns = ['tool', 'file', 'line_num', 'func_name','type']
        
        return df









#f.path=="/storage2/yueke/projects/crit/827_git"
for sev_folder in [os.path.join(sample_folder, sev) for sev in severities]:
    for project_folder in tqdm([f.path for f in os.scandir(sev_folder) if f.is_dir()]):
        repo_folder = os.path.join(project_folder, 'repo')
        analysis_folder = os.path.join(project_folder, 'analysis')
        project_name = os.path.basename(project_folder)

        # skip stuff
        # if project_name.split('_')[1] == 'Chrome' or project_name.split('_')[1] == 'linux':
        #     logging.info(f'-- skipping {project_name}')
        #     continue

        repo_folder = os.path.join(project_folder, 'repo')
        if not os.path.exists(repo_folder):
            logging.info(f'-- {project_name} repo not cloned')
            continue
        

        # if os.path.exists(os.path.join(analysis_folder, 'tool_data.csv')):
        #     logging.info(f'-- {project_name} already read')
        #     continue

        df = pd.DataFrame(columns=['tool', 'file', 'line_num', 'func_name'])
        if not os.path.exists(os.path.join(analysis_folder, 'tool_data_ci.csv')):
           print(f'-- {project_name} ci not run')
           continue
        print(f'starting {os.path.basename(project_folder)}')
        df_origin=pd.read_csv(os.path.join(analysis_folder, 'tool_data_ci.csv'))
        if len(df_origin)==0:
           print(f'-- {project_name} ci not run')
           continue

        try:
            infer_df = read_infer(analysis_folder)
            print(infer_df)
        except:
            logging.info(f'- infer failed {os.path.basename(project_folder)}')
            infer_df = df
            

        try:    
            clang_df = read_clang(analysis_folder)
        except:
            logging.info(f'- clang failed {os.path.basename(project_folder)}')
            clang_df = df



        # report_locations = pd.concat([df, infer_df, clang_df, cppcheck_df, rats_df, flawfinder_df])
        report_locations = pd.concat([df, infer_df, clang_df])
        print(report_locations)
        report_locations.to_csv(os.path.join(analysis_folder, 'tool_data_ci.csv'))

        print(f'done with {os.path.basename(project_folder)}')
        get_func_start_lines.cache_clear()

    print(f'done with {os.path.basename(sev_folder)}')
    logging.info(f'done with {os.path.basename(sev_folder)}')

logging.info(f'done with everything')
