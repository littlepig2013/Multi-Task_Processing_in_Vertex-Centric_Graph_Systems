import json, os
from scipy.optimize import curve_fit
import numpy as np


def func(x, a, b, c):
	return a*(x**b) + c

workload_list = [2**i for i in range(1,8)]
data_json_file="data.json"
params_json_file="params.json"

params=dict()
if os.path.exists(data_json_file):
	data_json_fin = open(data_json_file,"r")
	data = json.load(data_json_fin)
	data_json_fin.close()
	for dataset in data:
		params[dataset] = dict()
		x = data[dataset]
		for algo in x:
			params[dataset][algo] = dict()
			y = x[algo]
			workers2mem = dict()
			for t in y:
				workercount = y[t]["workerCount"]
				if workercount not in workers2mem:
					workers2mem[workercount] ={"HWM":[],"RSS":[]}
				workers2mem[workercount]["HWM"].append(y[t]["HWM"])
				workers2mem[workercount]["RSS"].append(y[t]["RSS"])
				
			xdata = []
			ydata = []
			ydata2 = []
			for worker in workers2mem:
				params[dataset][algo][worker] = dict()
				xdata = [i*worker for i in workload_list]
				ydata = workers2mem[worker]["HWM"]
				ydata.sort()
				ydata = [i*1024 for i in ydata]
				ydata2 = workers2mem[worker]["RSS"]
				ydata2.sort()
				ydata2 = [i*1024 for i in ydata2]
				#g_popt, _ = curve_fit(func, xdata, ydata2,bounds=[(0,0.5,0),(np.inf,1.5,np.inf)], maxfev=1000)
				g_popt, _ = curve_fit(func, xdata, ydata2, maxfev=3000)
				#f_popt, _ = curve_fit(func, xdata, ydata,bounds=[(0,g_popt[1],0),(np.inf,1.5,np.inf)], maxfev=1000)
				f_popt, _ = curve_fit(func, xdata, ydata, maxfev=3000)
				params[dataset][algo][worker]["HWM"] = f_popt.tolist()
				params[dataset][algo][worker]["RSS"] = g_popt.tolist()
	params_json_fout = open(params_json_file, "w")
	json.dump(params, params_json_fout, indent=4,sort_keys=True)
	params_json_fout.close()	
		
else:
	print("data.json not exists")
