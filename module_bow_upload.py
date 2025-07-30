"""This module is used to convert the data file to the raw data file for upload to the database."""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
import math
import itkdb
import os
import module_metrology as mm
import tkinter as tk
from tkinter import filedialog
from tkinter.constants import DISABLED, NORMAL
from tkinter import END

# Institute Specific Constants - MODIFY THESE!
INSTITUTE = 'SFU'
INSTRUMENT = "Smartscope Flash 302"
SITE_TYPE = 'EC'

# Program Constants - Do not modify 
PATH_TO_DATA = 'module_metrology_data/bow_data/'
PROGRAM_VERSION = 'July2025'
BOW_RANGE = (-50, 150) #um
X = 0
Y = 1
Z = 2
ENTRY_X = 100
ENTRY_Y = 20
DATA_DICT = dict()

def round(number, decimal=2):
    """Truncates a float to a value given by decimal. Default is 2 decimal places."""
    factor = 10.0 ** decimal
    return math.trunc(number * factor)/ factor

def print_format(data):
    """Formats for printing"""
    output = ""
    if type(data) == dict:
        for key, values in data.items():
            output += str(key) + ": " + str(values) + "\n"
    else:
        output = str(data)
    return output

def get_bow_results(lines):
    """"Computes the bow of the module"""
    results = dict()
    index = 12

    # Correct for tilt
    raw_data_dict = dict()
    for line in lines[index:] :
        name, x, y ,z = line.split()
        temp_list = raw_data_dict.get(name, [])
        temp_list.append([float(x),float(y),float(z)])
        raw_data_dict[name] = temp_list
    data_dict = mm.tilt_correction(raw_data_dict)

    # Determine the concavity
    sensor_data = np.array(data_dict.get('Sensor'))
    x = sensor_data[:,X]
    y = sensor_data[:,Y]
    z = sensor_data[:,Z]

    mid_y = np.max(y)/2
    mid_x = np.max(x)/2

    min_index = 0
    max_index = 0
    min_value = 10000
    max_value = -10000
    for i in range(0,len(z)):
        if z[i] > max_value:
            max_value = z[i]
            max_index = i
        if z[i] < min_value:
            min_value = z[i]
            min_index = i
    

    d_max_value = math.sqrt((x[max_index] - mid_x)**2 + (y[max_index] - mid_y)**2)
    d_min_value = math.sqrt((x[min_index] - mid_x)**2 + (y[min_index] - mid_y)**2)

    #Concave Down
    if d_max_value < d_min_value :
        bow = (min_value - max_value)*1000
    else:
        bow = (max_value - min_value)*1000
        
    results["BOW"] = round(bow)

    if BOW_RANGE[0] < bow < BOW_RANGE[1]:
        DATA_DICT['passed'] = True
        output_text.set("Bow passed! Press save to upload to database.")
    else:
        DATA_DICT['passed'] = False
        output_text.set("Bow failed. Press save if you wish to upload.")

    return results

def get_file_data():
    """Get the data from a file using the search function and format it into the standard JSON dictionary."""
    # Clear everything (except the password) so that we can upload multiple files.
    DATA_DICT.clear()
    id_box.configure(state=NORMAL)
    run_num_box.configure(state=NORMAL)
    operator_box.configure(state=NORMAL)
    bow_box.configure(state=NORMAL)
    id_box.delete('1.0', END)
    run_num_box.delete('1.0', END)
    operator_box.delete('1.0', END)
    bow_box.delete('1.0', END)
    id_box.configure(state=DISABLED)
    run_num_box.configure(state=DISABLED)
    operator_box.configure(state=DISABLED)
    bow_box.configure(state=DISABLED)

    file = filedialog.askopenfilename(initialdir = PATH_TO_DATA, title = 'Select Data File')
    
    # Get the data from the file
    with open(file) as data_file:
        lines = data_file.readlines()
    DATA_DICT["component"] = lines[3].split()[3]
    DATA_DICT["testType"] = "MODULE_BOW"
    # Added June 11 2025 - next 2 lines are for retroactive uploads
    DATA_DICT["stage"] = "GLUED"
    DATA_DICT["isRetroactive"] = True
    ###
    DATA_DICT["institution"] = lines[5].split()[1]
    DATA_DICT["runNumber"] = str(lines[8].split()[2])
    DATA_DICT["date"] = lines[4].split()[1]
    DATA_DICT["passed"] = ""
    DATA_DICT["problems"] = ""
    properties = dict()
    machine = lines[7].split()
    operator = lines[6].split()
    properties["JIG"] = ""
    properties["OPERATOR"] = " ".join(operator[1:])
    properties["USED_SETUP"] = " ".join(machine[2:])
    properties["SCRIPT_VERSION"] = lines[9].split()[3] 
    DATA_DICT["properties"] = properties 
    DATA_DICT["results"] = get_bow_results(lines)
    DATA_DICT["results"]["FILE"] = file
    DATA_DICT["results"]["TEMPERATURE"] = ""
    
    # Update the output for the user.
    id_box.configure(state=NORMAL)
    run_num_box.configure(state=NORMAL)
    operator_box.configure(state=NORMAL)
    bow_box.configure(state=NORMAL)

    id_box.insert('1.0', DATA_DICT["component"])
    run_num_box.insert('1.0', DATA_DICT["runNumber"])
    operator_box.insert('1.0', DATA_DICT["properties"]["OPERATOR"])
    bow_box.insert('1.0', print_format(DATA_DICT["results"]["BOW"]))

    id_box.configure(state=DISABLED)
    run_num_box.configure(state=DISABLED)
    operator_box.configure(state=DISABLED)
    bow_box.configure(state=DISABLED)

