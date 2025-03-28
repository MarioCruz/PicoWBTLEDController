import bluetooth
from machine import Pin, PWM
import time
import struct

# Initialize the external LED on GPIO 16
led_pin = Pin(16, Pin.OUT)

# Create PWM for brightness control
try:
    pwm = PWM(led_pin)
    pwm.freq(1000)  # Set frequency to 1kHz
    pwm.duty_u16(0)  # Start with LED off
    pwm_enabled = True
    print("PWM initialized successfully")
except Exception as e:
    pwm_enabled = False
    print(f"PWM initialization failed: {e}")
    print("Falling back to digital control only")

# Global state
pattern_active = False
stop_current_pattern = False

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

# Helper function to safely turn LED on/off
def set_led(state):
    """Set LED state with fallback between PWM and digital"""
    global pwm_enabled
    
    if state:  # Turn on
        if pwm_enabled:
            try:
                pwm.duty_u16(65535)  # Full brightness
            except:
                pwm_enabled = False
                led_pin.value(1)  # Fallback to digital
        else:
            led_pin.value(1)
    else:  # Turn off
        if pwm_enabled:
            try:
                pwm.duty_u16(0)  # Zero brightness
            except:
                pwm_enabled = False
                led_pin.value(0)  # Fallback to digital
        else:
            led_pin.value(0)

# LED pattern functions
def led_on():
    set_led(True)
    print("LED ON")

def led_off():
    set_led(False)
    print("LED OFF")

def led_flash(times=3, speed_ms=200):
    """Flash LED on and off n times"""
    global stop_current_pattern
    
    print(f"Flashing LED {times} times")
    for i in range(times):
        if stop_current_pattern:
            break
        set_led(True)
        time.sleep_ms(speed_ms)
        set_led(False)
        if i < times - 1:  # Don't sleep after last flash
            time.sleep_ms(speed_ms)

def led_pulse(cycles=3, step_ms=30):
    """Pulse LED brightness up and down n times"""
    global stop_current_pattern, pwm_enabled
    
    if not pwm_enabled:
        # Fallback to simple flashing if PWM is not available
        print("PWM not available, falling back to flash pattern")
        led_flash(cycles * 2, 300)
        return
    
    print(f"Pulsing LED {cycles} times")
    try:
        for _ in range(cycles):
            if stop_current_pattern:
                break
                
            # Fade in
            for duty in range(0, 65535, 2048):
                if stop_current_pattern:
                    break
                pwm.duty_u16(duty)
                time.sleep_ms(step_ms)
            
            # Fade out
            for duty in range(65535, 0, -2048):
                if stop_current_pattern:
                    break
                pwm.duty_u16(duty)
                time.sleep_ms(step_ms)
        
        # Ensure off at end
        pwm.duty_u16(0)
    except Exception as e:
        print(f"PWM error: {e}")
        pwm_enabled = False
        set_led(False)

def led_sos():
    """SOS pattern (... --- ...)"""
    global stop_current_pattern
    
    print("SOS pattern")
    # Define dot and dash durations in ms
    dot = 150
    dash = 450
    pause_between = 150
    pause_letter = 350
    
    # S (...)
    for _ in range(3):
        if stop_current_pattern:
            break
        set_led(True)
        time.sleep_ms(dot)
        set_led(False)
        time.sleep_ms(pause_between)
    
    time.sleep_ms(pause_letter)
    
    # O (---)
    for _ in range(3):
        if stop_current_pattern:
            break
        set_led(True)
        time.sleep_ms(dash)
        set_led(False)
        time.sleep_ms(pause_between)
    
    time.sleep_ms(pause_letter)
    
    # S (...)
    for _ in range(3):
        if stop_current_pattern:
            break
        set_led(True)
        time.sleep_ms(dot)
        set_led(False)
        time.sleep_ms(pause_between)

def led_heartbeat():
    """Simulate heartbeat pattern"""
    global stop_current_pattern
    
    print("Heartbeat pattern")
    # Do 3 heartbeats
    for _ in range(3):
        if stop_current_pattern:
            break
        # First beat (stronger)
        set_led(True)
        time.sleep_ms(150)
        set_led(False)
        time.sleep_ms(100)
        
        # Second beat (weaker)
        set_led(True)
        time.sleep_ms(100)
        set_led(False)
        time.sleep_ms(600)  # Longer pause between heartbeats

# IRQ handler
def ble_irq(event, data):
    global pattern_active, stop_current_pattern
    
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
            
            # Process the command
            if len(value) == 1:
                command = value[0]
                print(f"Setting LED mode to {command}")
                
                # Stop any active pattern
                if pattern_active:
                    stop_current_pattern = True
                    time.sleep_ms(50)  # Brief delay to ensure pattern stops
                
                # Execute the requested mode
                if command == 0:  # OFF
                    led_off()
                    
                elif command == 1:  # ON
                    led_on()
                    
                elif command == 2:  # Flash
                    pattern_active = True
                    stop_current_pattern = False
                    led_flash()
                    pattern_active = False
                    led_off()  # Ensure LED is off after pattern
                    
                elif command == 3:  # Pulse
                    pattern_active = True
                    stop_current_pattern = False
                    led_pulse()
                    pattern_active = False
                    led_off()  # Ensure LED is off after pattern
                    
                elif command == 4:  # SOS
                    pattern_active = True
                    stop_current_pattern = False
                    led_sos()
                    pattern_active = False
                    led_off()  # Ensure LED is off after pattern
                    
                elif command == 5:  # Heartbeat
                    pattern_active = True
                    stop_current_pattern = False
                    led_heartbeat()
                    pattern_active = False
                    led_off()  # Ensure LED is off after pattern

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

# Test the LED at startup with simple blink pattern
print("Testing basic LED functionality...")
for i in range(3):
    set_led(True)
    time.sleep_ms(200)
    set_led(False)
    time.sleep_ms(200)

print("LED test complete, BLE service is running")

# Main loop
while True:
    time.sleep_ms(100)