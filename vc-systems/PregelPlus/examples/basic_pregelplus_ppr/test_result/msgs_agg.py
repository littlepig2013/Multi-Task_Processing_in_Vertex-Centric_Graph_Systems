import sys

inputFile = sys.argv[1]
machineNum = int(sys.argv[2])

f = open(inputFile, 'r')
data = f.readlines()

max_msgs = 0
agg_msg_flag = False
agg_msgs = 0
max_agg_msgs = 0
for line in data:
	tmp = line.strip().split(' ')
	if tmp[0] == 'Superstep':
		if max_agg_msgs < agg_msgs:
			max_agg_msgs = agg_msgs
		agg_msgs = 0
		agg_msg_flag = True
	if len(tmp) >= 2:
		if tmp[1] == 'sent':
			msgs = int(tmp[2])
			if max_msgs < msgs:
				max_msgs = msgs
			if agg_msg_flag:
				agg_msgs += msgs

print("max avg #msgs: " + str(max_agg_msgs*1.0/machineNum))
print("max #msgs: " + str(max_msgs))
	
