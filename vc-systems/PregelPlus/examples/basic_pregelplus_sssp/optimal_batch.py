import os, sys
from scipy.optimize import curve_fit
import subprocess
import numpy as np
import math

machine_list = 2**np.arange(0, 4)
workload_list = 2**np.arange(0, 6)


CONF="-f ~/vc-systems/PregelPlus/examples/basic_pregelplus_sssp/test_tmp_conf"
EXECUTABLE_FILE=" ~/vc-systems/PregelPlus/examples/basic_pregelplus_sssp/run"
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

def method4(W, M, params, params2, s_params, attachable=True):#f(w) = M
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
		tmpW2 = storage_func_inv_params((M-attached_batch*M*0.5/s)*8*1024, s_params)
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
	



if __name__ == '__main__':	
	'''	
	for machineNum in machine_list:
		os.system("head -" + str(machineNum) + " ~/vc-systems/PregelPlus/examples/basic_pregelplus_sssp/conf > test_tmp_conf")
		fDict[machineNum] = dict()
		gDict[machineNum] = dict()
		fDict2[machineNum] = []
		gDict2[machineNum] = []
		sDict[machineNum] = dict()
		if machineNum != 1:
			workload_list *= 2
		os.system("./sync.sh 3")
		for i in range(len(workload_list)):
			workload=workload_list[i]
			os.system("sh getBatchedSeeds.sh " + str(BATCH) + " " + str(workload))
			os.system("./sync.sh 2")
			os.system("mpiexec -n " + str(machineNum) + " " + CONF + " " + EXECUTABLE_FILE + " 1 >" + OUTPUT_FILE)
			fin = open(OUTPUT_FILE, "r")
			data = fin.readlines()
			tmpfResult = getMostMemory(data, machineNum)
			tmpgResult = getMostMemory(data, machineNum, "VmRSS")
			fDict[machineNum][workload] = tmpfResult[0]
			gDict[machineNum][workload] = tmpgResult[0]
			fDict2[machineNum].append(tmpfResult[1])
			gDict2[machineNum].append(tmpgResult[1])
			print fDict[machineNum][workload]
			print gDict[machineNum][workload]
			storage_result = subprocess.check_output("$HADOOP_HOME/bin/hadoop dfs -dus /blogel_output", shell=True)
			sDict[machineNum][workload] = int(storage_result.strip().split("\t")[1])
			
			
		print machineNum
		print fDict[machineNum]
		print gDict[machineNum]
	'''		
	fDict = {8: {128: 2092730.0, 256: 4002640.5, 32: 600774.0, 8: 157966.0, 64: 1091113.5, 16: 332408.0}, 1: {32: 4763512.0, 1: 668772.0, 2: 593812.0, 4: 1265212.0, 8: 1664700.0, 16: 2124404.0}, 2: {64: 5351118.0, 32: 2436642.0, 2: 436516.0, 4: 507500.0, 8: 852014.0, 16: 1431126.0}, 4: {128: 4142920.0, 64: 2262392.0, 4: 307910.0, 32: 1286833.0, 8: 405493.0, 16: 672787.0}}	
	gDict = {8: {128: 2073540.5, 256: 3949585.5, 32: 600774.0, 8: 138606.0, 64: 1088894.0, 16: 331506.5}, 1: {32: 4586140.0, 1: 554096.0, 2: 530316.0, 4: 1036008.0, 8: 1435876.0, 16: 1937696.0}, 2: {64: 4931084.0, 32: 2287808.0, 2: 427938.0, 4: 432796.0, 8: 740890.0, 16: 1253024.0}, 4: {128: 3980509.0, 64: 2210550.0, 4: 262323.0, 32: 1270824.0, 8: 354073.0, 16: 655921.0}}
	fDict2 = {8: [0.2030690148512971, 0.1720822001877211, 0.15939438124818983, 0.14874483726944998, 0.14843792558046187, 0.14515742795287262], 1: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0], 2: [0.553505484335053, 0.5687251231527094, 0.5647864941186412, 0.5661262530343241, 0.5578529796334464, 0.551887287852744], 4: [0.3208340099379689, 0.30941101326040155, 0.2999641788560124, 0.2947616357367273, 0.28607509220329636, 0.2819774458594421]}
	gDict2 = {8: [0.2254916814567912, 0.17255016115822766, 0.15939438124818983, 0.14904802487661792, 0.1478075783906801, 0.1465237301483915], 1: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0], 2: [0.5646004795087138, 0.5853011580513683, 0.574171604421709, 0.5866799039763005, 0.5764347357820236, 0.568721198016501], 4: [0.3362114644922481, 0.32015996701245225, 0.3076772965036948, 0.2892139273416303, 0.28766687023591414, 0.2863797067158999]}
	sDict = {8: {128: 800468207, 256: 1599448337, 32: 205512240, 8: 57510834, 64: 402525698, 16: 106494871}, 1: {32: 209379070, 1: 11128487, 2: 18493435, 4: 30138440, 8: 57531161, 16: 109449820}, 2: {64: 402551110, 32: 205010132, 2: 17462491, 4: 30538442, 8: 54851707, 16: 105891573}, 4: {128: 800838384, 64: 406399876, 4: 29504719, 32: 199374444, 8: 54831809, 16: 103623150}}
	
	
	
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
		popt, _ = curve_fit(func, xdata, ydata, maxfev=3000)
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
		popt, _ = curve_fit(func2, xdata, ydata, maxfev=3000)
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
	W0 = [64+32*i for i in range(7)]
	WS = []
	for i in machine_list:
		WS.append([j*i for j in W0])

	M = 16*0.9*1024*1024


	print "Method 4:"
	i = 0
	for machineNum in machine_list:
		print machineNum
		f_factor = max(fDict2[machineNum])
		tmp_f_popt = [ x*(machineNum*f_factor) for x in f_popt[machineNum]]
		tmp_f_popt[1] = f_popt[machineNum][1]
		g_factor = max(gDict2[machineNum])
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
	 

