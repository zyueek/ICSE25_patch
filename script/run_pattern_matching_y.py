"""
Runs Flawfinder and RATS on all of the projects. These static analyzers
are pretty fast and straightforward to run.

NOTE:
Uses https://github.com/x1angli/cvt2utf to convert everything to UTF-8 as
suggested by Flawfinder. 

"""

import os
import sys
import time
import subprocess
import logging
import smtplib
import ssl
import cvt2utf
import chardet
from tqdm import *
import argparse as arg
# general expected directory layout:
#
# base_folder
# +-- logs
# +-- projects
#     +-- crit 
#         +-- 443_torque
#             +-- repo
#             +-- analysis

base_folder = '/storage2/yueke'
sample_folder = os.path.join(base_folder, 'projects')
severity = sys.argv[1]
if severity == 'all':
    severities = ['low', 'crit', 'med', 'high']
else:
    severities = [severity]

#################################################

def to_utf8(repo_folder: str):

    logging.info(f'- cvt2utf\tstarting')
    print(repo_folder)
#    subprocess.run(['python', 'tools/convert2utf-0.8.5/cvt2utf/cvt2utf.py', 'convert', '-e', 'c', 'h', repo_folder])
    subprocess.run(['cvt2utf',  'convert', "--exts" , "-b","c" ,"cpp",repo_folder])
        # -i c h:   include .c and .h files in the conversion
        # --nobak:  don't generate a ton of .bak files
        #
        # options now seem different. -e for files to change
        # run tool manually with -c to clean up .bak files

    logging.info(f'- cvt2utf\tdone')


def convert_to_utf8(root_directory):
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.endswith('.c') or filename.endswith('.h'):
                file_path = os.path.join(dirpath, filename)

                # Detecting the file encoding
                try:
                    with open(file_path, 'rb') as file:
                        raw_data = file.read()
                        encoding = chardet.detect(raw_data)['encoding']
                except Exception as e:
                    print(f"Error converting {filename} in {dirpath}: {e}")
                # If the file is not already UTF-8, convert and rewrite it
                if encoding != 'utf-8':
                    try:
                        with open(file_path, 'r', encoding=encoding) as file:
                            file_content = file.read()

                        # Writing the file content back in UTF-8
                        with open(file_path, 'w', encoding='utf-8') as file:
                            file.write(file_content)

#                        print(f"Converted {filename} to UTF-8 in {dirpath}.")
                    except Exception as e:
                        print(f"Error converting {filename} in {dirpath}: {e}")




def flawfinder(analysis_folder: str, repo_folder: str): 

    logging.info(f'- flawfinder\tstarting')
    with open(os.path.join(analysis_folder, 'flawfinder.csv'), 'wb+') as out:
        
        subprocess.run(['tools/flawfinder', '--csv', repo_folder], stdout=out, stderr=out)
    logging.info(f'- flawfinder\tdone')



count = 0
#f.path=="/storage2/yueke/projects/crit/1624_opa-ff"
# for each severity category folder
for sev_folder in [os.path.join(sample_folder, sev) for sev in severities]:
    # for each project of that severity
    for project_folder in tqdm([f.path for f in os.scandir(sev_folder) if f.is_dir()]):

        project_id = os.path.basename(project_folder)

        # folder where the cloned github repo is
        repo_folder = os.path.join(project_folder, 'repo')

        # folder where the analyzer report will go
        analysis_folder = os.path.join(project_folder, 'analysis') 

        # make analysis folder if needed
        if not os.path.exists(analysis_folder):
            os.mkdir(analysis_folder)

        # skip android stuff that didn't clone properly
        project_name = project_id.split('_')[1]
        if project_name == 'Android':
            logging.info(f'skipping {project_id}')
            continue

        logging.info(f'starting {project_id}')

        # fix the file encoding
        # this should stop any potential errors from flawfinder
        #
        # ISNT WORKING. SAYS REPO FOLDER IS NOT A FILE OR DIRECTORY
#        to_utf8(repo_folder)
        convert_to_utf8(repo_folder)
        # run each pattern matching tool
        try:
            flawfinder(analysis_folder, repo_folder)
#            rats(analysis_folder, repo_folder)
        except:
            logging.info(f'ERROR analyzing {project_id}')


        logging.info(f'done with {project_id}')
    
    logging.info(f'done with {os.path.basename(sev_folder)}')

logging.info('all pattern matching analysis completed')
