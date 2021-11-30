import random
import math, os
import time
import signal
import multiprocessing
from multiprocessing.pool import ThreadPool
import re

K = 3
CONF="-f ~/vc-systems/PregelPlus/examples/basic_pregelplus_khop/test_tmp_conf"
EXECUTABLE_FILE=" ~/vc-systems/PregelPlus/examples/basic_pregelplus_khop/run"
OUTPUT_FILE="test.out"

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

TOLERANCE_TIME = 14400
INTERVAL_TIME =  60


def writeBatchedSeeds(batched_workload):
	fin = open("originSeeds.txt","r")
	seeds = list()
	for line in fin:
		seeds.append(line.strip())
	fin.close()

	selected_seeds = list(random.sample(seeds, sum(batched_workload)))
	batched_seeds = []
	last_index = 0
	for workload in batched_workload:
		batched_seeds.append(selected_seeds[last_index:last_index+workload])
		last_index += workload
	fout = open("batchedSeeds.txt","w")
	for i in range(len(batched_seeds)):
		tmp_seeds = batched_seeds[i]
		for seed in tmp_seeds:
			fout.write(seed+"\t"+str(i)+"\n")
	fout.close()

if __name__ == '__main__':
	cpu_cores = multiprocessing.cpu_count()
	fin = open("test_result/test_workload","r")
	data = fin.readlines()
	execute_flag = [True]*len(data)	
	total_time_cost_list = [0.0 for x in range(len(data))]
	#workload_threshold = sys.maxint
	#workload_threshold = {1:384,4:448,5:448,6:448,7:448,8:448,9:448,10:448,11:448,12:448,13:448,14:448,15:448,16:448}
	workload_threshold = {}
	test_times = 1

	for p in range(test_times):
		line_index = 0
		print("Current Iteration: " + str(p))
		
		for line in data:
			print("\tCurrent Workload Setting:" + line)
				
			tmp = line.strip().split("\t")
			machineNum = int(tmp[0])
			os.system("head -" + str(machineNum) + " ~/vc-systems/PregelPlus/examples/basic_pregelplus_khop/tmp_conf > test_tmp_conf")
			os.system("./sync1.sh 3")
			total_workload = 0
			workload_list = tmp[1].split(";")
			total_time_cost = 0
			index = 0
			max_workload = 0
			batchNum = 1
			for workload_str in workload_list:
				batched_workload_str = workload_str.split(" ")
				batched_workload = [int(workload) for workload in batched_workload_str]
				if sum(batched_workload) >= max_workload:
					max_workload = sum(batched_workload)
					batchNum = len(batched_workload)

			if not execute_flag[line_index] or (batchNum in workload_threshold and max_workload >= workload_threshold[batchNum]):
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
				os.system("./sync1.sh 2") 
				output_file = "test_result/test_workload_detail/" + str(machineNum)+"_"+str(sum(batched_workload))+"_"+str(line_index)+"_"+str(index)+".out"
				hdfs_output_path = "/khop_output_tmp" + str(index) + "/"
				
				cmd = "mpiexec -n " + str(machineNum) + " " + CONF + " " + EXECUTABLE_FILE + " 1 " + hdfs_output_path + " " + str(K) + " > " + output_file
				pool = ThreadPool(processes=1)
				async_result = pool.apply_async(execute, (cmd, ))
				tmp_time_cost = float('inf')
				try:
					tmp_time_cost = async_result.get(TOLERANCE_TIME)
				except multiprocessing.TimeoutError:
					execute_flag[line_index] = False
					batchNum = len(batched_workload)
					workload_threshold[batchNum] = sum(batched_workload) 
					kill("mpiexec")
					failed_flag = True
					break
				finally:
					total_time_cost += tmp_time_cost
					pool.terminate()
					pool.close()

                        '''
			#Merge Hadoop File by Hadoop Streaming os.system("$HADOOP_HOME/bin/hadoop dfs -rmr /blogel_output/")	
			if not failed_flag:
				if len(workload_list) == 1:
					os.system("$HADOOP_HOME/bin/hadoop dfs -mv /khop_output_tmp1/ /khop_output/")
				else:
					input_command = ""
					hadoop_execute_file = "test_result/test_workload_detail/hadoop_execution_"+str(machineNum)+"_"+str(int(total_workload))+".txt"
					for k in range(len(workload_list)):
						input_command += " -input /khop_output_tmp" + str(k+1) + "/p*"
					start_time = time.time()
					os.system("$HADOOP_HOME/bin/hadoop jar " + streaming_jar_file_path + " -jobconf mapred.reduce.tasks=" + str(machineNum)+ " -file ../python-mapreduce/reducer.py -mapper cat -reducer reducer.py" + input_command+" -output /khop_output/ > " + hadoop_execute_file) 
						
					for k in range(len(workload_list)):
						os.system("$HADOOP_HOME/bin/hadoop dfs -rmr /khop_output_tmp" + str(k+1))
					end_time = time.time()
					os.system("$HADOOP_HOME/bin/hadoop dfs -rmr /khop_output")
					total_time_cost += end_time - start_time
                        '''

			time.sleep(10)
		
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
	
