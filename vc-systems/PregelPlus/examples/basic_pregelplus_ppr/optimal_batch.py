import os, sys
from scipy.optimize import curve_fit
import numpy as np
import math
import subprocess

#machine_list =  [ 1+i*2 for i in np.arange(4)]
machine_list =  [ 2**i for i in np.arange(4)]
workload_list = 2**np.arange(3, 9)


CONF=" -f ~/vc-systems/PregelPlus/examples/basic_pregelplus_ppr/test_tmp_conf"
EXECUTABLE_FILE=" ~/vc-systems/PregelPlus/examples/basic_pregelplus_ppr/run"
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
'''
def func2(workload, a, b, c, d):
	return a*workload + b*workload*workload + c*workload*workload*workload + d

def func2_params(workload, params):
	return params[0]*workload + params[1]*workload*workload + params[2]*workload*workload*workload + params[3]
'''

def method1(W, M, params, params2):#f(w)+(g(W))-(g(w)) = M
	diff = float("inf")
	final_w = 0
	for i in range(1, W+1):
		tmp_result = M - (func_params(i, params) + func2_params(W, params2) - func2_params(i, params2))
		if tmp_result > 0 and final_w < i:
			diff = tmp_result
			final_w = i
	return final_w

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
		M -= func2_params(final_w, params2) - (func2_params(0, params2))
		#M -= func_params(final_w, params) - func_params(0, params)
		#print str(M)
		final_ws.append(final_w)
		if W <= 0 or M < 0:
			break	
	final_ws.reverse()
	#print(sum(final_ws))
	return final_ws


def method3(W, M, params, params2):#min(f(w)+g(W-w))
	final_ws = []
	while True:
		final_w = 0
		min_mem = float("inf")
		for i in range(1, W+1):
			tmp_result = abs(M - (func_params(i, params) + func2_params(W-i, params2)) + func_params(0, params))
			if tmp_result < min_mem:
				min_mem = tmp_result
				final_w = i
		if final_w == 0:
			break
		W -= final_w
		M -= func_params(final_w, params) - func_params(0, params2)
		final_ws.append(final_w)
		if W <= 0:
			break	
	final_ws.reverse()
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
	

def getUpdatedWorkloadList(workload_list, machine):
	if machine == 1:
		return workload_list
	else:
		fstElement = workload_list[0]
		lstElement = workload_list[-1]
		lstElement *= machine*1.0/(machine-1)
		length = len(workload_list)
		growth_rate = math.pow(lstElement*1.0/fstElement, 1.0/(length - 1))
		newWorkload_list = [ round(fstElement*math.pow(growth_rate, i)) for i in range(length) ]
		return np.array(newWorkload_list)


