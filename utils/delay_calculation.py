import serial
import time
import json

port = '/dev/ttyUSB0'
baudrate = 115200
timeout = 10
duration = 30  # Time for read answer
speed = 0
number_of_rollers = 46 # not used
top_nozzle_distance = 315 # mm, near (left)
bottom_nozzle_distance = top_nozzle_distance + 30 # mm, far (right)

ser = serial.Serial(port, baudrate, timeout=timeout)

time.sleep(1)

start_time = time.time()

try:
    print(f"send: S1")
    ser.write(b'S1\n')
    data = ser.readline().decode('utf-8').strip()  
    print(f"received: {data}")
    print(f"Nozzle distance\n\ttop: {top_nozzle_distance}mm\n\tbottom: {bottom_nozzle_distance}mm\n\nReceiving & calculation, waiting...")
    while time.time() - start_time < duration:
        if ser.in_waiting > 0:
            json_string = ser.readline().decode('utf-8').strip()  
            print(f"received: {json_string}")
            data = json.loads(json_string)
            speed = data['speed']
            if speed > 0:
                top_nozzle = top_nozzle_distance / speed
                bottom_nozzle = bottom_nozzle_distance / speed
                print(f"Speed: {speed}\n\tnozzle delay: Top(near, left): {top_nozzle}\n\tBottom: (far, right): {bottom_nozzle}\n")

    print(f"send: S0")
    ser.write(b'S0\n')
    data = ser.readline().decode('utf-8').strip()  
    print(f"received: {data}")


except serial.SerialException as e:
    print(f"Failed with Serial: {e}")

finally:
    ser.close()
