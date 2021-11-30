import os, sys, time, copy
MAXIMUM_ITERATION = sys.maxint
REFRESH_INTERVAL = 2.0

filename="~/net-measurement/bandwidth_measure_output.txt"

f_test=open(filename_test, 'w')

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

#cmd = "ps aux | grep -v 'sh -c' | grep [p]ersonalized_pagerank | awk '{print $2}' | sort -d | head -1" 
cmd = "ps aux | grep -v 'sh -c' | grep -v 'mpiexec'| grep [d]blp_pregelplus | awk '{print $2}' | sort -d | head -1" 
while True:
	pid = os.popen(cmd).read().strip()
	if pid != "":
		break
	time.sleep(0.1*REFRESH_INTERVAL)
print(pid)
fileName = "/proc/" + pid + "/net/dev"
old_net_data = [0, 0, 0, 0]
start_net_data = [0, 0, 0, 0]
diff = [0, 0, 0, 0]
max_diff = [0, 0, 0, 0]
bandwidth_bound=125*1024*1024
overuse_acc=0
if os.path.exists(fileName):
	old_net_data = readNetFile(fileName)
	start_net_dat = copy.copy(old_net_data)


time.sleep(REFRESH_INTERVAL)
iteration = 0
start_time = time.time()
while pid != '':
	fileName = "/proc/" + pid + "/net/dev"
	new_net_data= readNetFile(fileName)
	if new_net_data == None:
		break
	
		
	for i in range(4):
		diff[i] = new_net_data[i] - old_net_data[i]
	if diff[0] + diff[2] > max_diff[0] + max_diff[2]:
		max_diff = copy.copy(diff)
	if diff[0] + diff[2] > bandwidth_bound:
		overuse_acc += 1
	#print("\t".join([str(x) for x in diff]))
	#print(diff)
	old_net_data = copy.copy(new_net_data)
	end_time = time.time()
	if REFRESH_INTERVAL > end_time - start_time:
		time.sleep(REFRESH_INTERVAL - (end_time - start_time))
	iteration += 1
		
	if iteration >= MAXIMUM_ITERATION:
		break	
	start_time = time.time()
	pid = os.popen(cmd).read().strip()

print(str(iteration*REFRESH_INTERVAL) + " seconds passed.")
print(max_diff)
print(old_net_data)
os.system("rm " + filename)
f = open(filename, 'w')
		
f.write("Max-Recv-Bytes\tMax-Recv-Pack\tMax-Trans-Bytes\tMax-Trans-Pack\n")
f.write('\t'.join([str(x/(REFRESH_INTERVAL)) for x in max_diff]) + "\n")
#f.write('\t'.join([str(x) for x in max_diff_iteration])+"\n")

tmp = [ old_net_data[i] - start_net_data[i] for i in range(4)]
old_net_data = copy.copy(tmp)
print(old_net_data)
f.write("Avg-Recv-Bytes\tAvg-Recv-Pack\tAvg-Trans-Bytes\tAvg-Trans-Pack\n")
f.write('\t'.join([str(x/(REFRESH_INTERVAL*iteration)) for x in old_net_data])+"\n")
f.write("Overuse-time\n")
f.write(str(overuse_acc*REFRESH_INTERVAL)+"\n")
f.close()