if __name__ == '__main__':
	'''
	OUTPUT_FILE="test.out"
	max_stay_mem = 0
	
	for machineNum in machine_list:
		print("machine number: " + str(machineNum))
		os.system("head -" + str(machineNum) + " /root/vc-systems/PregelPlus/examples/basic_pregelplus_ppr/tmp_conf > test_tmp_conf")
		os.system("./sync1.sh 3")
		fDict[machineNum] = dict()
		gDict[machineNum] = dict()
		fDict2[machineNum] = []
		gDict2[machineNum] = []
		sDict[machineNum] = dict()
		if machineNum != 1:
			workload_list = workload_list*2
		for i in range(len(workload_list)):
			workload=workload_list[i]
			print("\t"+str(workload))
			os.system("echo " + str(workload) + "' > batchedRWs.txt")
			#os.system("sh getBatchedSeeds.sh " + str(BATCH) + " " + str(workload))
			os.system("./sync1.sh 4")
			#os.system("mpiexec -n " + str(machineNum) + " " + CONF + " " + EXECUTABLE_FILE +" 1 >> " + OUTPUT_FILE)
			os.system("mpiexec -n " + str(machineNum) + " " + CONF + " " + EXECUTABLE_FILE + " " + str(machineNum) + " 1 >" + OUTPUT_FILE)
			#output_tmp = subprocess.check_output("$HADOOP_HOME/bin/hadoop dfs -cat /blogel_output/p* | wc -c", shell=True)
			#max_stay_mem_tmp = int(output_tmp.strip())*1.0/machineNum
			#print max_stay_mem_tmp
			#if max_stay_mem_tmp > max_stay_mem:
			#	max_stay_mem = max_stay_mem_tmp
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
	#print str(max_stay_mem) + " bytes"
	'''
	fDict = {8: {64: 218316.5, 128: 392833.5, 1024: 2069781.0, 256: 699551.0, 512: 1148762.0, 2048: 3993044.5}, 1: {128: 2487204.0, 256: 4597692.0, 32: 956932.0, 8: 471196.0, 64: 1501152.0, 16: 671876.0}, 2: {32: 557624.0, 128: 1646498.0, 64: 882126.0, 256: 3053892.0, 16: 392060.0, 512: 5821664.0}, 4: {32: 275770.0, 64: 430222.0, 1024: 4407796.0, 128: 724859.0, 256: 1317760.0, 512: 2405501.0}}
	gDict = {8: {64: 190359.5, 128: 304882.5, 1024: 1224868.5, 256: 459009.5, 512: 736088.0, 2048: 2070946.5}, 1: {128: 2143204.0, 256: 3473376.0, 32: 956932.0, 8: 471196.0, 64: 1423052.0, 16: 671876.0}, 2: {32: 492402.0, 128: 1110332.0, 64: 668336.0, 256: 1760134.0, 16: 374138.0, 512: 2899222.0}, 4: {32: 260023.0, 64: 374729.0, 1024: 2419467.0, 128: 559124.0, 256: 890792.0, 512: 1455326.0}}
	fDict2 = {8: [0.19441498924726258, 0.16265287965512107, 0.1408596371100892, 0.1371920380374699, 0.13526286114328037, 0.13050781177119364], 1: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0], 2: [0.5433862163954497, 0.504271695622857, 0.5049051949494744, 0.5212274779562441, 0.5330614180200217, 0.5397896546416969], 4: [0.33527939949958296, 0.29358563718266384, 0.26232550054562337, 0.2517734640602234, 0.25727862927514894, 0.25650143518438695]}
	gDict2 = {8: [0.17996212429639707, 0.15108771411937386, 0.15995093783461997, 0.13578879155753115, 0.13332410785321036, 0.12988384779616471], 1: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0], 2: [0.5602585142380619, 0.5485964719883347, 0.5263161044743961, 0.5277520597442927, 0.5129291292594769, 0.5064951907787676], 4: [0.3256481157436073, 0.30092413450787103, 0.2879271860982537, 0.27279207716279447, 0.2648657414215097, 0.25687682452374844]}
	sDict = {8: {64: 253132138, 128: 429617095, 1024: 2141159255, 256: 730378671, 512: 1241418423, 2048: 3714292135}, 1: {128: 425393620, 256: 730806257, 32: 155905294, 8: 53546284, 64: 261659451, 16: 94753186}, 2: {32: 153221157, 128: 427726889, 64: 234641602, 256: 729135219, 16: 99933771, 512: 1251412485}, 4: {32: 157273984, 64: 257470375, 1024: 2145825196, 128: 431867508, 256: 724549601, 512: 1246686484}}

	
	print fDict
	print gDict
	print fDict2
	print gDict2
	print "Storage Cost"
	print sDict
	f_popt = {}
	for machineNum in fDict:
		xdata = []
		ydata = []
		for workload in fDict[machineNum]:	
			xdata.append(workload)
			ydata.append(fDict[machineNum][workload])
		xdata=np.array(xdata)
		ydata=np.array(ydata)
		popt, _ = curve_fit(func, xdata, ydata, maxfev=1000)
		#print machineNum
		#print popt
		f_popt[machineNum]=popt
	print f_popt
	g_popt = {}
	for machineNum in gDict:
		xdata = [] 
		ydata = []
		for workload in gDict[machineNum]:
			xdata.append(workload)
			ydata.append(gDict[machineNum][workload])
		xdata = np.array(xdata)
		ydata = np.array(ydata)
		popt, _ = curve_fit(func2, xdata, ydata, maxfev=1000)
		#print machineNum
		#print popt
		g_popt[machineNum]=popt
	print g_popt
	
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

	W = 4096
	W0 = [768+128*i for i in range(3)]
	WS = []
	for i in machine_list:
		WS.append([j*i for j in W0])
	

	M = 16*0.85*1024*1024
	
	
	print "Method 3"
	i = 0
	for machineNum in machine_list:
		print "\tMachine Num: " + str(machineNum)
		f_factor = max(fDict2[machineNum])
		tmp_f_popt = [ x*(machineNum*f_factor) for x in f_popt[machineNum]]
		tmp_f_popt[1] = f_popt[machineNum][1]
		g_factor = max(gDict2[machineNum])
		tmp_g_popt = [ x*(machineNum*g_factor) for x in g_popt[machineNum]]
		tmp_g_popt[1] = g_popt[machineNum][1]
		for w in WS[i]:
			print w
			ws = method3(w, M, tmp_f_popt, tmp_g_popt)
			#ws = method4(w, M, tmp_f_popt, tmp_g_popt, s_popt[machineNum])
			#ws = method4(w, M, f_popt[index], g_popt[index])
			print str(w) + "\t"+str(ws) + "\t"
		i += 1
		print ""
	
