import badger2040
import math
from badger2040 import WIDTH
from badger2040 import HEIGHT

##########################################################################################
# Display Setup
##########################################################################################

display = badger2040.Badger2040()
display.led(128)
display.set_update_speed(2)

##########################################################################################
# Define function that reads CSV files, with up to three variables specified in the columns
##########################################################################################

def read_csv(filename, x_name, y_name=None, z_name=None):
    data = {
        x_name: []
    }
    
    if y_name:
        data[y_name] = []
    if z_name:
        data[z_name] = []
    # respect the double quote rule about CSV file
    def split_line_respecting_quotes(line):
        parts = []
        temp = ""
        inside_quotes = False

        for char in line:
            if char == '"':
                inside_quotes = not inside_quotes
            elif char == ',' and not inside_quotes:
                parts.append(temp.strip())
                temp = ""
            else:
                temp += char
        if temp:  # Append the last field
            parts.append(temp.strip())

        return parts

    with open(filename, 'r') as file:
        lines = file.readlines()
        headers = split_line_respecting_quotes(lines.pop(0).strip())

        if x_name not in headers:
            raise ValueError(f"{x_name} column not found in the CSV file.")
        x_index = headers.index(x_name)

        y_index = headers.index(y_name) if y_name and y_name in headers else None
        z_index = headers.index(z_name) if z_name and z_name in headers else None

        for line_num, line in enumerate(lines, start=2):  # Starting from 2 because we removed the header
            values = split_line_respecting_quotes(line.strip())
            
            if len(values) <= x_index:
                print(f"Warning: Line {line_num} has incomplete data: {line}")
                continue

            try:
                data[x_name].append(float(values[x_index].replace('"', '')) if values[x_index] != "" else None)
            except ValueError:
                print(f"Error at line {line_num}: Cannot convert {values[x_index]} to float for {x_name}")
                data[x_name].append(None)

            if y_name and len(values) > y_index:
                try:
                    data[y_name].append(float(values[y_index].replace('"', '')) if values[y_index] != "" else None)
                except ValueError:
                    print(f"Error at line {line_num}: Cannot convert {values[y_index]} to float for {y_name}")
                    data[y_name].append(None)

            if z_name and len(values) > z_index:
                try:
                    data[z_name].append(float(values[z_index].replace('"', '')) if values[z_index] != "" else None)
                except ValueError:
                    print(f"Error at line {line_num}: Cannot convert {values[z_index]} to float for {z_name}")
                    data[z_name].append(None)
                
    return data





##########################################################################################
# Define a function that bins numerical data according to your specified number of bins
##########################################################################################
def bin_data(values, bin_count=100):
    min_val = min(v for v in values if v is not None)
    max_val = max(v for v in values if v is not None)
    bin_size = (max_val - min_val) / (bin_count - 1)  # adjust bin_size for one less bin_count

    # Function to determine which bin a value belongs to
    def find_bin(value):
        if value is None:
            return None
        return 1 + int((value - min_val) / bin_size)

    binned_values = [find_bin(value) for value in values]

    # Making sure no value is greater than bin_count
    binned_values = [None if value is None else min(bin_count, value) for value in binned_values]

    return binned_values


##########################################################################################
# Define a function that clears the screen and prints a header row
##########################################################################################
def clear():
    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    display.set_font("bitmap8")
    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, 10)
    display.set_pen(15)
    display.text("Badger charts", 10, 1, WIDTH, 0.6) # parameters are left padding, top padding, width of screen area, font size
    display.set_pen(0)
 
##########################################################################################
# Define a function that draws a heatmap
# This bins x and y in to a user specified number of groups
# Then prints the data as z (pen colour), also binned in to up to 15 levels
# Print colour is always as dark as possible
#
##########################################################################################

