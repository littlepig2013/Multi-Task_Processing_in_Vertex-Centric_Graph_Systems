import sys

def memLineHandler(line, maxMem):
	tmp = line.strip().split("=")
	tmp = tmp[1].split('/')
	freeMem = float(tmp[0].strip()[0:-1])
	totalMem = float(tmp[1].strip()[0:-1])
	tmpMem = totalMem - freeMem
	if maxMem < tmpMem:
		maxMem = tmpMem
	return maxMem


highMem = 0
staggedMem = 0
if len(sys.argv) != 2:
	print("Illegal parameter number")
else:
	f = open(sys.argv[1], "r")
	data = f.readlines()
	for line in data:
		if line.startswith("Memory Info before"):
			highMem = memLineHandler(line, highMem)
		elif line.startswith("Memory Info after"):
			staggedMem = memLineHandler(line, staggedMem) 

	print("Highest Memory: " + str(highMem) + "M")
	print("Stagged Memory: " + str(staggedMem) + "M")

	f.close()

