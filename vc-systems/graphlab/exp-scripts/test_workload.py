import os
import re
import math
import time
import multiprocessing
from multiprocessing.pool import ThreadPool

def aggregation():
	f = open(CONF,"r")
	data = f.readlines()
	hosts = []
	for line in data:
		hosts.append(line.strip().split(':')[0])
	tmp_max = [0,0,0]
	tmp_max_sum = [0,0,0]
	tmp_avg_sum = [0,0,0]
	for host in hosts:
		os.system("scp " + host + ":/root/net-measurement/bandwidth_measure_output.txt tmp-net-xxx.txt")
		f1 = open("tmp-net-xxx.txt","r")	
		net_data = f1.readlines()
		if len(net_data) == 3:
			print(host)
			print(net_data)
			exit()
		print(host)
		#print(net_data)
		#print(net_data[1])
		tmp = net_data[1].strip().split("\t")
		tmp2 = [float(x) for x in tmp]
		if tmp2[0] + tmp2[2] >  tmp_max[2]:
			tmp_max = [tmp2[0],tmp2[2],tmp2[0]+tmp2[2]]
		for i in range(2):
			tmp_max_sum[i] += float(tmp2[i*2])
		tmp_max_sum[2] += tmp2[0] + tmp2[2]
		#print(net_data[3])
		tmp = net_data[3].strip().split("\t")
		for i in range(2):
			tmp_avg_sum[i] += float(tmp[i*2])
		tmp_avg_sum[2] += float(tmp[0]) + float(tmp[2])
		os.system("rm tmp-net-xxx.txt")
	result = tmp_max
	for i in range(3):
		result.append(tmp_max_sum[i]/len(hosts))
	for i in range(3):
		result.append(tmp_avg_sum[i]/len(hosts))
	print(result)
	return result
	


def writeBatchedSeeds(batched_workload):
	fout = open("batchedRWs.txt","w")
	for workload in batched_workload:
		fout.write(str(workload)+"\n")
	fout.close()

def execute(cmd):
	start_time = time.time()
	os.system(cmd)
	end_time = time.time()
	return end_time - start_time

def kill(tag):
	while True:
		out = os.popen("ps aux | grep [" + tag[0]+"]"+tag[1:]).read()
		line = ""
		tmp = out.splitlines()
		if len(tmp) >= 1:
			line = out.splitlines()[0]
			pid = int((re.split(" *", line.strip()))[1])
			try:
				os.kill(pid, signal.SIGKILL)
			except:
				os.system("kill -9 " + str(pid))
			finally:
				time.sleep(10)
		else:
			break
	
TOLERANCE_TIME = 14400
INTERVAL_TIME =  60
CONF = "/root/vc-systems/graphlab/tmp_conf"
EXECUTABLE_FILE = "/root/vc-systems/graphlab/release/toolkits/graph_analytics/personalized_pagerank"
if __name__ == '__main__':

	fin = open("test_result/test_workload","r")
	execute_threshold = dict()
	data = fin.readlines()
	stats_list = [ [] for x in range(len(data))]
	total_time_cost_list = [0.0 for x in range(len(data))]
	test_times = 1
	
	for p in range(test_times):
		line_index = 0
		print("Current Iteration: " + str(p))
		for line in data:
			print("\tCurrent Workload Setting:" + line)
			tmp = line.strip().split("\t")
			machineNum = int(tmp[0])
			os.system("head -" + str(machineNum) + " /root/vc-systems/PregelPlus/examples/basic_pregelplus_ppr/tmp_conf > ~/graphlab/tmp_conf")
			hosts = []
			hosts_f = open("/root/vc-systems/graphlab/tmp_conf","r")
			hosts_data = hosts_f.readlines()
			for line in hosts_data:
				hosts.append(line.strip().split(':')[0])
			hosts_f.close()
			total_workload = 0
			os.system("cd ~; ./deploy.sh")
			total_time_cost = 0
			batched_workload_str = tmp[1].split(" ")
			batched_workload = [int(workload) for workload in batched_workload_str]
			total_workload += sum(batched_workload)
			if total_workload in execute_threshold and len(batched_workload) > execute_threshold[total_workload]:

				total_time_cost_list[line_index] += float('inf')
				line_index += 1
				break
                        batched_workload_params_list = [ "--batchedRWs " + w for w in batched_workload_str]
			batched_workload_params_str = " ".join(batched_workload_params_list)
			output_file = "test_result/dblp_test_workload_detail/" + str(machineNum)+"_"+str(sum(batched_workload))+"_" + str(line_index) +".out"
			hdfs_input_path = "/dblp_pregelplus/"
			os.system("$HADOOP_HOME/bin/hadoop dfs -rmr /pregelplus_output/")
			cmd = "mpiexec -n " + str(machineNum) + " -f " + CONF + " " + EXECUTABLE_FILE + " --engine asynchronous --graph hdfs://localhost:54312" + hdfs_input_path + " " + batched_workload_params_str + " --saveprefix hdfs://localhost:54312/pregelplus_output/" + " --ncpus 1 > " + output_file 
			#cmd = "mpiexec -n " + str(machineNum) + " -f " + CONF + " " + EXECUTABLE_FILE + " --graph hdfs://galaxy040:54312" + hdfs_input_path + " " + batched_workload_params_str + " --saveprefix hdfs://galaxy040:54312/pregelplus_output/" + " --ncpus 1 > " + output_file 
			pool = ThreadPool(processes=1)
			for host in hosts:
				os.system("ssh " +  host + " '  exportnohup python -u /root/net-measurement/net_usage_measure_NLOAD.py > /root/net-measurement/log.txt &'")
			async_result = pool.apply_async(execute, (cmd, ))
			tmp_time_cost = float('inf')
			try:
				tmp_time_cost = async_result.get(TOLERANCE_TIME)
			except multiprocessing.TimeoutError:
				#execute_flag[line_index] = False
				execute_threshold[total_workload] = len(batched_workload)
				kill("mpiexec")
				kill("personalized_pagerank")
				pass
			finally:
				total_time_cost += tmp_time_cost
				time.sleep(tmp_time_cost*0.18)
				stats_list[line_index] = aggregation()
				pool.terminate()
				pool.close()
			
			total_time_cost_list[line_index] += total_time_cost
			print(line)
			print "Cost time:"
			print total_time_cost
			line_index += 1
			
			os.system("$HADOOP_HOME/bin/stop-all.sh")
			time.sleep(5)
			os.system("$HADOOP_HOME/bin/start-all.sh")
			time.sleep(5)
			os.system("$HADOOP_HOME/bin/hadoop dfsadmin -safemode leave")
			time.sleep(5)
	line_index = 0
	for line in data:
		print("Setting:")
		print("\t" + line)
		print("Result:")
		print("\tTotal time cost is " + str(total_time_cost_list[line_index]/test_times) + " seconds. \n")
		print("Net Stats:")
		print("\tMax Stats")
		print("Recv-Bytes\tTrans-Bytes\tTotal-Bytes")
		print("\t".join([str(x) for x in stats_list[line_index][:3]]))
		print("\tMax Avg Stats")
		print("Recv-Bytes\tTrans-Bytes\tTotal-Bytes")
		print("\t".join([str(x) for x in stats_list[line_index][3:6]]))
		print("\tAvg Stats")
		print("Recv-Bytes\tTrans-Bytes\tTotal-Bytes")
		print("\t".join([str(x) for x in stats_list[line_index][6:]]))
		line_index += 1











	
