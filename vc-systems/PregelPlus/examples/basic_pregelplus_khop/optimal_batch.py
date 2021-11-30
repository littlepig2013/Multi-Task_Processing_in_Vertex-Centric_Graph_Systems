import os, sys
from scipy.optimize import curve_fit
import subprocess
import numpy as np
import math, time, random

machine_list = 2**np.arange(0, 4)
workload_list = 2**np.arange(5, 11)


CONF="-f ~/vc-systems/PregelPlus/examples/basic_pregelplus_khop/test_tmp_conf"
EXECUTABLE_FILE=" ~/vc-systems/PregelPlus/examples/basic_pregelplus_khop/run"
OUTPUT_FILE="test.out"
BATCH=1

fDict = dict()
gDict = dict()
fDict2 = dict()
gDict2 = dict()
sDict = dict()

def storage_func(workload, a, b):
	return a*workload + b

def storage_func_params(workload, params):
	return params[0]*workload+params[1]

def storage_func_inv(storage, a, b):
	return (storage - b)/a

def storage_func_inv_params(storage, params):
	return (storage - params[1])/params[0]

def func(workload, a, b, c):
	return a*(workload**b) + c

def func_params(workload, params):
	return params[0]*(workload**params[1])+params[2]

def func_inv(mem, a, b, c):
	return math.pow((mem-c)/a, 1/b)

def func_inv_params(mem, params):
	return func_inv(mem, params[0], params[1], params[2])

def func2(workload, a, b, c):
	return func(workload, a, b, c)

def func2_params(workload, params):
	return func_params(workload, params)

def method2(W, M, params, params2):#f(w)+g(W-w) = M
	final_ws = []
	while True:
		final_w = 0
		diff = float("inf")
		for i in range(1, W+1):
			tmp_result = M - (func_params(i, params) + func2_params(W-i, params2) - func_params(0, params))
			if tmp_result > 0 and final_w < i:
				diff = tmp_result
				final_w = i
		if final_w == 0:
			break
		W -= final_w
		M -= func2_params(final_w, params2) - func2_params(0, params2)
		#M -= func_params(final_w, params) - func_params(0, params)
		print str(M)
		final_ws.append(final_w)
		if W <= 0 or M < 0:
			break	
	final_ws.reverse()
	print(sum(final_ws))
	return final_ws

def method4(W, M, params, params2, s_params, attachable=False):#f(w) = M
	tmpW = W
	tmpM = M
	ws = []
	final_ws = []
	while tmpM >= 0 and tmpW > 0:
		w = 0
		diff = float("inf")
		if tmpM < params[2]:
			break
		w = func_inv_params(tmpM, params)
		w = math.floor(w)
		#print "\tW:"+str(w)
		if w >= tmpW:
			w = tmpW
		if w == 0:
			break
		tmpW -= w
		tmpM -= func2_params(w, params2) - func2_params(0, params2)
		ws.append(w)
	#final_ws.reverse()
	total_w = sum(ws)
	final_ws.append(ws)
	if attachable and total_w < W:
		final_ws = []
		s = storage_func_params(total_w, s_params)/8
		attached_batch = int(min(M*0.5*1024/s, W*1.0/total_w))
		for i in range(attached_batch):
			final_ws.append(ws)
		tmpW1 = W - total_w*attached_batch		
		tmpW2 = storage_func_inv_params((M*1024-attached_batch*s)*8, s_params)
		tmpW = min(tmpW1, tmpW2)
		tmpWs = []
		i = 0
		while tmpW > ws[i]:
			tmpWs.append(ws[i])
			tmpW -= ws[i]
			i += 1	
		tmpWs.append(tmpW)
		final_ws.append(tmpWs)
		
	#print final_ws
	return final_ws


