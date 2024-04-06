""":q
Attempts to run Clang Static Analyzer.
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

#################################################

def make_configure(repo_folder: str):
    """try to set up project so ./configure will work"""

    if os.path.exists(os.path.join(repo_folder, 'configure')):
        return

    elif os.path.exists(os.path.join(repo_folder, 'autogen.sh')):
        cmd = f'{repo_folder}/autogen.sh'
        logging.info(f'-- running autogen.sh    {cmd}')

        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        logging.info(output)

    else:
        cmd = f'autoreconf --install {repo_folder}'
        logging.info('-- running autoreconf')

        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        logging.info(output)


def clang(analysis_folder: str, repo_folder: str):

    cur_time = time.strftime('%X')
    logging.info(f'- clang\tstarting\t{cur_time}')

    # folder to redirect clang output to
    clang_folder = os.path.join(analysis_folder, 'clang')

    # run configure through scan-build to increase the chances that
    # the scan-build make process will actually work
    #
    # if running manually from inside repo folder, command would be
    # scan-build ./configure

    if os.path.exists(os.path.join(repo_folder, 'configure')):
        logging.info('-- running scan-build configure')
        logging.info(f'--- scan-build {repo_folder}/configure')
        subprocess.run(['scan-build', f'{repo_folder}/configure'])

        cur_time = time.strftime('%X')
        logging.info(f'- clang\tconfigured\t{cur_time}')

    # linux needs configuration to be specified
    # if repo_folder.split('/')[-2].endswith('linux'):
    #     make = 'make defconfig'
    # else:
    #     make = 'make'

    # now run the analyzer
    # 
    # if running manually from inside repo folder, command would be
    # scan-build --force-analyze-debug-code -o ../analysis/clang make
    #
    # --force-analyze-debug-code added as per scan-build's recommended usage guidelines
    # https://clang-analyzer.llvm.org/scan-build.html#recommended_debug 
    #
    # TODO: REPLACE -j4 WITH THE APPROPRIATE NUMBER 

    logging.info('-- running scan-build make')
    # clang_output = subprocess.run(['scan-build', '--force-analyze-debug-code', '-o', clang_folder, 
    #     make, '-C', repo_folder, '-j8'], stdout=subprocess.PIPE)
    clang_output = subprocess.check_output(['scan-build', '--force-analyze-debug-code', '-o', clang_folder, 
        'make', '-C', repo_folder, '-j12'], stderr=subprocess.STDOUT)
    
    # check if it actually worked
    # the output of a failed scan-build analysis will end with
    # scan-build: Removing directory '/path/to/folder/' because it contains no report.

    # if clang_output.stdout.endswith(b'because it contains no report.\n'):
    #     clang_failed(analysis_folder)
    
    # logging.info(clang_output.stdout)
    logging.info(clang_output)
    
    cur_time = time.strftime('%X')
    logging.info(f'- clang\tdone\t{cur_time}')


def clang_failed(analysis_folder: str):
    """create file to flag projects that weren't successfully analyzed by clang"""
    logging.info('-- clang failed')
    with open(os.path.join(analysis_folder, 'FAIL-CLANG'), 'w') as f: pass


#################################################

# configure logging
timestr = time.strftime("%Y%m%d-%H%M%S")
log_file = os.path.join('/home', f'clang_{timestr}.log')
targets = logging.StreamHandler(sys.stdout), logging.FileHandler(log_file)
logging.basicConfig(format='%(message)s', level=logging.INFO, handlers=targets)

# now run clang on all projects

# for each severity category folder
for sev_folder in [os.path.join(sample_folder, sev) for sev in severities]:
    # for each project of that severity
    for project_folder in [f.path for f in os.scandir(sev_folder) if f.is_dir()]:

        # folder where the cloned github repo is
        repo_folder = os.path.join(project_folder, 'repo')
        if not os.path.exists(repo_folder):
            continue

        # folder where the analyzer report will go
        analysis_folder = os.path.join(project_folder, 'analysis') 

        # skip chrome for now
        if os.path.basename(project_folder).endswith(('Chrome', 'linux')):
            continue

        clang_folder = os.path.join(analysis_folder, 'clang')
        if os.path.isdir(clang_folder) and os.listdir(clang_folder):
            logging.info(f'- already did {os.path.basename(project_folder)}')
            continue

        logging.info(f'- starting {os.path.basename(project_folder)}')

        # generate a configure file
        try:
            make_configure(repo_folder)
        except:
            clang_failed(analysis_folder)
        
        else:

            # run clang analyzer
            try:
                clang(analysis_folder, repo_folder)
            except:
                clang_failed(analysis_folder)
            
        finally:
            logging.info(f'- done with {os.path.basename(project_folder)}')
    
    logging.info(f'done with {os.path.basename(sev_folder)}')

logging.info('all clang analyzing completed')