def save_data():
    """Saves a metrology data file in the standard file format"""
    if problems_box.curselection() == () or DATA_DICT == {} or jig.get() == "" or retroactive_box.curselection() == ():
        output_text.set('Please ensure all mandatory values have been entered and a data file has been choosen. Then try again.')
        return 
    else:
        if problems_box.get(problems_box.curselection()[0]) == "Yes":
             DATA_DICT["problems"]  = True
        else: 
            DATA_DICT["problems"] = False
    
        if retroactive_box.get(retroactive_box.curselection()[0]) == "GLUED":
            DATA_DICT["isRetroactive"] = True
            DATA_DICT["stage"] = "GLUED"
        elif retroactive_box.get(retroactive_box.curselection()[0]) == "FINISHED":
            DATA_DICT["isRetroactive"] = True
            DATA_DICT["stage"] = "FINISHED"  
        elif retroactive_box.get(retroactive_box.curselection()[0]) == "STITCH-BONDING":
            DATA_DICT["isRetroactive"] = True
            DATA_DICT["stage"] = "STITCH_BONDING"        
        else: 
            DATA_DICT["isRetroactive"] = False 

    print(DATA_DICT)
    DATA_DICT['properties']['JIG'] = jig.get()
    DATA_DICT["results"]['TEMPERATURE'] = temperature.get()

    db_passcode_1 =  db_pass_1.get()
    db_passcode_2 =  db_pass_2.get()

    try :
        user = itkdb.core.User(accessCode1 = db_passcode_1, accessCode2 = db_passcode_2)
        client = itkdb.Client(user=user)
    except:
        output_text.set("Set passcodes are incorrect. Try again")
        return
    
    result= client.post("uploadTestRunResults", json = DATA_DICT)

    if (('uuAppErrorMap')=={}):
        output_text.set('Upload of Test and File Successful!')
    elif (('uuAppErrorMap'))[0]=='cern-itkpd-main/uploadTestRunResults/':
        output_text.set("Error in Test Upload.")
    elif list(('uuAppErrorMap'))[0]=='cern-itkpd-main/uploadTestRunResults/componentAtDifferentLocation':
        output_text.set('Component cannot be uploaded as is not currently at the given location')
    elif (('uuAppErrorMap'))[0]=='cern-itkpd-main/uploadTestRunResults/unassociatedStageWithTestType':
        output_text.set('Component cannot be uploaded as the current stage does not have this test type. You will need to update the stage of the component on the ITK DB. Note that due to a bug on the ITK DB, you might also get this error if the component is not at your current location.')
    elif (('uuAppErrorMap'))[0]!='cern-itkpd-main/uploadTestRunResults/':
        output_text.set("Upload of Test Successful!")
    else:
        output_text.set('Error!')
            
    #upload the raw data file
    if (('uuAppErrorMap')[0]!='cern-itkpd-main/uploadTestRunResults/'):
        ###Upload the attached file!
        testRun = result['testRun']['id']
        file_path = DATA_DICT['results']['FILE']
        file_name = os.path.basename(file_path)
        dataforuploadattachment={
                "testRun": testRun,
                "type": "file",
                "title": file_name, 
                "description": "Automatic Attachment of Original Data File", 
            }
        attachment = {'data': (file_name, open(file_path, 'rb'), 'text')}
        client.post("createTestRunAttachment", data = dataforuploadattachment, files = attachment)
        output_text.set("Upload of test and attachment completed.")
 

# GUI Definition
root = tk.Tk()
frame = tk.Frame(root, height = 450, width = 500)
frame.pack()

jig = tk.StringVar()
temperature = tk.StringVar()
output_text = tk.StringVar()

db_pass_1 = tk.StringVar()
db_pass_2 = tk.StringVar()

#Define the boxes to dontain the string variables.
title = tk.Label(frame, text = 'Module Bow Upload GUI', font = ('calibri', 18))
title.place(x = 115, y = 10 )

