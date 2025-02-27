from decimal import *

from bs4 import BeautifulSoup
from PyPDFForm import PdfWrapper
import dearpygui.dearpygui as UI
UI.create_context()

data = {}
vars = { # Global variables for entire script
    'total_distance': "0",
    'previous_rem_fuel': "0",
}

def extract_navlog(input_string): # takes in a string (html of page) and returns a list of all waypoints and corresponding data
    extracted = []

    page = BeautifulSoup(input_string, 'html.parser')
    table = page.find('table', class_="waypoint mt-10 show-borders text-centered condensed no-wrap")
    
    # loop through all the containers, stop when a container has a child: class='sub-header' (this is the start of the alternate table)
    for container in table.find_all('tbody',  class_ = 'dont-break-container'):
        if container.find('tr', class_= "sub-header"): break # stop looping at the end of the table

        data_row = container.find('tr', class_= "table-data-row")

        if data_row:
            if data_row.span: data_row.span.string = ""
            row = []
            for info in data_row.stripped_strings:
                row.append(info)
            
            extracted.append(row)

    # also extract final reserve, alternate and block fuel from the header
    vars['final_res_fuel'] = page.find('td', class_="performance-metric reserve-fuel").span.string.split(" ")[0]
    vars['alt_fuel'] = page.find('td', class_="performance-metric alternate-fuel").span.string.split(" ")[0] 
    vars['block_fuel'] = page.find('td', class_="performance-metric block-fuel").span.string.split(" ")[0]
    # set previous rem fuel to block fuel
    vars['previous_rem_fuel'] = vars['block_fuel']

    vars["cruise_altitude"] = page.find(string="Altitude").find_next_sibling()
    #print(table.find_all(string='Profile'))
    #print(table.find_all(string='Fuel Flow'))

    return extracted

def insert_data(data_row, wpt_index, page_index): # inserts row of waypoint data into the data dict
    # waypoint name
    data["page" + str(page_index)]["waypoint" + str(wpt_index + 1)] = data_row[0]

    # wind vector and speed
    wind_dir, wind_spd = data_row[6].split("/")
    data["page" + str(page_index)]["wind_dir" + str(wpt_index)] = wind_dir
    data["page" + str(page_index)]["wind_spd" + str(wpt_index)] = wind_spd

    # Course and Heading
    wca_int = int(data_row[2]) - int(data_row[3])
    if wca_int < -180: wca_int += 360
    elif wca_int > 180: wca_int -= 360
    wca = "0" 
    if wca_int < 0: wca = str(wca_int)
    else: wca = "+" + str(wca_int)
    data["page" + str(page_index)]["mag_track" + str(wpt_index)] = data_row[3]
    data["page" + str(page_index)]["mag_hdg" + str(wpt_index)] = data_row[2]
    data["page" + str(page_index)]["wca" + str(wpt_index)] = wca

    # TAS and GS
    data["page" + str(page_index)]["spd_tas" + str(wpt_index)] = data_row[8]
    data["page" + str(page_index)]["spd_gs" + str(wpt_index)] = data_row[9]

    # Leg distance and Total distance
    vars["total_distance"] = str(int(data_row[10]) + int(vars["total_distance"]))
    data["page" + str(page_index)]["dist_leg" + str(wpt_index)] = data_row[10]
    data["page" + str(page_index)]["dist_tot" + str(wpt_index)] = vars["total_distance"]

    # Leg time and Total time
    data["page" + str(page_index)]["time_ete" + str(wpt_index)] = data_row[14]
    data["page" + str(page_index)]["time_tot" + str(wpt_index)] = data_row[16]

    # Leg Fuel and Remaining Fuel
    fuel_rem = data_row[13]
    leg_fuel = str(Decimal(vars["previous_rem_fuel"]) - Decimal(fuel_rem))
    vars["previous_rem_fuel"] = fuel_rem
    data["page" + str(page_index)]["fuel_leg" + str(wpt_index)] = leg_fuel
    data["page" + str(page_index)]["fuel_rem" + str(wpt_index)] = fuel_rem

    # Create UI input text boxes
    UI.add_input_text(uppercase=True, tag="waypoint::"+str(page_index)+"_"+str(wpt_index + 1), default_value=data_row[0], parent="Waypoint Group")

    with UI.group(horizontal=True, tag="info"+str(page_index)+"_"+str(wpt_index), parent="Altitudes Group"):
        UI.add_input_text(tag="alt::"+str(page_index)+"_"+str(wpt_index), parent="info"+str(page_index)+"_"+str(wpt_index))
        UI.add_input_text(tag="ma::"+str(page_index)+"_"+str(wpt_index), parent="info"+str(page_index)+"_"+str(wpt_index))

