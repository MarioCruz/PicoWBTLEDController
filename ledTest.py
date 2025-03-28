import bluetooth
from machine import Pin
import time

# Initialize the external LED on GPIO 16
led = Pin(16, Pin.OUT)

# BLE Configuration
ble = bluetooth.BLE()
ble.active(True)

# Custom Service and Characteristic UUIDs 
LED_SERVICE_UUID = bluetooth.UUID("19B10000-E8F2-537E-4F6C-D104768A1214")
LED_CHAR_UUID = bluetooth.UUID("19B10001-E8F2-537E-4F6C-D104768A1214")

# Register BLE services and characteristics
services = (
    (LED_SERVICE_UUID, (
        (LED_CHAR_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_READ),
    )),
)

((led_char_handle,),) = ble.gatts_register_services(services)

# Set initial value for characteristic
ble.gatts_write(led_char_handle, b'\x00')  # LED initially OFF

# IRQ handler with correct constant names
def ble_irq(event, data):
    # Use the proper IRQ constant names for your firmware
    if event == 1:  # _IRQ_CENTRAL_CONNECT
        print("BLE Connected")
        
    elif event == 2:  # _IRQ_CENTRAL_DISCONNECT
        print("BLE Disconnected")
        # Restart advertising
        ble.gap_advertise(100, adv_payload)
        
    elif event == 3:  # _IRQ_GATTS_WRITE
        # Handle write to characteristic
        conn_handle, attr_handle = data
        if attr_handle == led_char_handle:
            value = ble.gatts_read(led_char_handle)
            print("Received:", value)
            
            if value == b'\x01':
                led.value(1)  # Turn LED ON
                print("LED ON")
            elif value == b'\x00':
                led.value(0)  # Turn LED OFF
                print("LED OFF")

# Register IRQ handler
ble.irq(ble_irq)

# Simple advertising payload
device_name = 'PicoW-LED'
adv_payload = bytearray()
adv_payload += b'\x02\x01\x06'  # Standard flags for general discovery
adv_payload += bytes([len(device_name) + 1, 0x09]) + device_name.encode()  # Complete name

# Start advertising
ble.gap_advertise(100, adv_payload)
print(f"Advertising as {device_name}")

# Test the LED at startup
print("Testing LED on GP16...")
led.value(1)  # Turn on
time.sleep(1)
led.value(0)  # Turn off
print("LED test complete, BLE service is running")

# Main loop
while True:
    time.sleep_ms(100)