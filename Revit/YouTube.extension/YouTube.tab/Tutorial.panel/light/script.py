import urllib2
import json
import time

# REPLACE THIS WITH YOUR PICO'S IP ADDRESS
PICO_IP = "192.168.50.163" 
BASE_URL = "http://{}".format(PICO_IP)

# --- YOUR SETTINGS ---
# Concentrated White
DEFAULT_COLOR = "E6F3FF"
DEFAULT_BRIGHTNESS = 70
# Revit Brand Blue (Approximate)
REVIT_BLUE = "0050BB" 
# Your Default White
DEFAULT_WHITE = "E6F3FF"
# ---------------------

def send_command(endpoint):
    """Sends a GET request to the Pico."""
    try:
        url = "{}{}".format(BASE_URL, endpoint)
        # Set a short timeout so Revit doesn't freeze if lamp is offline
        response = urllib2.urlopen(url, timeout=1) 
        return response.read()
    except Exception as e:
        print("Failed to connect to lamp: {}".format(e))
        return None

def set_lamp(color_hex, brightness=100):
    """
    Sets color and brightness.
    color_hex: String like "FF0000" (Red)
    brightness: Int 0-100
    """
    # Clean the hash if present
    color_hex = color_hex.replace("#", "")
    
    # Construct the API URL based on your main.py handle_api logic
    query = "/api/set?c={}&b={}".format(color_hex, brightness)
    send_command(query)

def set_mode(mode_name):
    """
    Sets mode to 'static' or 'rainbow'
    """
    query = "/api/mode?name={}".format(mode_name)
    send_command(query)

def flash_lamp(color_hex, duration=1.0):
    """
    Flashes the lamp for 'duration' seconds.
    """
    color_hex = color_hex.replace("#", "")
    # /api/flash?c=FF0000&t=1.0
    query = "/api/flash?c={}&t={}".format(color_hex, duration)
    send_command(query)

def turn_off():
    send_command("/api/off")

def animate_lamp(mode, color_start, color_end, duration_sec):
    """
    mode: 'linear' (Start->End) or 'pulse' (Start->End->Start)
    """
    c1 = color_start.replace("#", "")
    c2 = color_end.replace("#", "")
    
    # URL: /api/animate?m=pulse&c1=E6F3FF&c2=0050BB&t=3.0
    query = "/api/animate?m={}&c1={}&c2={}&t={}".format(mode, c1, c2, duration_sec)
    send_command(query)

def set_rainbow(duration_sec=None):
    """
    Sets rainbow mode.
    If duration_sec is set (e.g. 5.0), it returns to Default White after that time.
    If duration_sec is None, it runs forever.
    """
    if duration_sec:
        # /api/mode?name=rainbow&t=5.0
        query = "/api/mode?name=rainbow&t={}".format(duration_sec)
    else:
        # /api/mode?name=rainbow
        query = "/api/mode?name=rainbow"
    
    send_command(query)

def reset_to_default():
    """Restores the lamp to Concentrated White."""
    set_lamp(DEFAULT_COLOR, DEFAULT_BRIGHTNESS)

# ==========================================
# EXAMPLE USAGE INSIDE REVIT
# ==========================================

# Example 1: Turn Red (Error/Warning State)
#set_lamp("FF0000", 100)

# Example 2: Turn Cool White (Focus Mode)
#set_lamp("FFFFFF", 80)

# Example 3: Rainbow Mode (Success/Party)
# set_mode("rainbow")

#flash_lamp("0000FF", 3)

# 1. THE REVIT STARTUP EFFECT
# Transitions from White -> Blue -> White over 3 seconds
#animate_lamp("pulse", DEFAULT_WHITE, REVIT_BLUE, 1.0)

# 2. SHUTDOWN EFFECT (Linear)
# Fades from White -> Off (Black) over 2 seconds
# animate_lamp("linear", DEFAULT_WHITE, "000000", 2.0)

# 3. RAINBOW BREATHING
set_rainbow(4.0)
