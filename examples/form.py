# -----------------------------------------------------------------------------------------------
# form.py - Badger 2040 Form Engine
#
# Description:
#    This is a ODK-compatible form engine, written in python, for filling in ODK Build
#    forms on a Pimoroni Badger 2040/2040W device: https://shop.pimoroni.com/products/badger-2040
#
# Created June 13, 2023 by Dr. Gareth S. Bestor <xiphware@gmail.com>
# -----------------------------------------------------------------------------------------------

import time
import utime
import machine
import json
import qrcode
import ubinascii
import jpegdec
import os
import io
import random
import badger2040 # https://github.com/pimoroni/badger2040/blob/main/firmware/PIMORONI_BADGER2040/lib/badger2040.py
import badger_os #https://github.com/pimoroni/badger2040/blob/main/firmware/PIMORONI_BADGER2040/lib/badger_os.py
import sys
from pcf85063a import PCF85063A

# Set badger CPU speed - higher numbers are faster but draw more power
# 1-4. 4 is overclocking.

badger2040.system_speed(3)

print("starting form.py")

# The ODK Build form definition to load. * Must be an ODK Build json file, NOT an XForm xml or XLSForm xlsx! *
form = "/forms/Badger 2040 Test.odkbuild"

# The name and version ID of the ODK form on the Central server. This is the form that will ultimately receive the submission on Central
serverform = "Badger-2040-Test-Acquire"
versionid = "1688347654"

# The cvs file to write and accumulate saved form results
submissions = "/forms/submissions.csv"


# ------------------------------
# Clock
# ------------------------------
# Initialise the rtc
# Create PCF85063A RTC instance
i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))
rtc_pcf85063a = PCF85063A(i2c)
# Display PCF85063A's RTC : call time from pcf rtc using command rtc_pcf85063a.datetime()
print(f"PCF_RTC: {rtc_pcf85063a.datetime()}")
# ------------------------------
# Global Constants
# ------------------------------

WIDTH = badger2040.WIDTH # 296
HEIGHT = badger2040.HEIGHT # 128

FONT = "sans"
FONT_THICKNESS = 2

# Font size = HEIGHT/32
TITLE_HEIGHT = 24
TITLE_TEXT_SIZE = 0.7

OPTION_HEIGHT = 20
OPTION_TEXT_SIZE = 0.6

MENU_HEIGHT = 16
MENU_TEXT_SIZE = 0.5

TEXT_HEIGHT = 18
TEXT_SIZE = 0.6

CONTROL_HEIGHT = HEIGHT - MENU_HEIGHT - TITLE_HEIGHT

SCROLLBAR_WIDTH = 7 # odd width is better for dithering the inside

# x position of front A/B/C menu buttons
BUTTONA_X = WIDTH // 7
BUTTONB_X = WIDTH // 2
BUTTONC_X = WIDTH * 6 // 7

BLACK = 0
WHITE = 15
GREY = 12

CHARS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["SPACE", "DEL"]

MAX_MAGNITUDE = 100 # integer controls: x1, x10, x100

# ------------------------------
# Load Form Definition
# ------------------------------

print("loading '{}'".format(form))

formfile = open(form)
formdef = json.load(formfile)
formfile.close()

controls = formdef['controls']
metadata = formdef['metadata']

def print_form_info():
    print("Title:", formdef['title'])
    print("Version:", metadata['version'])
    print("URL:", metadata['submission_url'])
    
    for i, control in enumerate(controls):
        print("control #{}".format(i))
        print("    name:", control['name'])
        print("    type:", control['type'])
        print("    label:", control['label']['0'])
        
        if 'options' in control:
            options = control['options']
            opts = [option['text']['0'] for option in options]
            print("    options:", opts)
            vals = [option['val'] for option in options]
            print("    values:", vals)
                      
# ------------------------------
# State
# ------------------------------

state = {
    'at_start': True,
    'at_end': False,
    'current': 0,
    'saved': False,
    'selection': 0, # index of currently highlighted Select control option
    'magnitude': 1, # 1x, 10x, 100x for Integer control
    'char_index': 0, # index of currently selected Text control character; CHARS[0] = A
    'values': [],
    'timestamp': '',
    'button_A': None,
    'button_B': None,
    'button_C': None
}

