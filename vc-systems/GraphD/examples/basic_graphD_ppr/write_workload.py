
fout = open("test_result/test_workload","w")
W =2048
WS = [W]
#WS = [W-1024,W,W+1024]
#WS = list(range(W,W*2+256, 256))
deltas = [0]
#deltas = [3,4]
deltas = [0]
batches = [2**i for i in range(8)]
#batches = [1]
#machines = [2**i for i in range(4)]
machines = [27]

for Wi in WS: 
	for machine_num in machines:
		baseW = Wi#*machine_num
		deltaW = baseW/16
		for delta in deltas:
			tmpW = baseW + delta*deltaW			
			for batch_num in batches:
				s = str(machine_num)+"\t"
				splitW = tmpW/batch_num
				if splitW*batch_num < tmpW:
					splitW += 1
				leftW = tmpW
				firstFlag = True
				while leftW > 0:
					if not firstFlag:
						s += " "
					if leftW > splitW:
						s += str(splitW)
						leftW -= splitW
					else:
						s += str(leftW)
						leftW = 0
					firstFlag = False

				s += "\n"
		
				fout.write(s)
