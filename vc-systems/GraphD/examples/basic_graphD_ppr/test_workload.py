from optimal_batch import * 
import re
import math
import os,signal
import time
import multiprocessing
from multiprocessing.pool import ThreadPool, Pool


def parse_io_util(filename):
	f = open(filename, "r")
	patterns = ["Final Max Avg util", "Avg percentage of 100 for all machines","Max overuse IO count", "Max avgrq-sz", "Max avgqu-sz", "Avg avgrq-sz", "Avg avgqu-sz"]
	count = 0
	for line in f:
		tmp = line.strip().split(":")
		for p in patterns:
			if tmp[0].startswith(p):
				print(line)
				count+=1
		if count >= len(patterns):
			break
	f.close()
		
	

def aggregation():
	f = open("test_tmp_conf","r")
	data = f.readlines()
	hosts = []
	for line in data:
		hosts.append(line.strip().split(':')[0])
	tmp_max = [0,0,0]
	tmp_max_sum = [0,0,0]
	tmp_avg_sum = [0,0,0]
	sum_overuse_time = 0
	max_overuse_time = 0
	for host in hosts:
		os.system("scp " + host + ":~/net-measurement/bandwidth_measure_output.txt tmp-net-xxx.txt")
		f1 = open("tmp-net-xxx.txt","r")	
		net_data = f1.readlines()
		if len(net_data) == 3:
			print(host)
			print(net_data)
			exit()
		#print(host)
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
		overuse_time = float(net_data[5])
		sum_overuse_time += overuse_time
		max_overuse_time = max(overuse_time, max_overuse_time)
		print(net_data[5])
		os.system("rm tmp-net-xxx.txt")
	result = tmp_max
	for i in range(3):
		result.append(tmp_max_sum[i]/len(hosts))
	for i in range(3):
		result.append(tmp_avg_sum[i]/len(hosts))
	print(result)
	print("Avg overuse time:")
	print(sum_overuse_time/len(hosts))
	result.append(sum_overuse_time/len(hosts))
	print("Max overuse time:")
	print(max_overuse_time)
	result.append(max_overuse_time)
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

def readLog(filename):
	max_util = 0
	f = open(filename,"r")
	for line in f:
		tmp = line.strip().split(" ")
		i = 0
		while tmp[i] != "Util:":
			i += 1
			if i == len(tmp):
				break
		if i == len(tmp):
			continue
		util = float(tmp[i+1][:-1])	
		if util > max_util:
			max_util = util
	return max_util


def kill(tag):
	
	while True:
		out = os.popen("ps aux | grep " + tag).read().strip()
		line = ""
		tmp = out.splitlines()
		x = 0
		for line in tmp:
			if not line.endswith(tag):
				x += 1
		if x >= 1:
			for line in tmp:
				if not line.endswith(tag):
					pid = int((re.split(" *", line.strip()))[1])
					try:
						os.kill(pid, signal.SIGKILL)
					except:
						pass
					finally:
						time.sleep(10)
		else:
			break
	
	