badger_os.state_load("form", state)
print("initial state:", state)

# ------------------------------
# Button Actions
# ------------------------------

# Page navigation actions (hard refresh)

def start():
    global state
    global needs_refresh
    
    state['at_start'] = False
    if len(controls) > 0:
        state['at_end'] = False
    else:
        state['at_end'] = True # the form has no controls so jump to end!

    state['current'] = 0
    state['saved'] = False
    state['selection'] = 0
    state['magnitude'] = 1
    state['char_index'] = 0
    
    # Initialize all controls to their default value, if any
    state['values'] = list(map(lambda control: control['defaultValue'], controls))

    display.set_update_speed(badger2040.UPDATE_FAST)
    needs_refresh = True

def get_time():
    datetime_tuple = rtc_pcf85063a.datetime()
    return datetime_tuple

def format_time(datetime_tuple):
    year, month, day, hour, minute, second, weekday = datetime_tuple
    formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        year, month, day, hour, minute, second
    )
    return formatted_time

def save():
    global state
    global needs_refresh

    # Add a UUID that is compatible with ODK submissions to Central
    # Generate a random UUID
    uuid = '-'.join([''.join([random.choice('0123456789abcdef') for _ in range(8)]),
                    ''.join([random.choice('0123456789abcdef') for _ in range(4)]),
                    ''.join([random.choice('0123456789abcdef') for _ in range(4)]),
                    ''.join([random.choice('0123456789abcdef') for _ in range(4)]),
                    ''.join([random.choice('0123456789abcdef') for _ in range(12)])])

    # ISO8601 local time (no timezone!); see https://github.com/micropython/micropython/issues/3087
    # Badger 2040 doesn't have an RTC, so the time resets when wake up! So the timestamp is only meaningful when running from Thonny!
    state['timestamp']
    state['timestamp'] = get_time()
    state['timestamp'] = format_time(state['timestamp'])
    print("Current date and time:", state['timestamp'])
    # Append csv results to submissions file
    print("saving to '{}'".format(submissions))
    with open(submissions, "a") as f:
        f.write(f"uuid:{uuid},{csv()}\n")

    # Create individual XML file for the submission
    folder_name = "instances/"
    try:
        os.mkdir("instances")
    except OSError:
        pass  # The directory already exists

    try:
        os.mkdir(folder_name)
    except OSError:
        pass  # The directory already exists

    xml_filename = folder_name + f"/uuid{uuid}.xml"
    with open(xml_filename, "w") as xml_file:
        xml_file.write(
            f"<data xmlns:jr=\"http://openrosa.org/javarosa\" xmlns:orx=\"http://openrosa.org/xforms\" id=\"{serverform}\"  version=\"{versionid}\">\n")
        for i, control in enumerate(controls):
            name = control['name']
            value = state['values'][i]
            xml_file.write(f"  <{name}>{value}</{name}>\n")
        xml_file.write(f"  <timestamp>{state['timestamp']}</timestamp>\n")  # Add timestamp field
        deviceid = ubinascii.hexlify(machine.unique_id()).decode("utf-8")
        xml_file.write(f"  <device_id>{deviceid}</device_id>\n")  # Add device_id field
        xml_file.write(f"  <meta><instanceID>uuid:{uuid}</instanceID></meta>\n")  # Add device_id field
        xml_file.write("</data>")

    state['saved'] = True

    display.set_update_speed(badger2040.UPDATE_FAST)
    needs_refresh = True

def cancel():
    global state
    global needs_refresh
    
    state['at_start'] = True
    state['at_end'] = False
    state['values'] = []
    
    display.set_update_speed(badger2040.UPDATE_FAST)
    needs_refresh = True


def show_previous():
    global state
    global needs_refresh
    
    if state['at_start']:
        return
    elif state['at_end'] and not state['saved']:
        state['at_end'] = False
        state['current'] = len(controls) - 1
        state['selection'] = 0
        state['magnitude'] = 1
        state['char_index'] = 0
        display.set_update_speed(badger2040.UPDATE_FAST)
        needs_refresh = True
    elif state['current'] > 0:
        state['current'] -= 1
        state['selection'] = 0
        state['magnitude'] = 1
        state['char_index'] = 0
        display.set_update_speed(badger2040.UPDATE_FAST)
        needs_refresh = True
        