def plot_heatmap_binned(filename, x_name, y_name, z_name,AXIS_THICKNESS = 3,TICK_SPACING = 10,TICK_LENGTH = 5,x_offset = 30,y_offset = -10,rect_size_x = 4,rect_size_y = 4,x_bins_number = 50,y_bins_number = 30,z_bins_number = 10, skip = 5):
    csv_data = read_csv(filename, x_name, y_name, z_name)

    x = csv_data[x_name]
    y = csv_data[y_name]
    z = csv_data[z_name]

    binned_x = [x_val * rect_size_x for x_val in bin_data(x, x_bins_number)]
    binned_y = [y_val * rect_size_y for y_val in bin_data(y, y_bins_number)]
    binned_z = bin_data(z, z_bins_number)

    # Dictionaries to store the sum of z values and count of data points
    z_sums = {}
    counts = {}

    # Iterate and aggregate
    for x_val, y_val, z_val in zip(binned_x, binned_y, z):
        if None not in (x_val, y_val, z_val):  
            if (x_val, y_val) in z_sums:
                z_sums[(x_val, y_val)] += z_val
                counts[(x_val, y_val)] += 1
            else:
                z_sums[(x_val, y_val)] = z_val
                counts[(x_val, y_val)] = 1

    # Calculate average z values
    avg_z = {}
    for key, value in z_sums.items():
        avg_z[key] = value / counts[key]

    filtered_data = [(x_val, y_val, z_val) for x_val, y_val, z_val in zip(binned_x, binned_y, binned_z) if None not in (x_val, y_val, z_val)]

    x_origin = min(binned_x)
    y_origin = HEIGHT - min(binned_y)

    x_endpoint = max(binned_x)
    y_endpoint = HEIGHT - max(binned_y)

    display.line(x_origin + x_offset, y_origin + y_offset, x_endpoint + x_offset, y_origin + y_offset, AXIS_THICKNESS)
    display.line(x_origin + x_offset, y_origin + y_offset, x_origin + x_offset, y_endpoint + y_offset, AXIS_THICKNESS)
    
    for i in range(0, int((x_endpoint - x_origin) / TICK_SPACING) + 1):
        if i % skip == 0:
            x_pos = x_origin + (i * TICK_SPACING)
            display.line(x_pos + x_offset, y_origin + y_offset + (AXIS_THICKNESS*2), x_pos + x_offset, y_origin - TICK_LENGTH + y_offset + (AXIS_THICKNESS*2), 1)
            display.text(str(i), x_pos + x_offset, y_origin + y_offset + TICK_LENGTH + 5, 1, 1)

    y_axis_length = abs(y_origin - y_endpoint)
    num_ticks = y_axis_length // TICK_SPACING

    for i in range(num_ticks + 1):
        if i % skip == 0:
            y_tick_pos = y_origin - (i * TICK_SPACING)
            flipped_y = y_tick_pos + y_offset
            display.line(x_origin + x_offset, flipped_y, x_origin + x_offset - TICK_LENGTH, flipped_y, 1)
            display.text(str(i), x_origin + x_offset - TICK_LENGTH - 20, flipped_y, 1, 1)

    for (x_val, y_val), z_val in avg_z.items():
        display.set_pen(int(round(15 - z_val)))
        flipped_y = HEIGHT - y_val - rect_size_y
        display.rectangle(x_val + x_offset, flipped_y + y_offset, rect_size_x, rect_size_y)
    
        # Draw legend
    max_z = max([z for (_, _, z) in filtered_data])
    min_z = min([z for (_, _, z) in filtered_data])
    
    legend_steps = 5  # For example, you can adjust this
    legend_width = 20  # Width of the legend box
    legend_height = 10  # Height of each step in the legend
    
    legend_x_start = x_endpoint + x_offset + 40  # Position legend a bit to the right of the heatmap
    legend_y_start = y_origin + y_offset - 10  # Just above the x-axis
    
    for step in range(legend_steps):
        z_val = min_z + (max_z - min_z) * (step / (legend_steps - 1))
        display.set_pen(int(round(15 - z_val)))
        y_pos = legend_y_start - step * legend_height
        display.rectangle(legend_x_start, y_pos, legend_width, legend_height)
        display.set_pen(0)     
        display.text(str(round(z_val, 2)), legend_x_start + legend_width + 5, y_pos, 1, 1)
  

