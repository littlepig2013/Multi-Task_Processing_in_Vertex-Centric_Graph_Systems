#!/usr/bin/env python
import sys

total_workload = int(sys.argv[1])

nodes = dict()

for line in sys.stdin:
	tmp = line.strip().split('\t')
	node_id = tmp[0]
	result = tmp[1]
	if node_id not in nodes:
		nodes[node_id] = {}
	tmp_result = result.strip().split(' ')	
	for tmp_ppr_str in tmp_result:
		tmp_ppr	= tmp_ppr_str.strip().split(":")
		dst_node_id = int(tmp_ppr[0])
		dst_node_ppr = float(tmp_ppr[1])
		if dst_node_id not in nodes[node_id]:
			nodes[node_id][dst_node_id] = 0.0
		nodes[node_id][dst_node_id] += dst_node_ppr/total_workload

for node_id in nodes:
	node_id_ppr_list_result = []
	for dst_node_id in nodes[node_id]:
		node_id_ppr_list_result.append(str(dst_node_id)+":"+str(nodes[node_id][dst_node_id]))
	print(node_id+"\t"+" ".join(node_id_ppr_list_result))
