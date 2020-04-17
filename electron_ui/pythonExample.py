import sys

# FUNCTIONS

def start():
    print('I STARTED and asked to install FROM WITHIN NODE.JS', flush=True)
    with open(r"D:\1.txt", "w") as file:
        file.write("Start install once\n")

def respond():
    print('schedule update man', flush=True)
    with open(r"D:\1.txt", "a") as file:
        file.write('I GOT hello FROM NODE.JS -> HI THERE EXAMPLE ANALYZER\n')

def ender():
    print('I GOT exit FROM NODE.JS -> I STOPPED FROM WITHIN NODE.JS', flush=True)
    exit()


# CODE

while True:
    line = sys.stdin.readline()
    if "exit" in line:
        ender()
    elif  "schedule_update" in line:
        respond()
    elif "install_once" in line:
        start()
    elif line:
        print('dunno')