##########################################################################################
# Define a function that draws a heatmap
# This just draws the raw values of x and y, albeit rounded to the nearest integer
# Then prints the data as z (pen colour), also binned in to up to 15 levels
# Print colour is always as dark as possible
#
# Note that this is probably only useful when you have a single data point for each value of x and y
# Otherwise you'll be printing boxes over boxes
##########################################################################################    
def plot_heatmap_rounded(filename, x_name, y_name, z_name, AXIS_THICKNESS=3, TICK_SPACING=10, TICK_LENGTH=5, x_offset=30, y_offset=-10, rect_size_x=4, rect_size_y=4, z_bins_number=10, skip=5):
    csv_data = read_csv(filename, x_name, y_name, z_name)

    x = csv_data[x_name]
    y = csv_data[y_name]
    z = csv_data[z_name]
    
    for val in x:
        if val is not None and (math.isnan(val) or math.isinf(val)):
            print("Found problematic X:", val)

    for val in y:
        if val is not None and (math.isnan(val) or math.isinf(val)):
            print("Found problematic Y:", val)
    print("Unique types in x:", {type(val) for val in x})
    print("Unique types in y:", {type(val) for val in y})

    def safe_round(val):
        try:
            return int(round(val))
        except TypeError as e:
            print(f"Error when processing value {val} of type {type(val)}. Error: {e}")
            return None
    
    rounded_x = [safe_round(x_val) for x_val in x]
    rounded_y = [safe_round(y_val) for y_val in y]
    # Round x and y values to the nearest integer
    rounded_x = [int(round(x_val)) if x_val is not None and not (math.isnan(x_val) or math.isinf(x_val)) else None for x_val in x]
    rounded_y = [int(round(y_val)) if y_val is not None and not (math.isnan(y_val) or math.isinf(y_val)) else None for y_val in y]
    binned_z = bin_data(z, z_bins_number)

    scaled_rounded_x = [x_val * rect_size_x for x_val in rounded_x]
    scaled_rounded_y = [y_val * rect_size_y for y_val in rounded_y]

    # Filter out rows with None values
    filtered_data = [(x_val, y_val, z_val) for x_val, y_val, z_val in zip(scaled_rounded_x, scaled_rounded_y, binned_z) if None not in (x_val, y_val, z_val)]
   
    print(filtered_data)
    # Get the highest value of x and the lowest value of y from the binned data for origins
    x_origin = min(scaled_rounded_x)
    y_origin = HEIGHT - min(scaled_rounded_y)  # using HEIGHT to flip the y-axis

    # For the endpoints:
    x_endpoint = max(scaled_rounded_x)
    y_endpoint = HEIGHT - max(scaled_rounded_y)  # This will be the bottom of the screen

    # When drawing the X and Y axes:
    display.line(x_origin + x_offset, y_origin + y_offset, x_endpoint + x_offset, y_origin + y_offset, AXIS_THICKNESS)
    display.line(x_origin + x_offset, y_origin + y_offset, x_origin + x_offset, y_endpoint + y_offset, AXIS_THICKNESS)

    # Add ticks and labels for x-axis
    for i in range(0, int((x_endpoint - x_origin) / TICK_SPACING) + 1):
        if i % skip == 0:
            x_pos = x_origin + (i * TICK_SPACING)
            display.line(x_pos + x_offset, y_origin + y_offset + (AXIS_THICKNESS*2), x_pos + x_offset, y_origin - TICK_LENGTH + y_offset + (AXIS_THICKNESS*2), 1)
            display.text(str(i), x_pos + x_offset, y_origin + y_offset + TICK_LENGTH + 5, 1, 1)  # Adjust the +5 for desired spacing

    y_axis_length = abs(y_origin - y_endpoint)
    num_ticks = y_axis_length // TICK_SPACING

    # Add ticks and labels for y-axis
    for i in range(num_ticks + 1):
        if i % skip == 0:
            y_tick_pos = y_origin - (i * TICK_SPACING)
            flipped_y = y_tick_pos + y_offset
            display.line(x_origin + x_offset, flipped_y, x_origin + x_offset - TICK_LENGTH, flipped_y, 1)
            display.text(str(i), x_origin + x_offset - TICK_LENGTH - 20, flipped_y, 1, 1)  # Adjust the -20 for desired spacing

    # Loop through each filtered row of data
    for x_val, y_val, z_val in filtered_data:
        display.set_pen((15 - z_val))
        flipped_y = HEIGHT - y_val - rect_size_y
        display.rectangle(x_val + x_offset, flipped_y + y_offset, rect_size_x, rect_size_y)    
        # Get the highest and lowest values of z for the legend
    max_z = max([z for (_, _, z) in filtered_data])
    min_z = min([z for (_, _, z) in filtered_data])
    
 
    # Define legend properties
    legend_steps = 5
    legend_width = 20  
    legend_height = 10  
    
    # Position the legend a bit to the right of the heatmap
    legend_x_start = x_endpoint + x_offset + 40  
    legend_y_start = y_origin + y_offset - 10  # Position it just above the x-axis

    z_range = max(z) - min(z)
    z_step = z_range / z_bins_number
    z_thresholds = [min(z) + z_step * i for i in range(z_bins_number + 1)]

    # Draw the legend
    for step in range(legend_steps):
        z_val = step if step < len(z_thresholds) else z_bins_number - 1  # Use the binned values
        threshold_val = z_thresholds[step] if step < len(z_thresholds) else z_thresholds[-1]  # Actual threshold value

        display_val = int(round(15 - z_val))
        display.set_pen(display_val)

        y_pos = legend_y_start - step * legend_height
        display.rectangle(legend_x_start, y_pos, legend_width, legend_height)
        display.set_pen(0)
        display.text(str(round(threshold_val, 2)), legend_x_start + legend_width + 5, y_pos, 1, 1)