streaming_jar_file_path = "$HADOOP_HOME/contrib/streaming/hadoop-streaming-1.2.1.jar" 
TOLERANCE_TIME = 14400.0
INTERVAL_TIME =  60
if __name__ == '__main__':
	cpu_cores = multiprocessing.cpu_count()
	fin = open("test_result/test_workload","r")
	#execute_flag = [True]*len(data)
	execute_threshold = dict()
	data = fin.readlines()
	total_time_cost_list = [0.0 for x in range(len(data))]
	util_list = [0.0 for x in range(len(data))]
	stats_list = [ [] for x in range(len(data))]
	test_times = 1
	for p in range(test_times):
		line_index = 0
		print("Current Iteration: " + str(p))
		for line in data:
			print("\tCurrent Workload Setting:" + line)
			tmp = line.strip().split("\t")
			machineNum = int(tmp[0])
			os.system("head -" + str(machineNum) + " ~/vc-systems/GraphD/examples/basic_graphD_ppr/tmp_conf > test_tmp_conf")
			os.system("./sync1.sh 3")
			hosts = []
			hosts_f = open("test_tmp_conf","r")
			hosts_data = hosts_f.readlines()
			for line in hosts_data:
				hosts.append(line.strip().split(':')[0])
			total_workload = 0
			workload_list = tmp[1].split(";")
			total_time_cost = 0
			index = 0
		
			unitPPRFlag = 0
			if len(workload_list) == 1:
				unitPPRFlag = 1	
			for workload_str in workload_list:
				index += 1
				batched_workload_str = workload_str.split(" ")
				batched_workload = [int(workload) for workload in batched_workload_str]
				total_workload += sum(batched_workload)

				#if not execute_flag[line_index] or max_workload > workload_threshold:
				if total_workload in execute_threshold and len(batched_workload) > execute_threshold[total_workload]:
					total_time_cost_list[line_index] += float('inf')
					line_index += 1
					break

				writeBatchedSeeds(batched_workload)
				#os.system("sh getBatchedSeeds.sh " + str(BATCH) + " " + str(workload))
				os.system("./sync1.sh 2")
				output_file = "test_result/test_workload_detail/" + str(machineNum)+"_"+str(sum(batched_workload))+"_" + str(line_index) + "_"+str(index)+"-test-rq-qu-4.out"
				hdfs_output_path = "/graphd_output_tmp" + str(index) + "/"
				cmd = "mpiexec -n " + str(machineNum) + " " + CONF + " " + EXECUTABLE_FILE + " /dblp_pregelplus/ > " + output_file + " 2> /dev/null"
				pool = ThreadPool(processes=1)
				tmp_time_cost = float('inf')
				for host in hosts:
					os.system("ssh " +  host + " 'nohup python ~/net-measurement/net_usage_measure.py > /dev/null &'")
				os.system("bash measure.sh start")
				async_result = pool.apply_async(execute, (cmd, ))	
				
				try:
					tmp_time_cost = async_result.get(TOLERANCE_TIME)
				except multiprocessing.TimeoutError:
					#execute_flag[line_index] = False
					execute_threshold[total_workload] = len(batched_workload)
					kill("mpiexec")
					os.system("bash measure.sh stop")
					os.system("bash measure.sh measure")
					os.system("bash measure.sh delete")
					pass
				finally:
					os.system("bash measure.sh measure")
					os.system("bash measure.sh delete")
					total_time_cost += tmp_time_cost
					time.sleep(tmp_time_cost*0.08)
					stats_list[line_index] = aggregation()
					parse_io_util("max_util.txt")
					pool.terminate()
					pool.close()
					
				'''	
				i = 0
				while True:
					time.sleep(INTERVAL_TIME)
					if not async_result.successful():
						total_time_cost += async_result.get();
						break
					elif i*INTERVAL_TIME > TOLERANCE_TIME:
						total_time_cost = float("inf")
						break
					i += 1
				pool.terminate()	
				pool.close()
				'''
			#Merge Hadoop File by Hadoop Streaming
			os.system("$HADOOP_HOME/bin/hadoop dfs -rmr /graphd_output/ > /dev/null")	
			hadoop_execute_file = "test_result/test_workload_detail/hadoop_execution_"+str(machineNum)+"_"+str(int(total_workload))+".txt"
			if len(workload_list) == 1:
				os.system("$HADOOP_HOME/bin/hadoop dfs -mv /graphd_output_tmp1/ /graphd_output/ > " + hadoop_execute_file)
			else:
				input_command = ""
				for k in range(len(workload_list)):
					input_command += " -input /graphd_output_tmp" + str(k+1) + "/p*"
				start_time = time.time()
				os.system("$HADOOP_HOME/bin/hadoop jar " + streaming_jar_file_path + " -Dmapred.reduce.tasks=" + str(cpu_cores)+ " -file ./reducer.py -mapper cat -reducer 'python reducer.py " + str(total_workload) + "'" +  input_command +" -output /graphd_output/ > " + hadoop_execute_file) 
					
				for k in range(len(workload_list)):
					os.system("$HADOOP_HOME/bin/hadoop dfs -rmr /graphd_output_tmp" + str(k+1) + " > /dev/null")
				end_time = time.time()
				total_time_cost += end_time - start_time
			time.sleep(10)
		
			total_time_cost_list[line_index] += total_time_cost
			print "Cost time:"
			print total_time_cost
			line_index += 1
			#os.system("$HADOOP_HOME/bin/stop-all.sh")	
			#os.system("$HADOOP_HOME/bin/start-all.sh")	
			#os.system("$HADOOP_HOME/bin/hadoop dfsadmin -safemode leave")	

	line_index = 0
	for line in data:
		print("Setting:")
		print("\t" + line)	
		print("Result:")
		print("\tTotal Util is " + str(util_list[line_index]/test_times) + " % \n")
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
		print("\t".join([str(x) for x in stats_list[line_index][6:9]]))
		print("\tBandwidth Overuse Stats")
		print("Avg-overuse-time\tMax-overuse-time")
		print("\t".join([str(x) for x in stats_list[line_index][9:]]))


		line_index += 1
	
