f = open("test_result/test_workload","w")
W = 20480
num_of_machines = 27
deltaW = W/20

f.write(str(num_of_machines) + "\t" + str(W/2) + " " + str(W/2) + "\n")
f.write(str(num_of_machines) + "\t" + str(W/2) + "\n")
for i in range(2,9,2):
	f.write(str(num_of_machines) + "\t" + str(W/2-i*deltaW) + " " + str(W/2+i*deltaW) + "\n")
	f.write(str(num_of_machines) + "\t" + str(W/2+i*deltaW) + " " + str(W/2-i*deltaW) + "\n")
	f.write(str(num_of_machines) + "\t" + str(W/2-i*deltaW) + "\n")
	f.write(str(num_of_machines) + "\t" + str(W/2+i*deltaW) + "\n")
f.write(str(num_of_machines) + "\t" + str(W))

f.close()