def plot_barchart(filename, x_name, AXIS_THICKNESS=3, TICK_LENGTH=5, x_offset=30, y_offset=-10, rect_size_x=4, rect_size_y=4, x_bins_number=50, skip=1):
    csv_data = read_csv(filename, x_name)
    x = csv_data[x_name]
    
    x_bins = bin_data(x, x_bins_number)

    counts = {}
    for x_bin in x_bins:
        if x_bin is not None:
            counts[x_bin] = counts.get(x_bin, 0) + 1

    filtered_data = [(x_bin * rect_size_x, count) for x_bin, count in counts.items()]

    x_origin = 0
    y_origin = HEIGHT
    x_endpoint = x_bins_number * rect_size_x
    max_count = max(counts.values())
    y_endpoint = HEIGHT - (max_count * rect_size_y)

    display.line(x_origin + x_offset, y_origin + y_offset, x_endpoint + x_offset, y_origin + y_offset, AXIS_THICKNESS)
    display.line(x_origin + x_offset, y_origin + y_offset, x_origin + x_offset, y_endpoint + y_offset, AXIS_THICKNESS)

    # X-axis ticks and labels
    for index, (x_val, _) in enumerate(filtered_data):
        display.line(x_val + x_offset, y_origin + y_offset + (AXIS_THICKNESS*2), x_val + x_offset, y_origin - TICK_LENGTH + y_offset + (AXIS_THICKNESS*2), 1)
    
        # Only print the label if the index is divisible by skip (starting from 0)
        if index % skip == 0:
            display.text(str(x_val//rect_size_x), x_val + x_offset, y_origin + y_offset + TICK_LENGTH + 5,1,1) # Adjust the +5 for desired spacing

    y_axis_length = abs(y_origin - y_endpoint)

    # Y-axis ticks and labels based on integer count values
    for i in range(0, max_count + 1):
        if i % skip == 0:  # Only draw if the current index i is divisible by skip
            y_tick_pos = y_origin - (i * rect_size_y)
            flipped_y = y_tick_pos + y_offset
            display.line(x_origin + x_offset, flipped_y, x_origin + x_offset - TICK_LENGTH, flipped_y, 1)
            # Adding Y value as text label to the left of tick mark
            display.text(str(i), x_origin + x_offset - TICK_LENGTH - 20, flipped_y,1,1) # Adjust the -20 for desired spacing

    for x_val, count in filtered_data:
        print(f"x = {x_val}, count = {count}, xorigin = {x_val + x_offset}, yorigin = {y_origin + y_offset}, yend = {y_origin + y_offset - count *10}")
        display.set_pen(0)
        display.line(x_val + x_offset, y_origin + y_offset, x_val + x_offset, y_origin + y_offset - (count * rect_size_y), AXIS_THICKNESS)
#display.update()





clear()

plot_barchart('data2.csv',
                     x_name='x',
                     AXIS_THICKNESS=3,
                     TICK_LENGTH=5,
                     x_offset=50,
                     y_offset=-50,
                     rect_size_x=4,
                     rect_size_y=4,
                     skip=5
                )

display.update()

clear()

plot_heatmap_binned('data2.csv',
             x_name='x',
             y_name='y',
             z_name='z',
             AXIS_THICKNESS = 3,
             TICK_SPACING = 10,
             TICK_LENGTH = 5,
             x_offset = 20,
             y_offset = -10,
             rect_size_x = 9,
             rect_size_y = 9,
             x_bins_number = 10,
             y_bins_number = 10,
             z_bins_number = 10,
             skip=1)

display.update()

clear()

plot_heatmap_rounded('data.csv',
                     x_name='x',
                     y_name='y',
                     z_name='z',
                     AXIS_THICKNESS=3,
                     TICK_SPACING=10,
                     TICK_LENGTH=5,
                     x_offset=20,
                     y_offset=-10,
                     rect_size_x=9,
                     rect_size_y=9,
                     z_bins_number=10,
                     skip=2)
display.update()

