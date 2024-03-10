import os
import json
import pandas as pd
import sys
base_folder = '/storage2/yueke/'
sample_folder = os.path.join(base_folder, 'projects')
severities = ['crit', 'high', 'med', 'low']
#severities = ['crit']
df_list = []
severity = sys.argv[1]
if severity == 'all':
    severities = ['low', 'crit', 'med', 'high']
else:
    severities = [severity]
num=0
import numpy as np
import math
for sev_folder in [os.path.join(sample_folder, sev) for sev in severities]:
    for project_folder in [f.path for f in os.scandir(sev_folder) if f.is_dir()]:
        analysis_folder = os.path.join(project_folder, 'analysis')
        severity = os.path.basename(sev_folder)
        project_name = os.path.basename(project_folder)

        if not os.path.exists(os.path.join(analysis_folder, 'diff.csv')):
            continue
        if not os.path.exists(os.path.join(analysis_folder, 'distances_realloc_ci.csv')):
            continue
        if not os.path.exists(os.path.join(analysis_folder, 'log-distances_ci.csv')):
            temp_df = pd.read_csv(os.path.join(analysis_folder, 'distances_realloc_ci.csv'))
            temp_df = temp_df[['tool','file','func_name', 'linenum', 'filenum','real_loc','type']]
            temp_df['severity'] = severity
            temp_df['project'] = project_name
            temp_df['log_dist']= [np.NaN] * len(temp_df)
            with open(os.path.join(project_folder, 'info.json')) as file:
                project_info = json.load(file)
            temp_df['cwe'] = project_info['cwe_id']
            temp_df['date'] = project_info['publish_date']
            temp_df['loc'] = project_info['loc']
            temp_df['score'] = project_info['score']
            temp_df.to_csv(os.path.join(analysis_folder, 'alldist_ci.csv'))
            continue
        temp_df = pd.read_csv(os.path.join(analysis_folder, 'distances_realloc_ci.csv'))
        log_df=pd.read_csv(os.path.join(analysis_folder, 'log-distances_ci.csv'))
        # temp_df = temp_df[['tool', 'logical_dists', 'line_dists', 'file_dists']]
        temp_df = temp_df[['tool','file','func_name' ,'linenum', 'filenum','real_loc','type']]
#        if all(math.isnan(x) for x in loglist):
#          continue
        temp_df['severity'] = severity
        temp_df['project'] = project_name
        temp_df['log_dist']=log_df['logical_dist']

#        temp_df['project']=[project_folder]*len(log_df)
#        temp_df['severity']=[sev_folder]*len(log_df)
        # get the cwe and date from info.json
        with open(os.path.join(project_folder, 'info.json')) as file:
            project_info = json.load(file)
        temp_df['cwe'] = project_info['cwe_id']
        temp_df['date'] = project_info['publish_date']
        temp_df['loc'] = project_info['loc']
        temp_df['score'] = project_info['score']
#        print(temp_df)
        num+=1
        print(num)
        print(project_name)
        temp_df.to_csv(os.path.join(analysis_folder, 'alldist_ci.csv'))
#        df_list.append(temp_df)
           
#mega_df = pd.concat(df_list, ignore_index=True)
#mega_df.to_csv(os.path.join(sample_folder, 'all_info_2dis.csv'))
