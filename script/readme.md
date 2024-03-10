The dirctory includes the main algorithm to run static anlyzer and analyze the data.

run_clang.py run_infer.py run_pattern_mathcing.py are used to run static analyzer on the source code.

calculate_distances.py is used to calculate the distance between reported warning and patch location for line(rline) distance and file distance.

dot-to-nx.py and nx-to-log_dist.py are used to calculate logical distance.

2000.xml is the official cwe category, we use the comprehension category in our study.
