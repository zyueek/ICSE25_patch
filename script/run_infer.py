"""
Attempts to run Clang Static Analyzer and FB Infer on all of the projects. One or both
will be unsuccessful for a large portion of projects. Takes some time for larger/complex
projects.
"""

import os
import sys
import time
import subprocess
import logging

# general expected directory layout:
#
# base_folder
# +-- logs
# +-- projects
#     +-- crit 
#         +-- 443_torque
#             +-- repo
#             +-- analysis

base_folder = '/storage2'
sample_folder = os.path.join(base_folder, 'projects')

sev = sys.argv[1]
if sev == 'all':
    severities = ['crit', 'high', 'med', 'low']
else:
    severities = [sev]

jobs = sys.argv[2]

#################################################

def make_configure(repo_folder: str):
    """try to set up project so ./configure will work"""

    # TODO: other ways to try?

    if os.path.exists(os.path.join(repo_folder, 'configure')):
        return

    elif os.path.exists('autogen.sh'):
        subprocess.run(['./autogen.sh'])

    else:
        subprocess.run(['autoreconf', '--install'])


def clean(repo_folder: str):
    """clean and remove configuration that scan-build made"""

    logging.info(f'- clean\tstarting')
    subprocess.run(['make', 'distclean', '-C', repo_folder])
    logging.info(f'- clean\tdone')


def infer(analysis_folder: str, repo_folder: str):

    cur_time = time.strftime("%Y%m%d-%H%M%S")
    logging.info(f'- infer\tstarting\t{cur_time}')

    # folder to redirect infer output to
    infer_folder = os.path.join(analysis_folder, 'infer')

    # run configure
    config_file = os.path.join(repo_folder, 'configure')
    subprocess.run(config_file)

    cur_time = time.strftime("%Y%m%d-%H%M%S")
    logging.info(f'- infer\tconfigured\t{cur_time}')

    # run infer
    #
    # if running manually from inside repo folder, command would be
    # infer run -o ../analysis/infer -- make -j4
    #
    # TODO: REPLACE -j4 WITH THE APPROPRIATE NUMBER 

    try:
        subprocess.run(['infer', 'run', '-o', infer_folder, '--', 'make', '-c', repo_folder, jobs])

    except:
    
        # try once more to run infer
        #
        # if running manually from inside repo folder, command would be
        # infer run -o ../analysis/infer --force-integration make

        cur_time = time.strftime("%Y%m%d-%H%M%S")
        logging.info(f'- infer\trerunning\t{cur_time}')

        try:
            subprocess.run(['infer', 'capture'])
            subprocess.run(['infer', 'run', '-o', infer_folder, '--force-integration', 'make', '-c', repo_folder, jobs])

        except:
            pass

    finally:
        cur_time = time.strftime("%Y%m%d-%H%M%S")
        logging.info(f'- infer\tdone\t{cur_time}')


#################################################

# configure logging
timestr = time.strftime("%Y%m%d-%H%M%S")
log_file = os.path.join('/home/yueke/logs', f'build_{timestr}.log')
targets = logging.StreamHandler(sys.stdout), logging.FileHandler(log_file)
logging.basicConfig(format='%(message)s', level=logging.INFO, handlers=targets)

# now run clang and infer on all projects

# for each severity category folder
for sev_folder in [os.path.join(sample_folder, sev) for sev in severities]:
    # for each project of that severity
    for project_folder in [f.path for f in os.scandir(sev_folder) if f.is_dir()]:

        # folder where the cloned github repo is
        repo_folder = os.path.join(project_folder, 'repo2')

        # folder where the analyzer report will go
        analysis_folder = os.path.join(project_folder, 'analysis') 

        logging.info(f'starting {os.path.basename(project_folder)}')

        # generate a configure file
        try:
            make_configure(repo_folder)
        except:
            logging.info(f'-- make failed {os.path.basename(project_folder)}')
        
        else:

            # run infer
            try:
                infer(analysis_folder, repo_folder)
            except:
                logging.info(f'-- infer failed {os.path.basename(project_folder)}')
            
        finally:
            logging.info(f'done with {os.path.basename(project_folder)}')
    
    logging.info(f'done with {os.path.basename(sev_folder)}')

logging.info('all building analyzing completed')
