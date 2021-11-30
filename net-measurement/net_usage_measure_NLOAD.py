import os, sys, time, copy,re, subprocess
MAXIMUM_ITERATION = sys.maxint
REFRESH_INTERVAL = 2.0

filename_output="~/net-measurement/bandwidth_measure_output.txt"
filename="~/net-measurement/bandwidth_measure_test.txt"

def kill(tag):
	while True:
		out = os.popen("ps aux | grep [" + tag[0] + "]" + tag[1:] + " | grep -v sh"  ).read()
		line = ""
		tmp = out.splitlines()
		#print(tmp)
		if len(tmp) >= 1:
			line = out.splitlines()[0]
			pid = int((re.split(" *", line.strip()))[1])
			try:
				os.system("kill -9 " + str(pid))
				#os.kill(pid, signal.SIGKILL)
			except:
				pass
			finally:
				time.sleep(10)
		else:
			break
	

def readNetFile(fileName):
	if os.path.exists(fileName):
		f = open(fileName, 'r')
		data = f.readlines()[2:]
		for line in data:
			tmp = line.strip().split(':')
			if tmp[0].endswith("eth0"):
				net_data = tmp[1].strip().split()
				f.close()
				return int(net_data[0]), int(net_data[1]), int(net_data[8]), int(net_data[9])
	else:
		return None

if __name__ == "__main__":
	#cmd = "ps aux | grep -v 'sh -c' | grep [p]ersonalized_pagerank | awk '{print $2}' | sort -d | head -1" 
	os.system("rm " + filename)
	print("test")
	cmd = "ps aux | grep -v 'sh -c' | grep -v 'mpiexec'| grep [d]blp_pregelplus | awk '{print $2}' | sort -d | head -1" 
	while True:
		pid = os.popen(cmd).read().strip()
		print(pid)
		if pid != "":
			break
		time.sleep(0.1*REFRESH_INTERVAL)

	os.system("nohup nload -f " + filename + " > /dev/null &")
	#subprocess.call("./net-measure.sh")
	print(pid)

	while True:
		pid = os.popen(cmd).read().strip()
		if pid == "":
			break
		time.sleep(2*REFRESH_INTERVAL)
	kill("nload")
	os.system("grep eth0 " + filename + "|awk 'BEGIN{maxIn=0;maxOut=0;maxB=0;sumIn=0;sumOut=0;}{if($6 + $7 > maxB){maxIn=$6;maxOut=$7;maxB=$6+$7;}sumIn+=$6;sumOut+=$7;}END{print maxIn,maxOut,sumIn*1.0/NR,sumOut*1.0/NR}' > ~/net-measurement/tmp-xxxxx.txt")

	f1 = open("~/net-measurement/tmp-xxxxx.txt","r")
	data = f1.readline()
	tmp = data.strip().split(' ')
	f1.close()

	os.system("rm " + filename_output) 
	f = open(filename_output, 'w')		
	f.write("Max-Recv-Bytes\tMax-Recv-Pack\tMax-Trans-Bytes\tMax-Trans-Pack\n")
	f.write(tmp[0] + "\t0\t" + tmp[1] + "\t0\t"+ "\n")

	f.write("Avg-Recv-Bytes\tAvg-Recv-Pack\tAvg-Trans-Bytes\tAvg-Trans-Pack\n")
	f.write(tmp[2] + "\t0\t" + tmp[3] + "\t0\t"+ "\n")
	f.close()

