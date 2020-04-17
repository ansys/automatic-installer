import sys

# FUNCTIONS

def start():
    print('I STARTED FROM WITHIN NODE.JS', flush=True)
    with open(r"D:\1.txt", "w") as file:
        file.write("Start\n")

def respond():
    print('I GOT hello FROM NODE.JS -> HI THERE EXAMPLE ANALYZER', flush=True)
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
    elif  "hello" in line:
        respond()
    elif "start" in line:
        start()
    elif line:
        print('dunno')
