import os
import glob
import pandas as pd
import numpy as np
import sys
from tqdm import *

base_folder = '/storage2/yueke'
sample_folder = os.path.join(base_folder, 'projects')

severity = sys.argv[1]
if severity == 'all':
    severities = ['low', 'crit', 'med', 'high']
else:
    severities = [severity]

def count_comments_and_blank_lines(filename, start_line, end_line):
    count = 0
    in_multiline_comment = False

    with open(filename, 'r') as file:
        for i, line in enumerate(file, start=1):
            if i > start_line and i < end_line:
                stripped_line = line.strip()

                # Check for multiline comments
                if in_multiline_comment:
                    count += 1
                    if "*/" in stripped_line:
                        in_multiline_comment = False
                else:
                    # Check for single line comment or blank line
                    if stripped_line.startswith("//") or not stripped_line:
                        count += 1
                    # Check for start of multiline comment
                    elif "/*" in stripped_line:
                        count += 1
                        if "*/" not in stripped_line:
                            in_multiline_comment = True

    return count


def find_files(directory, filename_pattern, search_string):
    matching_files = []
    # Search for .c files that contain filename_pattern
    for filepath in glob.glob(os.path.join(directory, '*' + filename_pattern + '*.c')):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
            if search_string in file.read():
                matching_files.append(filepath)
    return matching_files

# Example usage
# f.path=="/storage2/yueke/projects/crit/1624_opa-ff
if __name__ == "__main__":
    for sev_folder in [os.path.join(sample_folder, sev) for sev in severities]:
        for project_folder in tqdm([f.path for f in os.scandir(sev_folder) if f.is_dir()]):
            analysis_folder = os.path.join(project_folder, 'analysis')
            repo_folder = os.path.join(project_folder, 'repo')
            if not os.path.exists(os.path.join(analysis_folder, 'diff.csv')):
                continue
            df_tool=pd.read_csv(analysis_folder+"/tool_data1.csv")
            
            df_diff=pd.read_csv(analysis_folder+"/diff.csv")
            realloc_list=[]
            for i in range(len(df_tool)):
                filename=df_tool.iloc[i,2]
                func_name=df_tool.iloc[i,4]
                linenum=df_tool.iloc[i,3] 
                vul=df_diff[df_diff["filename"]==filename]
                if vul.empty:
                    realloc_list.append(0.1)
                    continue
                minlist=[]
                fileloc=repo_folder+"/"+filename
                for j in range(len(vul)):
                    vul_start=vul.iloc[j,2]
                    vul_end=vul.iloc[j,3]
                    if (vul_start<=linenum and vul_end>=linenum):
                        minlist.append(0)
                    elif (vul_start>linenum):
 #                       start_line, end_line = (vul_loc, linenum) if vul_loc < linenum else (linenum, vul_loc)
                        blank=count_comments_and_blank_lines(fileloc, linenum, vul_start)
                        realloc=abs(vul_start-linenum)-blank
                        
                    else:
                        blank=count_comments_and_blank_lines(fileloc, vul_end, linenum)
                        realloc=abs(vul_end-linenum)-blank                    
                    minlist.append(realloc)
#                    print(minlist)
                realloc_list.append(min(minlist))
            print(realloc_list)
            df_tool["real_loc"]=realloc_list    
            df_tool.to_csv(analysis_folder+"/tool_data1.csv",index=False)
