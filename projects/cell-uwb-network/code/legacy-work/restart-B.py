from four_io import *
b=boards[1]
print(command(b,'r\ng\nsleep 100'))
start(b,1,234,3000,0,7,500,1000,5)
time.sleep(.3);print(read(b))
