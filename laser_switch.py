import serial
import time

def connect():
    arduino = serial.Serial('COM4', 9600)
    time.sleep(2)
    return arduino

def send_command(arduino, command):
    arduino.write(command.encode())

def disconnect(arduino):
    arduino.close()