def remove_toc_tod(data_table): # loop through the data table to remove -TOC-, -TOD-
    new_table = []

    for i, row in enumerate(data_table):
        if row[0] == "-TOC-" or row[0] == "-TOD-":
            data_table[i+1][10] = str(int(data_table[i][10]) + int(data_table[i+1][10])) # Distance
            data_table[i+1][12] = str(Decimal(data_table[i][12]) + Decimal(data_table[i+1][12])) # Fuel

            cur_hrs, cur_min = data_table[i][14].split(":")
            next_hrs, next_min = data_table[i+1][14].split(":")
            new_hrs = int(cur_hrs) + int(next_hrs)
            new_min = int(cur_min) + int(next_min)
            if new_min > 60: new_min -= 60; new_hrs += 1
            new_min = "0" + str(new_min) if new_min < 10 else str(new_min)
            data_table[i+1][14] = str(new_hrs) + ":" + new_min # Time
        else:
            new_table.append(row)
    
    return new_table

def sort_data(data_table): # takes the raw data from extract_navlog and turns it into sorted data for edit & input into the OFP  
    first_waypoint = data_table[0][0]
    waypoint_index = 0
    page_index = 0

    UI.add_input_text(tag="waypoint::"+str(page_index)+"_"+str(waypoint_index + 1), default_value=first_waypoint, parent="Waypoint Group")
    
    for data_row in data_table:
        if waypoint_index == 0: # Start a new page and add the first waypoint
            data["page" + str(page_index)] = {}
            data["page" + str(page_index)]["waypoint1"] = first_waypoint
            waypoint_index += 1
            continue
        
        insert_data(data_row, waypoint_index, page_index)

        if waypoint_index == 15: #last waypoint on the page
            first_waypoint = data_row[0] # Set first waypoint for next page to current waypoint
            page_index += 1
            waypoint_index = 0
            continue

        waypoint_index += 1

    return data

# ------------------------- UI Functions -------------------------

def extract_button_pressed():
    try:
        # Data Extraction
        input_string = UI.get_value("input_string")

        raw_data = extract_navlog(input_string)
        if UI.get_value("remove_toc_tod"): raw_data = remove_toc_tod(raw_data) # Only remove TOC and TOD if it is selected

        global data
        data = sort_data(raw_data)

    except:
        print("An error occurred whilst trying to extract the navlog.")

    else:
        # Lock Input Fields
        UI.disable_item("input_string")
        UI.disable_item("full_stop_checkbox")
        UI.enable_item("export")

        UI.show_item("Input Window")

def reset_button_pressed():
    # Reset variables
    for i, v in enumerate(vars):
        vars[v] = None
    vars['total_distance'] = '0'
    vars['previous_rem_fuel'] = '0'

    for i, v in enumerate(data):
        data[v] = None

    # Enable Input Fields
    UI.enable_item("input_string")
    UI.set_value("input_string", "")

    UI.enable_item("full_stop_checkbox")
    UI.disable_item("export")

    UI.hide_item("Input Window")

    # Delete input fields
    for item in UI.get_item_children("Waypoint Group")[1]:
        if UI.get_item_type(item) == UI.get_item_type("input_string"):
            UI.delete_item(item)
    for row in UI.get_item_children("Altitudes Group")[1]:
        if UI.get_item_type(row) == UI.get_item_type("Altitudes Group") and UI.get_item_alias(row) != "ignore_delete":
            for item in UI.get_item_children(row)[1]:
                UI.delete_item(item)
            UI.delete_item(row)

def export_button_pressed():
    # Take the variables from the input boxes and add them to the data dict
    # Export the file as PDF
    global data

    # Loop through all waypoint text boxes and transfer their value to the data dict
    for item in UI.get_item_children("Waypoint Group")[1]:
        raw_key = UI.get_item_alias(item)
        value = UI.get_value(item)
        
        page_index, wpt_index = raw_key.split("::")[1].split("_")
        data["page" + page_index]["waypoint" + wpt_index] = value

        # Make the last waypoint the first one on the next page
        if int(wpt_index) == 16 and data["page" + str(int(page_index)+1)] != None:
            data["page" + str(int(page_index)+1)]["waypoint1"] = value

    # Loop through all altitude values and add them to data dict
    for row in UI.get_item_children("Altitudes Group")[1]:
        for item in UI.get_item_children(row)[1]:
            raw_key = UI.get_item_alias(item)
            value = UI.get_value(item)

            key, indecies = raw_key.split("::")
            page_index, wpt_index = indecies.split("_")
            data["page" + page_index][key + wpt_index] = value

    
    # Save file as PDF
    pages: PdfWrapper
    for page in data:
        try: pages += PdfWrapper("OFP_Template.pdf").pages[0].fill(data[page])
        except: pages = PdfWrapper("OFP_Template.pdf").pages[0].fill(data[page])
    
    with open("output/OFP.pdf", "wb+") as output:
        output.write(pages.read())
    
    print("Export Sucessfull")


