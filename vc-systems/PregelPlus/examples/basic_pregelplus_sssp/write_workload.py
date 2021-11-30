
fout = open("test_result/test_workload","w")
W = 128*8
WS = [W]
#deltas = [1, 2, 3, 4, 5, 6, 7, 8]
deltas = [4]
batches = [i for i in range(5, 16)]
#batches = [1]
#machines = [2**i for i in range(4)]
machines = [8]

for Wi in WS: 
	for machine_num in machines:
		baseW = Wi#*machine_num
		deltaW = baseW
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
