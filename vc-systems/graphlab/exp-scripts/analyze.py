import sys
workers=[1,2,4,8,16]
lines = sys.stdin.readlines()
j=0
print(len(lines))
for worker in workers:
	s = 0
	for i in range(worker):
		tmp = lines[j].strip().split(" ")
		s += float(tmp[-1])/1024/1024/1024
		j += 1
	print("Worker " + str(i) + " : " + str(float(s/worker)))
