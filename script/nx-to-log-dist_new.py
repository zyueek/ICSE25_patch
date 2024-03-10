import os
import re
import time
import logging
import sys
import networkx as nx
import pandas as pd
import numpy as np
from Levenshtein import distance

def find_closest_key(value, mapping, max_distance=3):
    if value in mapping:
        return mapping[value]
    else:
        closest_key, closest_distance = min(
            ((key, distance(value, key)) for key in mapping.keys()),
            key=lambda item: item[1]
        )
        if closest_distance <= max_distance:
            return mapping[closest_key]
        else:
            return  999 # Or any other value indicating a failed match
def find_node_with_subset(node_list, target_subset):
    for node_name in node_list:
        if target_subset in node_name:
            return node_name
    return None

pd.options.mode.chained_assignment = None

base_folder = '/storage2/yueke'
sample_folder = os.path.join(base_folder, 'projects')

severity = sys.argv[1]
if severity == 'all':
    severities = ['low', 'crit', 'med', 'high']
else:
    severities = [severity]

# configure logging
timestr = time.strftime("%Y%m%d-%H%M%S")
log_file = os.path.join('/home/cuthbene/logs/', f'logdist_{timestr}.log')
targets = logging.StreamHandler(sys.stdout), logging.FileHandler(log_file)
logging.basicConfig(format='%(message)s', level=logging.INFO, handlers=targets)
#f.path=="/storage2/yueke/projects/crit/1624_opa-ff"
for sev_folder in [os.path.join(sample_folder, sev) for sev in severities]:
    for project_folder in [f.path for f in os.scandir(sev_folder) if f.is_dir()]:
        logging.info(f'starting {os.path.basename(project_folder)}')

        analysis_folder = os.path.join(project_folder, 'analysis')
        repo_folder = os.path.join(project_folder, 'repo')

        if not os.path.exists(os.path.join(analysis_folder, 'caller_graph.csv')):
            continue

        # try:
        caller_df = pd.read_csv(os.path.join(analysis_folder, 'caller_graph.csv'), index_col=0)
        caller = nx.from_pandas_adjacency(caller_df)
        callee_df = pd.read_csv(os.path.join(analysis_folder, 'callee_graph.csv'), index_col=0)
        callee = nx.from_pandas_adjacency(callee_df)

        logging.info('-- imported from csv')

        # now that we have the graphs, need to get location of patch
        patches = pd.read_csv(os.path.join(analysis_folder, 'diff.csv'), index_col=0)

        # also get the tool data
        tool_data = pd.read_csv(os.path.join(analysis_folder, 'tool_data.csv'), index_col=0)
        tool_data = tool_data.assign(location=tool_data.agg('{0[file]}-:{0[func_name]}'.format, axis=1))
        callername=list(caller_df.columns)
        calleename=list(callee_df.columns)
        # calculate distances
        logical_distances = [np.NaN] * len(tool_data)
        for _, row in patches.iterrows():
            # idea is to get distance from patched function to every other function
            # then fill in the distances in the table
            
            # want to go from tool flag -> ?? -> patched func
            # therefore patched func is target
            try:
#                target = f"{row['filename']}-:{row['function']}"
                target = f"{row['function'][1:]}"
                logging.info(f'-- starting analysis on {target}')
            except:
                logging.info(f'-- skipping')
                continue

            closest_target_caller = find_node_with_subset(callername, target)
            closest_target_callee = find_node_with_subset(calleename, target)
            if closest_target_caller is not None:
                target=closest_target_caller
            elif closest_target_callee is not None:
                target=closest_target_callee
            else:
                print("No close enough target found")
                continue
            # calculate the length from target to each other function
            if closest_target_caller in caller:
                caller_paths = nx.shortest_path(caller, closest_target_caller)
                caller_lens = {k.replace('rc/','') if k.startswith('rc/') else k: len(v) for k, v in caller_paths.items()}
#                print(caller_paths)
                # map to the tool data
                caller_dists = tool_data['location'].map(lambda x: find_closest_key(x, caller_lens))
#                caller_dists = tool_data['location'].map(lambda x: find_element_with_substring(x, callername))
 #               print(tool_data['location'])

                # update if shorter than the current shortest
                logical_distances = np.fmin(list(caller_dists), logical_distances)
                # print('caller ', logical_distances)

                logging.info('-- done with caller dist')
            
            if target in callee:
                # now do the same thing but for the callee
                callee_paths = nx.shortest_path(callee, target=target)
                callee_lens = {k.replace('src/','') if k.startswith('src/') else k: len(v) for k, v in callee_paths.items()}
                callee_dists = tool_data['location'].map(lambda x: find_closest_key(x, callee_lens)) * -1

                callee_dists = list(callee_dists)
            
                # update if shorter than the current shortest
                logical_distances = pd.Series(np.where(np.abs(callee_dists) < logical_distances, callee_dists, logical_distances))
                # for i, val in enumerate(logical_distances):
                # print('callee ', logical_distances)

                logging.info('-- done with callee dist')

        # save the distances
        # print(type(logical_distances))
        tool_data['logical_dist'] = list(logical_distances)
        print(tool_data['logical_dist'].value_counts())
        print(list(logical_distances))
        tool_data.to_csv(os.path.join(analysis_folder, 'log-distances.csv'))

        # except:
        #     logging.info(f'failed on {os.path.basename(project_folder)}')

    logging.info(f'DONE with {os.path.basename(sev_folder)}')

logging.info(f'done with everything')