save_button = tk.Button(frame, text = "Save Data", command = lambda: save_data())
save_button.place(x = ENTRY_X + 110, y = ENTRY_Y + 275)

browser_button = tk.Button(frame, text = "Find File", command = lambda: get_file_data())
browser_button.place(x = ENTRY_X + 300, y = ENTRY_Y + 40)

problems_label = tk.Label(frame, text='Problems?')
problems_label.place(x = ENTRY_X + 60, y = ENTRY_Y + 120)
problems_box = tk.Listbox(frame, width = 4, relief = 'groove', height = '2', exportselection=0)
problems_box.place(x = ENTRY_X + 120, y = ENTRY_Y + 120)
problems_box.insert(0,"Yes")
problems_box.insert(1,"No")

retroactive_label = tk.Label(frame, text='Retroactive Upload?')
retroactive_label.place(x = ENTRY_X + 60, y = ENTRY_Y + 170)
retroactive_box = tk.Listbox(frame, width = 20, relief = 'groove', height = '4', exportselection=0)
retroactive_box.place(x = ENTRY_X + 60, y = ENTRY_Y + 190)
retroactive_box.insert(0,"No")
retroactive_box.insert(1,"GLUED")
retroactive_box.insert(2,"FINISHED")
retroactive_box.insert(2,"STITCH-BONDING")

id_label = tk.Label(frame, text='SN')
id_label.place(x = ENTRY_X - 70, y = ENTRY_Y + 40)
id_box = tk.Text(frame, font = ('calibri', 10), width = 15, height = 1,  relief = 'sunken', state=DISABLED)
id_box.place(x = ENTRY_X - 50 , y = ENTRY_Y + 40)

run_num_label = tk.Label(frame, text='Run Number')
run_num_label.place(x = ENTRY_X - 95, y = ENTRY_Y + 120)
run_num_box = tk.Text(frame, font = ('calibri', 10), width = 5, height = 1, relief = 'sunken', state=DISABLED)
run_num_box.place(x = ENTRY_X - 20 , y = ENTRY_Y + 120)

temp_num_label = tk.Label(frame, text='Temperature')
temp_num_label.place(x = ENTRY_X - 95, y = ENTRY_Y + 155)
temp_num_box = tk.Entry(frame, textvariable = temperature, justify = 'left' , width = 5)
temp_num_box.place(x = ENTRY_X - 20 , y = ENTRY_Y + 155)

operator_label = tk.Label(frame, text='Operator')
operator_label.place(x = ENTRY_X + 80, y = ENTRY_Y + 40)
operator_box = tk.Text(frame, font = ('calibri', 10), width = 15, height = 1, relief = 'sunken', state=DISABLED)
operator_box.place(x = ENTRY_X + 135, y = ENTRY_Y + 40)

bow_label = tk.Label(frame, text='Bow (um)')
bow_label.place(x = ENTRY_X - 95, y = ENTRY_Y + 80)
bow_box = tk.Text(frame, font = ('calibri', 10), width = 20, height = 1,  relief = 'sunken',state=DISABLED)
bow_box.place(x = ENTRY_X - 35 , y = ENTRY_Y + 80)

jig_label = tk.Label(frame, text='Jig Used')
jig_label.place(x = ENTRY_X + 120, y = ENTRY_Y + 80)
jig_box = tk.Entry(frame, textvariable = jig, justify = 'left' , width = 30)
jig_box.place(x = ENTRY_X + 170 , y = ENTRY_Y + 80)

db_pass_1_label = tk.Label(frame, text="AccessCode 1")
db_pass_1_label.place(x = ENTRY_X + 190, y = ENTRY_Y + 120)
db_pass_1_box = tk.Entry(frame, textvariable = db_pass_1, show='*', justify = 'left', width = 15)
db_pass_1_box.place(x = ENTRY_X + 270, y = ENTRY_Y + 120)

db_pass_2_label = tk.Label(frame, text="AccessCode 2")
db_pass_2_label.place(x = ENTRY_X + 190, y = ENTRY_Y + 150)
db_pass_2_box = tk.Entry(frame, textvariable = db_pass_2, show='*',  justify = 'left', width = 15)
db_pass_2_box.place(x = ENTRY_X + 270, y = ENTRY_Y + 150)

output_text_box = tk.Message(frame, textvariable = output_text, font = ('calibri', 10), width = 344, relief = 'sunken', justify = 'left')
output_text_box.place(x = ENTRY_X - 30, y = ENTRY_Y + 315)
output_text.set(' Look for a data file using the \'Find File\' button to import data from an appropriate data file.'
'Select \'Yes\' or \'No\' for if problems existed during testing and the jig used for the bow measurement.'
'If everything looks correct press \'Save Data\' to upload to the database.' )

root.mainloop()