def show_next():
    global state
    global needs_refresh
    
    if state['at_start'] or state['at_end']:
        return
    
    current = state['current']
    value = state['values'][current]
    if value == '' and controls[current]['required']:
        return # disable Next if current control is required but unanswered
    
    if current < len(controls) - 1:
        state['current'] += 1
        state['selection'] = 0
        state['magnitude'] = 1
        state['char_index'] = 0
    elif current == len(controls) - 1:
        state['current'] = 0
        state['at_end'] = True
        
    display.set_update_speed(badger2040.UPDATE_FAST)
    needs_refresh = True   


# Integer control actions

def increment():
    global state
    global needs_refresh

    current = state['current']
    value = state['values'][current]

    min_value = controls[current]['range']['min']
    if min_value != '' and controls[current]['range']['minInclusive'] != True:
        min_value = str(int(min_value) + 1)
        
    max_value = controls[current]['range']['max']
    if max_value != '' and controls[current]['range']['maxInclusive'] != True:
        max_value = str(int(max_value) - 1)
    
    # if value not yet set then initialize to minimum, if applicable, otherwise 0
    if value == '':
        if min_value != '':
            state['values'][current] = min_value
        else:
            state['values'][current] = "0"
        needs_refresh = True   
    else:
        old = int(value)
        new = old + state['magnitude']
        if max_value != '':
            new = min(new, int(max_value)) # clip to maximum, if applicable
        if new != old:
            state['values'][current] = str(new)
            needs_refresh = True  

 
def decrement():
    global state
    global needs_refresh

    current = state['current']
    value = state['values'][current]

    min_value = controls[current]['range']['min']
    if min_value != '' and controls[current]['range']['minInclusive'] != True:
        min_value = str(int(min_value) + 1) # TODO: decimals?
    
    # if value not yet set then initialize to minimum, if applicable, otherwise 0
    if value == '':
        if min_value != '':
            state['values'][current] = min_value
        else:
            state['values'][current] = "0"
        needs_refresh = True   
    else:
        old = int(value)
        new = old - state['magnitude']
        if min_value != '':
            new = max(new, int(min_value)) # clip to minimum, if applicable
        if new != old:
            state['values'][current] = str(new)
            needs_refresh = True   


def change_magnitude():
    global state
    global needs_refresh

    state['magnitude'] *= 10
    if state['magnitude'] > MAX_MAGNITUDE:
        state['magnitude'] = 1
    needs_refresh = True   


# Select control actions

def next_option():
    global state
    global needs_refresh

    if state['selection'] < len(controls[state['current']]['options']) - 1:
        state['selection'] += 1
        needs_refresh = True   


def previous_option():
    global state
    global needs_refresh

    if state['selection'] > 0:
        state['selection'] -= 1
        needs_refresh = True   


def select_option():
    global state
    global needs_refresh

    current = state['current']
    control = controls[current]
    type = control['type']
    value = state['values'][current]

    val = control['options'][state['selection']]['val']
    if type == 'inputSelectOne':
        if val == value: 
            state['values'][current] = '' # value already selected, so clear it
        else:
            state['values'][current] = val
    else: # inputSelectMany
        if value == '':
            state['values'][current] = val
        else:
            values = value.split() # convert space separated select-multi value into array
            if val in values:
                state['values'][current] = ' '.join(list(filter(lambda v: v != val, values))) # value already selected, so remove it from list
            else:
                state['values'][current] = ' '.join(values + [val]) # append new value to existing selection        
    needs_refresh = True   


# Text control actions

def next_char():
    global state
    global needs_refresh

    if state['char_index'] < len(CHARS) - 1:
        state['char_index'] += 1
        needs_refresh = True   


def previous_char():
    global state
    global needs_refresh

    if state['char_index'] > 0:
        state['char_index'] -= 1
        needs_refresh = True   


def select_char():
    global state
    global needs_refresh
    
    current = state['current']
    value = state['values'][current]
    char = CHARS[state['char_index']]
    
    if char == 'DEL':
        if len(value) == 0:
            return
        elif len(value) == 1:
            state['values'][current] = ''
        else:
            state['values'][current] = value[0:len(value)-1]
    elif char == 'SPACE':
        state['values'][current] += ' '
    else:
        state['values'][current] += char
    needs_refresh = True     


