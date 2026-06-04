import re

def numrepl(matchobj):
    return matchobj.group(1)

data = ""
g = input()
while g != "":
	data += re.sub(r"(\d+\.\d{2})\d+",numrepl, g) + "\n"
	g = input()

print(data)