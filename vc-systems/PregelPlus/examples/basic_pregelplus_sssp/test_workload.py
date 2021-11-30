from optimal_batch import *
import random
import math
import time
import signal
import multiprocessing
from multiprocessing.pool import ThreadPool
import re

def execute(cmd):
	start_time = time.time()
	os.system(cmd)
	end_time = time.time()
	return end_time - start_time

def kill(tag):
	while True:
		out = os.popen("ps aux | grep " + tag).read()
		line = ""
		tmp = out.splitlines()
		if len(tmp) >= 3:
			line = out.splitlines()[0]
			pid = int((re.split(" *", line.strip()))[1])
			try:
				os.kill(pid, signal.SIGKILL)
			except:
				pass
		else:
			break
	
	



seeds = []
streaming_jar_file_path = "$HADOOP_HOME/contrib/streaming/hadoop-streaming-1.2.1.jar" 

TOLERANCE_TIME = 6400
INTERVAL_TIME =  60


def writeBatchedSeeds(batched_workload):
	fout = open("batchedSeeds.txt","w")
	i = 0
	for j in range(len(batched_workload)):
		pre_workload = 0
		if j != 0:
			pre_workload = sum(batched_workload[:j])	
		curr_workload = batched_workload[j]
		for i in range(pre_workload, pre_workload+curr_workload):
			fout.write(str(seeds[i])+"\t"+str(j)+"\n")
	fout.close()

if __name__ == '__main__':
	cpu_cores = multiprocessing.cpu_count()
	fin = open("test_result/test_workload","r")
	data = fin.readlines()
	execute_flag = [True]*len(data)	
	total_time_cost_list = [0.0 for x in range(len(data))]
	#workload_threshold = sys.maxint
	workload_threshold = 2**12
	test_times = 1

	for p in range(test_times):
		line_index = 0
		print("Current Iteration: " + str(p))
		fin = open("originSeeds.txt","r")
		seeds_data = fin.readlines()
		for line in seeds_data:
			seeds.append(int(line.strip()))	
		random.shuffle(seeds)
		fin.close()
		for line in data:
			print("\tCurrent Workload Setting:" + line)
				
			tmp = line.strip().split("\t")
			machineNum = int(tmp[0])
			os.system("head -" + str(machineNum) + " /root/vc-systems/PregelPlus/examples/basic_pregelplus_sssp/conf > test_tmp_conf")
			os.system("./sync.sh 3")
			total_workload = 0
			workload_list = tmp[1].split(";")
			total_time_cost = 0
			index = 0
			max_workload = 0
			for workload_str in workload_list:
				batched_workload_str = workload_str.split(" ")
				batched_workload = [int(workload) for workload in batched_workload_str]
				if max(batched_workload) >= max_workload:
					max_workload = max(batched_workload)

			if not execute_flag[line_index] or max_workload > workload_threshold:
				print "execute flag: " + str(execute_flag[line_index])
				print "max workload: " + str(max_workload) + "\tthreshold: " + str(workload_threshold)
				print "Cost time:"
				print "\t" + "inf"
				total_time_cost_list[line_index] += float('inf')
				line_index += 1
				continue
				
			failed_flag = False
			for workload_str in workload_list:
				index += 1
				batched_workload_str = workload_str.split(" ")
				batched_workload = [int(workload) for workload in batched_workload_str]
				total_workload += sum(batched_workload)
				writeBatchedSeeds(batched_workload)
				#os.system("sh getBatchedSeeds.sh " + str(BATCH) + " " + str(workload))
				os.system("./sync.sh 2") 
				output_file = "test_result/test_workload_detail/" + str(machineNum)+"_"+str(sum(batched_workload))+"_"+str(index)+".out"
				hdfs_output_path = "/blogel_output_tmp" + str(index) + "/"
				
				cmd = "mpiexec -n " + str(machineNum) + " " + CONF + " " + EXECUTABLE_FILE + " 1 " + hdfs_output_path + " > " + output_file
				pool = ThreadPool(processes=1)
				async_result = pool.apply_async(execute, (cmd, ))
				tmp_time_cost = float('inf')
				try:
					tmp_time_cost = async_result.get(TOLERANCE_TIME)
				except multiprocessing.TimeoutError:
					execute_flag[line_index] = False
					workload_threshold = max(batched_workload) 
					kill("mpiexec")
					failed_flag = True
					break
				finally:
					total_time_cost += tmp_time_cost
					pool.terminate()
					pool.close()


			time.sleep(10)
			os.system("$HADOOP_HOME/bin/stop-dfs.sh")
			time.sleep(10)
			os.system("$HADOOP_HOME/bin/start-dfs.sh")
			time.sleep(10)
			os.system("$HADOOP_HOME/bin/hadoop dfsadmin -safemode leave")
		
			total_time_cost_list[line_index] += total_time_cost
			print "Cost time:"
			print total_time_cost
			line_index += 1


	line_index = 0
	for line in data:
		print("Setting:")
		print("\t" + line)	
		print("Result:")
		print("\tTotal time cost is " + str(total_time_cost_list[line_index]/test_times) + " seconds. \n")
		line_index += 1
	
