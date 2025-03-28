from machine import Pin
import time

# Initialize external LED on GPIO 16
led = Pin(16, Pin.OUT)

# Simple blink test
print("Testing external LED on GP16...")
for _ in range(5):
    led.value(1)  # Turn on
    print("LED ON")
    time.sleep(3)
    led.value(0)  # Turn off
    print("LED OFF")
    time.sleep(1)

print("Test complete")