UI.create_viewport(title="OFP Program", width=1080, height=600, resizable=False)
with UI.window(no_background=True, tag="Primary Window"):
    with UI.group(horizontal=True):
        with UI.child_window(width=300, tag="Control Window"):
            UI.add_spacer(height=10)

            UI.add_input_text(hint="Navlog Input", tag="input_string")
            UI.add_checkbox(label="[WIP] Start new page after full stop", tag="full_stop_checkbox")
            UI.add_checkbox(label="Remove TOC & TOD", tag="remove_toc_tod", default_value=True)

            with UI.group(horizontal=True, tag="Extract Reset"):
                UI.add_button(label="Extract", callback=extract_button_pressed)
                UI.add_button(label="Reset", callback=reset_button_pressed)
            
            UI.add_spacer(height=50)
            UI.add_button(label="Export as PDF", tag="export", callback=export_button_pressed)
        
        with UI.child_window(width=740, tag="Input Window"):
            with UI.group(horizontal=True):
                
                with UI.group():
                    with UI.group(horizontal=True):
                        with UI.group(width=100, tag="Waypoint Group"): # Waypoint Names
                            UI.add_text(default_value="Waypoint")
                        with UI.group(width=50, tag="Altitudes Group"): # Altitudes & Min Altitudes
                            UI.add_spacer(height=7)
                            with UI.group(horizontal=True, tag="ignore_delete"):
                                UI.add_text(default_value="Alt    ")
                                UI.add_text(default_value="Min Alt")

                UI.add_spacer(width=5)

                with UI.group():
                    with UI.group(horizontal=True):
                        UI.add_input_text(width=300, height=130, multiline=True, hint="Notes and Clearance", tag="Notes and Clearance")
                        UI.add_input_text(width=160, height=130, uppercase=True, hint="Transition Altitude", tag="transition_altitude")

                    UI.add_spacer(height=5)

                    with UI.group(horizontal=True):
                        with UI.group():
                            UI.add_text(default_value="Frequencies")
                            with UI.group(horizontal=True): # Dep Airport
                                UI.add_input_text(width=40, hint="DEP")
                                UI.add_input_text(width=60, hint="TWR")
                                UI.add_input_text(width=60, hint="ATIS")
                                UI.add_input_text(width=60, hint="GROUND")
                            
                            with UI.group(horizontal=True): # Arr Airport
                                UI.add_input_text(width=40, hint="ARR")
                                UI.add_input_text(width=60, hint="TWR")
                                UI.add_input_text(width=60, hint="ATIS")
                                UI.add_input_text(width=60, hint="GROUND")

                            with UI.group(horizontal=True): # Alt Airport
                                UI.add_input_text(width=40, hint="ALT")
                                UI.add_input_text(width=60, hint="TWR")
                                UI.add_input_text(width=60, hint="ATIS")
                                UI.add_input_text(width=60, hint="GROUND")

                        UI.add_spacer(width=5)

                        with UI.group():
                            UI.add_text(default_value="Enroute Frequencies")
                            with UI.group(horizontal=True):
                                UI.add_input_text(width=110, uppercase=True, hint="Station 1")
                                UI.add_input_text(width=80, hint="Frequency 1")
                            with UI.group(horizontal=True):
                                UI.add_input_text(width=110, uppercase=True, hint="Station 2")
                                UI.add_input_text(width=80, hint="Frequency 2")
                            with UI.group(horizontal=True):
                                UI.add_input_text(width=110, uppercase=True, hint="Station 3")
                                UI.add_input_text(width=80, hint="Frequency 3")
            
UI.hide_item("Input Window")

UI.setup_dearpygui()
UI.show_viewport()
UI.set_primary_window("Primary Window", True)
UI.start_dearpygui()
UI.destroy_context()


# Data flow:
# 0. User Presses the "Extract" button. Lock changing of settings, to prevent headace and issues. Allow the user to reset using another button in case they wish to change settings ✓
# 1. Extract from input string ✓
# 2. Parse and sort data ✓
# 3. Create corresponding input fields ✓
# 4. Update data table with variables from the text fields ✓
# 5. Export data to PDF ✓


#------------------TODO-----------------------
#  Implement min remaining fuel
#  Implement misc page info
#  Fix UI layout
#  Ask confirmation before reset
#  Add status message (display errors, import + export messages)
#  Add logic to not override previous exported OFP's
#  Indicate when input is disabled (maybe use UI.set_item_type_disabled_theme()? )
#  Detect when Full stop, Create new page from there on out
#  Automatically select FF for cruising altitude (Cruise altitude can be found bottom of Foreflight navlog)

#  --optional--
#  Make min Altitude box automatically calculate minimum altitude from heighest obstacle input
#  Create Presets for the Frequencies (Select ENCN and load all ENCN frequencies)
#  Create a toggle for each waypoint to ignore in OFP
#  M&B, Fuel, Performance, WX minima side

#-----------------ISSUES----------------------


#------------REQUIRES TESTING-----------------
# Reset button