# ------------------------------
# UI Components
# ------------------------------

def draw_asterisk(x, y):
    display.set_pen(BLACK)
    display.image(bytearray((
        0b10011001,
        0b11011011,
        0b11000011,
        0b00000000,
        0b11000011,
        0b11011011,
        0b10011001,
        0b11111111,
    )), 8, 8, x, y)


def draw_scrollbar(i, num):
    x = WIDTH - SCROLLBAR_WIDTH
    y = 0
    
    display.set_pen(BLACK)
    display.rectangle(x, y, WIDTH, HEIGHT)
    display.set_pen(GREY)
    display.rectangle(x+1, y+1, SCROLLBAR_WIDTH-2, HEIGHT-2)
    display.set_pen(BLACK)
    
    height = max(HEIGHT // num, 10)
    top = HEIGHT * i // num
    display.rectangle(x, top, SCROLLBAR_WIDTH, height)

    
def draw_menu(a, b, c):
    display.set_pen(BLACK)
    if state['at_start'] or state['at_end']:
        display.rectangle(0, HEIGHT - MENU_HEIGHT, WIDTH, HEIGHT)
    else:
        display.rectangle(0, HEIGHT - MENU_HEIGHT, WIDTH - SCROLLBAR_WIDTH - 2, HEIGHT) # leave RHS space for scrollbar
    display.set_pen(WHITE)

    y = HEIGHT - (MENU_HEIGHT // 2)
    max_width = WIDTH // 3
    if a is not None:
        display.text(a, BUTTONA_X - (display.measure_text(a, MENU_TEXT_SIZE) // 2), y, max_width, MENU_TEXT_SIZE)

    if b is not None:
        display.text(b, BUTTONB_X - (display.measure_text(b, MENU_TEXT_SIZE) // 2), y, max_width, MENU_TEXT_SIZE)
        
    if c is not None:
        display.text(c, BUTTONC_X - (display.measure_text(c, MENU_TEXT_SIZE) // 2), y, max_width, MENU_TEXT_SIZE)
    

def draw_options(options, selected, current, x, y, width, height, item_height, multiselect):
    # Determine maximum number of columns per page based on the longest option
    longest = max(map(lambda option: display.measure_text(option, OPTION_TEXT_SIZE), options))
    columns = width // (longest + item_height + 5) # text + checkbox + padding
    rows = height // item_height

    # Determine first option shown on the page containing the current option
    options_per_page = rows * columns
    start = (current // options_per_page) * options_per_page

    item_x = 0
    item_y = 0
    column = 0

    for i in range(start, len(options)):
        top = item_y + y - (item_height // 2)
        
        # Highlight current option
        if i == current:
            display.set_pen(GREY)
            display.rectangle(item_x, top, width // columns, item_height)
            
        display.set_pen(BLACK)
        display.text(options[i], item_x + x + item_height, item_y + y, WIDTH, OPTION_TEXT_SIZE)
        
        if multiselect:
            draw_check_box(item_x, top, item_height, selected[i], 2, 2)
        else:
            draw_radio_button(item_x, top, item_height, selected[i], 2, 2)
        
        # Check if wrap to next column
        item_y += item_height
        if item_y >= height - MENU_HEIGHT - (item_height // 2):
            item_x += width // columns
            item_y = 0
            column += 1
            if column >= columns:
                return
            
 
def draw_check_box(x, y, size, selected, padding, thickness):
    x0 = x + padding + (thickness // 2)
    w = size - thickness - (padding * 2)
    x1 = x0 + w
    y0 = y + padding + (thickness // 2)
    h = w
    y1 = y0 + h
    
    display.set_pen(WHITE)
    display.rectangle(x0, y0, w, h)
    display.set_pen(BLACK)
    display.line(x0, y0, x1, y0, thickness)
    display.line(x1, y0, x1, y1, thickness)
    display.line(x1, y1, x0, y1, thickness)
    display.line(x0, y1, x0, y0, thickness)

    if selected:
        display.line(x0, y0, x1, y1, thickness)
        display.line(x0, y1, x1, y0, thickness)
        

def draw_radio_button(x, y, size, selected, padding, thickness):
    centerx = x + size // 2
    centery = y + size // 2
    radius = (size - padding * 2) // 2
    
    display.set_pen(BLACK)
    display.circle(centerx, centery, radius)
    display.set_pen(WHITE)
    display.circle(centerx, centery, radius - thickness)
        
    if selected:
        display.set_pen(BLACK)
        display.circle(centerx, centery, radius - (thickness * 2))


def draw_pic_options(options, selected, current, x, y, width, height, pic_size):
    columns = 3
    padding = (width - (columns * pic_size)) // (columns + 1)
    start = max(current - 1, 0)
    item_x = padding
    column = 0

    if current == start:
        item_x += pic_size + padding
        column = 1

    for i in range(start, len(options)):
        display.set_pen(BLACK)

        # Line under current option
        if i == current:
            display.rectangle(item_x, y + pic_size + 6, pic_size, 2)     

        # Box around selected option(s)
        if selected[i]:
            display.rectangle(item_x - 3, y - 3, pic_size + 6, pic_size + 6)
            display.set_pen(WHITE)
            display.rectangle(item_x - 1, y - 1, pic_size + 2, pic_size + 2)

        jpeg.open_file("/icons/" + options[i]) # option label provides the icon filename
        jpeg.decode(item_x, y)
        
        # Next column
        item_x += pic_size + padding
        column += 1
        if column >= columns:
            return
        
# ------------------------------
# QR code
# ------------------------------

def csv():
    # https://docs.pycom.io/firmwareapi/pycom/machine/
    deviceid = ubinascii.hexlify(machine.unique_id()).decode("utf-8")

    values = [formdef['title'], str(metadata['version']), deviceid, state['timestamp']]
    values += state['values']
    return ','.join(values)
    
# Below QR functions copied verbatim from qrgen.py example!

def measure_qr_code(size, code):
    w, h = code.get_size()
    module_size = int(size / w)
    return module_size * w, module_size


def draw_qr_code(ox, oy, size, code):
    size, module_size = measure_qr_code(size, code)
    display.set_pen(WHITE)
    display.rectangle(ox, oy, size, size)
    
    display.set_pen(BLACK)
    for x in range(size):
        for y in range(size):
            if code.get_module(x, y):
                display.rectangle(ox + x * module_size, oy + y * module_size, module_size, module_size)

# ------------------------------
# Disk Usage
# ------------------------------

def map_value(input, in_min, in_max, out_min, out_max):
    return (((input - in_min) * (out_max - out_min)) / (in_max - in_min)) + out_min


def draw_progress_bar(percent, x, y, width, height):
    display.set_pen(BLACK)
    display.rectangle(x, y, width, height)
    display.set_pen(WHITE)
    display.rectangle(x+1, y+1, width-2, height-2)
    display.set_pen(BLACK)
    display.rectangle(x+2, y+2, int((width-4) * percent), height-4)
    

# ------------------------------
# Form Pages & Controls
# ------------------------------

def show_start_page():
    global state
    
    y = TITLE_HEIGHT // 2
    display.text(formdef['title'], 0, y, WIDTH, TITLE_TEXT_SIZE)
    y += TITLE_HEIGHT
    display.text("version " + str(metadata['version']), 0, y, WIDTH, OPTION_TEXT_SIZE)
    
    y += OPTION_HEIGHT * 2
    display.text(str(len(controls)) + " questions", 0, y, WIDTH, OPTION_TEXT_SIZE)
    
    total_required = len(list(filter(lambda control: control['required'], controls)))
    y += OPTION_HEIGHT
    display.text(str(total_required) + " mandatory", 0, y, WIDTH, OPTION_TEXT_SIZE)
    
    draw_menu(None, "Start", "Exit")
    state['button_A'] = None
    state['button_B'] = 'start'
    state['button_C'] = None

    # Show disk usage in menu bar; adapted from badger_os.get_disk_usage()
    f_bsize, f_frsize, f_blocks, f_bfree, _, _, _, _, _, _ = os.statvfs("/")
    f_total = f_frsize * f_blocks
    f_free = f_bsize * f_bfree
    f_used = f_total - f_free
    draw_progress_bar(f_used/f_total, 3, HEIGHT - MENU_HEIGHT + 2, 40, MENU_HEIGHT - 4)

    display.set_pen(WHITE)
    display.set_font("bitmap8")
    display.text("{}k free".format(int(f_free/1024)), 45 , HEIGHT - MENU_HEIGHT + 4, 50, 1)
    display.set_font(FONT)
    print("{} / {} bytes used, {} free".format(f_used, f_total, f_free))
    
    # TODO: show battery level; see https://github.com/pimoroni/pimoroni-pico/issues/334
    
 
def show_end_page():
    global state
    
    y = TITLE_HEIGHT // 2
    if state['saved']:
        display.text("Form saved!", 0, y, WIDTH, TITLE_TEXT_SIZE)
        
        # Show QR-code with csv
        code = qrcode.QRCode()
        code.set_text(csv())
        size, _ = measure_qr_code(HEIGHT, code)
        draw_qr_code(WIDTH - size, (HEIGHT - size) // 2, HEIGHT, code)
    
        datetime = state['timestamp'].split(' ')
        y += OPTION_HEIGHT * 2
        display.text(datetime[0], 0, y, WIDTH, OPTION_TEXT_SIZE)
        y += OPTION_HEIGHT
        display.text("@ " + datetime[1], 0, y, WIDTH, OPTION_TEXT_SIZE)

        state['button_A'] = 'cancel'
        state['button_B'] = 'cancel'
        state['button_C'] = 'cancel'
        
    else:
        #answered = len(list(filter(lambda control: len(str(control['value'])) > 0, controls)))
        answered = len(list(filter(lambda value: value != '', state['values'])))
        total_required = len(list(filter(lambda control: control['required'], controls)))
        
        #required = len(list(filter(lambda control: control['required'] and len(str(control['value'])) > 0, controls)))
        required = 0
        for i, control in enumerate(controls):
            if control['required'] and state['values'][i] != '':
                required += 1
        
        display.text("End of form", 0, y, WIDTH, TITLE_TEXT_SIZE)
        y += TITLE_HEIGHT * 2
        display.text("answered " + str(answered) + "/" + str(len(controls)), 0, y, WIDTH, OPTION_TEXT_SIZE)
        y += OPTION_HEIGHT
        display.text("mandatory " + str(required) + "/" + str(total_required), 0, y, WIDTH, OPTION_TEXT_SIZE)

        if required == total_required:
            draw_menu("Cancel", "Save", None)
            state['button_A'] = 'cancel'
            state['button_B'] = 'save'
            state['button_C'] = None
        else:
            draw_menu("Cancel", None, None)
            state['button_A'] = 'cancel'
            state['button_B'] = None
            state['button_C'] = None


def show_current_control():
    global state
    
    current = state['current']
    control = controls[current]
    type = control['type']
    label = control['label']['0']
    value = state['values'][current] # value of the current control
    
    width = WIDTH - SCROLLBAR_WIDTH - 2
    x = 0
    y = TITLE_HEIGHT // 2
    
    if control['required']: # asterisk icon to indicate required controls (sans font's asterisk looks lowsy...)
        x += 10
        draw_asterisk(0,y-4)
    
    display.text(label, x, y, width, TITLE_TEXT_SIZE)
    display.line(0, y + TITLE_HEIGHT // 2 - 1, width, y + TITLE_HEIGHT // 2 - 1)
    y += TITLE_HEIGHT

    if type == 'inputNumeric' and control['kind'] == 'Integer':
        display.text(value, WIDTH // 2 - (display.measure_text(value, TITLE_TEXT_SIZE) // 2), y + (CONTROL_HEIGHT - TITLE_HEIGHT) // 2, WIDTH, TITLE_TEXT_SIZE)
        
        draw_menu("-", "x"+str(state['magnitude']), "+")
        state['button_A'] = 'decrement'
        state['button_B'] = 'change_magnitude'
        state['button_C'] = 'increment'
        
    elif type == 'inputSelectOne' or type == 'inputSelectMany':
        options = [option['text']['0'] for option in control['options']]
        values = [option['val'] for option in control['options']]
        
        if type == 'inputSelectMany':
            # select-multi
            selected = list(map(lambda val: val in value.split(), values)) # convert space separated select-multi value into array to match against
            if control['appearance'] == 'Horizontal Layout': # option labels contain the icon filenames to display
                draw_pic_options(options, selected, state['selection'], 0, y, width + SCROLLBAR_WIDTH, CONTROL_HEIGHT, 64) # add SCROLLBAR_WIDTH to center middle icon over B button
            else:
                draw_options(options, selected, state['selection'], 0, y, width, CONTROL_HEIGHT, OPTION_HEIGHT, True)
        else:
            # select-one
            selected = list(map(lambda val: val == value, values)) # select-one only has one single value
            if control['appearance'] == 'Horizontal Layout': # option labels contain the icon filenames to display
                draw_pic_options(options, selected, state['selection'], 0, y, width + SCROLLBAR_WIDTH, CONTROL_HEIGHT, 64) # add SCROLLBAR_WIDTH to center middle icon over B button
            else:
                draw_options(options, selected, state['selection'], 0, y, width, CONTROL_HEIGHT, OPTION_HEIGHT, False)
        
        draw_menu("Prev", "Select", "Next")
        state['button_A'] = 'previous_option'
        state['button_B'] = 'select_option'
        state['button_C'] = 'next_option'
                
    elif type == 'inputText' and control['readOnly'] == False:
        display.text(value, WIDTH // 2 - (display.measure_text(value, TITLE_TEXT_SIZE) // 2), y + (CONTROL_HEIGHT - TITLE_HEIGHT) // 2, WIDTH, TITLE_TEXT_SIZE)
        
        draw_menu("<", CHARS[state['char_index']], ">")
        state['button_A'] = 'previous_char'
        state['button_B'] = 'select_char'
        state['button_C'] = 'next_char'

    #elif type == 'inputText' and control['readOnly'] == True: # TODO: note
    #elif type == 'inputNumeric' and control['kind'] == 'Decimal': # TODO: decimal

    draw_scrollbar(state['current'], len(controls))

# ------------------------------
#       Main
# ------------------------------

display = badger2040.Badger2040()
display.set_font(FONT)
display.set_thickness(FONT_THICKNESS)

jpeg = jpegdec.JPEG(display.display)

if badger2040.woken_by_button():
    # Dont hard refresh after waking because it negatively impacts perceived response time
    display.set_update_speed(badger2040.UPDATE_TURBO)
    needs_refresh = False
else:
    display.set_update_speed(badger2040.UPDATE_FAST)
    needs_refresh = True
    print_form_info()

while True:
    try:
        display.keepalive()

        if badger2040.woken_by_button() or display.pressed_any():
            if display.pressed(badger2040.BUTTON_UP):
                show_previous()
            elif display.pressed(badger2040.BUTTON_DOWN):
                show_next()

            # Handle button C press while show_start_page is running
            if state['at_start'] and display.pressed(badger2040.BUTTON_C):
                sys.exit()
                    
            if display.pressed(badger2040.BUTTON_DOWN):
                show_next()
            
            # https://stackoverflow.com/questions/3061/calling-a-function-of-a-module-by-using-its-name-a-string
            if display.pressed(badger2040.BUTTON_A):
                handler = state['button_A']
                if handler is not None:
                    locals()[handler]()
                
            if display.pressed(badger2040.BUTTON_B):
                handler = state['button_B']
                if handler is not None:
                    locals()[handler]()
                
            if display.pressed(badger2040.BUTTON_C):
                handler = state['button_C']
                if handler is not None:
                    locals()[handler]()
        

            
        badger2040.reset_pressed_to_wake()
        
        if needs_refresh:
            display.set_pen(WHITE)
            display.clear()
            display.set_pen(BLACK)
    
            if state['at_start']:
                show_start_page()
            elif state['at_end']:
                show_end_page()
            else:
                show_current_control()
                
        display.update()
        display.set_update_speed(badger2040.UPDATE_TURBO)

        badger_os.state_save("form", state)
        print("state:", state)
        needs_refresh = False
        
    
    # Halt if on battery to save power; we will wake up and resume from saved state if any of the front buttons are pressed
        display.halt()

    except SystemExit:
        # Catch the SystemExit exception and return to launcher.py
 #       badger2040.reset_pressed_to_wake()
        #badger_os.state_launch()
        print('killing app')
        badger_os.launch('launcher')