def getMostMemory(data, machineNum, attr="VmHWM"):
	memDict = dict()
	currSuperstep = 1
	memDict[1] = []
	for line in data:
		tmp = line.strip().replace("\t"," ").split(" ")
		#if len(memDict[currSuperstep]) == machineNum:
		if tmp[0].startswith("Superstep"):
			currSuperstep += 1
			memDict[currSuperstep] = []
		else:
			if len(tmp) > 1:
				if tmp[1].startswith(attr):
					for tmpStr in tmp[1:]:
						if tmpStr.isdigit():
							memDict[currSuperstep].append(int(tmpStr))
	maxMem = 0
	maxMemSuperstep = 0
	if attr == "VmHWM":
	#if True:
		for superstep, memList in memDict.items():
			tmpMem = sum(memList)
			if tmpMem > maxMem:
				maxMem = tmpMem	
				maxMemSuperstep = superstep
	else:
		for superstep, memList in memDict.items():
			if superstep > maxMemSuperstep and memList != []:
				maxMemSuperstep = superstep
				maxMem = sum(memList)

	tmpMemList = memDict[maxMemSuperstep]
	tmpUnbalancedFactorList = [x*1.0/maxMem for x in tmpMemList]
	#print tmpMemList
	#print sum(tmpMemList)
	print tmpUnbalancedFactorList
	print "Superstep: " + str(maxMemSuperstep) + "\t Length:" + str(len(tmpUnbalancedFactorList))
	if len(tmpUnbalancedFactorList) != machineNum:
		f = open('test2.out','w')
		for line in data:
			f.write(line)
		f.close()
		exit()
	return [maxMem*1.0/machineNum, max(tmpUnbalancedFactorList)]
	

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
	'''	
	for machineNum in machine_list:
		os.system("head -" + str(machineNum) + " ~/vc-systems/PregelPlus/examples/basic_pregelplus_khop/tmp_conf > test_tmp_conf")
		fDict[machineNum] = dict()
		gDict[machineNum] = dict()
		fDict2[machineNum] = []
		gDict2[machineNum] = []
		sDict[machineNum] = dict()
		if machineNum != 1:
			workload_list *= 2
		os.system("./sync1.sh 3")
		for i in range(len(workload_list)):
			workload=workload_list[i]
			writeBatchedSeeds([workload])
			#os.system("echo " + str(workload) + "' > batchedRWs.txt")
			#os.system("sh getBatchedSeeds.sh " + str(BATCH) + " " + str(workload))
			os.system("./sync1.sh 2")
			output_file = "train_result/" + str(machineNum)+"_"+str(workload)+".out"
			hdfs_output_path = "/khop_output_tmp" + str(i) + "/"
			start_time = time.time()
			os.system("mpiexec -n " + str(machineNum) + " " + CONF + " " + EXECUTABLE_FILE + " 1 " + hdfs_output_path + " 3 > " + output_file)
			end_time = time.time()
			print("Cost time " + str(end_time - start_time))
			fin = open(output_file, "r")
			data = fin.readlines()
			tmpfResult = getMostMemory(data, machineNum)
			tmpgResult = getMostMemory(data, machineNum, "VmRSS")
			fDict[machineNum][workload] = tmpfResult[0]
			gDict[machineNum][workload] = tmpgResult[0]
			fDict2[machineNum].append(tmpfResult[1])
			gDict2[machineNum].append(tmpgResult[1])
			print fDict[machineNum][workload]
			print gDict[machineNum][workload]
			storage_result = subprocess.check_output("$HADOOP_HOME/bin/hadoop dfs -dus " + hdfs_output_path, shell=True)
			sDict[machineNum][workload] = int(storage_result.strip().split("\t")[1])
			
			
		print machineNum
		print fDict[machineNum]
		print gDict[machineNum]
	'''		
	fDict = {8: {256: 118979.5, 512: 124240.5, 4096: 521433.0, 8192: 1049457.5, 2048: 310005.0, 1024: 150460.5}, 1: {32: 763400.0, 64: 760804.0, 1024: 982376.0, 128: 761212.0, 256: 764756.0, 512: 768872.0}, 2: {64: 399954.0, 128: 400038.0, 1024: 845682.0, 256: 402736.0, 512: 400948.0, 2048: 875654.0}, 4: {128: 215474.0, 256: 216516.0, 4096: 1141689.0, 512: 260737.0, 1024: 314541.0, 2048: 538657.0}}
	gDict = {8: {256: 100222.5, 512: 108683.0, 4096: 506258.0, 8192: 1037788.5, 2048: 310005.0, 1024: 149592.0}, 1: {32: 546396.0, 64: 544280.0, 1024: 982376.0, 128: 545864.0, 256: 551612.0, 512: 573484.0}, 2: {64: 254914.0, 128: 265734.0, 1024: 832148.0, 256: 312946.0, 512: 319570.0, 2048: 862874.0}, 4: {128: 164339.0, 256: 182238.0, 4096: 1141689.0, 512: 240029.0, 1024: 314541.0, 2048: 538657.0}}
	fDict2 = {8: [0.29774036703801915, 0.28708432435477965, 0.2654218216741271, 0.18097288753407204, 0.23364842654761014, 0.2343163015176889], 1: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0], 2: [0.5782314966221116, 0.5779850914163155, 0.579342298677049, 0.5768478705468041, 0.6247005375543053, 0.6339010613781242], 4: [0.3925578027975533, 0.38966173400580095, 0.3342256756808585, 0.39645388041622553, 0.38050744722522867, 0.3733416017847242]}
	gDict2 = {8: [0.3019132430342488, 0.2842256838696024, 0.2659868174768704, 0.18097288753407204, 0.24065199957334008, 0.23568964196461997], 1: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0], 2: [0.5501541696415262, 0.5569178200757148, 0.6032094994024528, 0.6069593516287511, 0.6348606257540725, 0.6432897502995802], 4: [0.44665599766336656, 0.40159571549292683, 0.35274071049748157, 0.39645388041622553, 0.38050744722522867, 0.3733416017847242]}

	sDict = {8: {256: 16932306, 512: 31765974, 4096: 209691875, 8192: 433771162, 2048: 116386335, 1024: 61263834}, 1: {32: 5217951, 64: 5916182, 1024: 19723816, 128: 6531426, 256: 8198937, 512: 11889491}, 2: {64: 6404241, 128: 8892499, 1024: 39768095, 256: 14349318, 512: 18766110, 2048: 67202558}, 4: {128: 10168675, 256: 18830575, 4096: 196233413, 512: 28503478, 1024: 53590688, 2048: 99882877}}
	
	
	
	print fDict
	print gDict
	print fDict2
	print gDict2
	
	print "Storage Cost"
	print sDict
	f_popt = {}
	for machineNum in machine_list:
		xdata = []
		ydata = []
		for workload in fDict[machineNum]:	
			xdata.append(workload)
			ydata.append(fDict[machineNum][workload])
		xdata=np.array(xdata)
		ydata=np.array(ydata)
		popt, _ = curve_fit(func, xdata, ydata, maxfev=8000)
		#popt, _ = curve_fit(func, xdata, ydata)
		print machineNum
		print popt
		f_popt[machineNum]=popt
	g_popt = {}
	for machineNum in machine_list:
		xdata = []
		ydata = []
		for workload in gDict[machineNum]:
			xdata.append(workload)
			ydata.append(gDict[machineNum][workload])
		xdata = np.array(xdata)
		ydata = np.array(ydata)
		popt, _ = curve_fit(func2, xdata, ydata, maxfev=8000)
		print machineNum
		print popt
		g_popt[machineNum]=popt

	s_popt = {}
	for machineNum in machine_list:
		xdata = []
		ydata = []
		for workload in sDict[machineNum]:
			xdata.append(workload)
			ydata.append(sDict[machineNum][workload])
		xdata = np.array(xdata)
		ydata = np.array(ydata)
		popt, _ = curve_fit(storage_func, xdata, ydata, maxfev=3000)
		print machineNum
		print popt
		s_popt[machineNum] = popt



	W = 256
	W0 = [1024+1024*i for i in range(7)]
	WS = []
	for i in machine_list:
		WS.append([j*i for j in W0])

	M = 16*0.9*1024*1024


	print "Method 4:"
	i = 0
	for machineNum in machine_list:
		print machineNum
		f_factor = max(fDict2[machineNum])
		#f_factor = 1.0/machineNum
		tmp_f_popt = [ x*(machineNum*f_factor) for x in f_popt[machineNum]]
		tmp_f_popt[1] = f_popt[machineNum][1]
		g_factor = max(gDict2[machineNum])
		#g_factor = 1.0/machineNum
		tmp_g_popt = [ x*(machineNum*g_factor) for x in g_popt[machineNum]]
		tmp_g_popt[1] = g_popt[machineNum][1]
		for w in WS[i]:
			print w
			ws = method4(w, M, tmp_f_popt, tmp_g_popt, s_popt[machineNum])
			print str(w) + "\t" + str(ws) + "\t"
		i += 1
		print ""


	#os.system("rm test.out")
	#os.system("rm test_tmp_conf")
	 

