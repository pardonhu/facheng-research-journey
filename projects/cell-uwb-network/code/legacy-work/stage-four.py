from four_io import *
b=boards[3]
command(b,f"h\nloadfile {(b['build']/'uwb-four.hex').as_posix()}\nr\ng\nsleep 200")
start(b,1,12345,3000,0,7,500,1000,5)
for i in range(10):
 try: print(i,read(b),flush=True)
 except Exception as e: print(str(e)[-1500:],flush=True)
 time.sleep(.3)
