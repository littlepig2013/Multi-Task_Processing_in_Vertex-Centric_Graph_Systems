import json, os


def memLineHandler(line, maxMem):
	tmp = line.strip().split("=") 
	tmp = tmp[1].split('/')
	freeMem = float(tmp[0].strip()[0:-1]) 
	totalMem = float(tmp[1].strip()[0:-1]) 
	tmpMem = totalMem - freeMem
	if maxMem < tmpMem:
		maxMem = tmpMem
	return maxMem

hosts=["localhost"]

JSON_FILENAME="data.json"
HADOOP_USERLOG_PATH ="~/hadoop/tmp/mapred/local/userlogs/"

data = dict()
if os.path.exists(JSON_FILENAME):
	json_fin = open(JSON_FILENAME,"r")
	data = json.load(json_fin)
	json_fin.close()

if "dblp" not in data:
	data["dblp"] = {"ppr":dict(),"sssp":dict()}
if "ppr" not in data["dblp"]:
	data["dblp"]["ppr"] = dict()
if "sssp" not in data["dblp"]:
	data["dblp"]["sssp"] = dict()
if "web_stanford" not in data:
	data["web_stanford"] = {"ppr":dict(),"sssp":dict()}
if "ppr" not in data["web_stanford"]:
	data["web_stanford"]["ppr"] = dict()
if "sssp" not in data["web_stanford"]:
	data["web_stanford"]["sssp"] = dict()

dataset="web_stanford"
algo="ppr"

for host in hosts:
	os.system("rsync -rav -e ssh --exclude='*/syslog' --exclude='*/log.index' " + host + ":" + HADOOP_USERLOG_PATH + "/job_* log_agg/")

for f in os.listdir("./log_agg/"):
	if f.startswith("job"):
		if f not in data[dataset][algo]:
			fs = os.listdir("./log_agg/" + f)
			highMem = 0
			staggedMem = 0
			workerCount = 0
			for tmpf in fs:
				if tmpf.startswith("attempt"):
					fname = "./log_agg/"+f+"/"+tmpf+"/stdout"
					outf = open(fname)
					outputs = outf.readlines()
					if len(outputs) == 0:
						outf.close()
						continue
					for line in outputs:
						if line.startswith("Memory Info before"):
							highMem = memLineHandler(line, highMem)
						elif line.startswith("Memory Info after"):
							staggedMem = memLineHandler(line, staggedMem)
						elif line.startswith("Worker Count"):
							workerCount = int(line.strip().split("=")[1].strip().split(" ")[0])
					outf.close()
			print("Job ID: " + f)
			print("Highest Memory: " + str(highMem) + "M")
			print("Stagged Memory: " + str(staggedMem) + "M")
			if workerCount == 0:
				print("Warning: no worker found")
			else:
				data[dataset][algo][f] = {"workerCount":workerCount,"HWM":highMem,"RSS":staggedMem}

json_fout = open(JSON_FILENAME,"w")
json.dump(data, json_fout)
json_fout.close()

