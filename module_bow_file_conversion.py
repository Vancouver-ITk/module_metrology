import csv
import re
import module_metrology as mm
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib.ticker import LinearLocator

X_LIMIT = 0.1 #mm
Y_LIMIT = 0.3 #mm
INSTITUTE = 'SFU'
INSTRUMENT = "Smartscope Flash 302"
PATH_TO_DATA = 'module_metrology_data/'
PATH_TO_POSITION_FILES = 'metrology_position_files/'
SITE_TYPE = 'EC'
PROGRAM_VERSION = 'Vancouver_LocalScript_June2025'
X = 0
Y = 1
Z = 2
ENTRY_X = 100
ENTRY_Y = 20
DATA_DICT = dict()

def clear_data():
    """Clears all data so one can start over"""
    DATA_DICT.clear()
    output_text.set('Please enter the database serial number, operator name and run number. Select the module type. '
    'Look for a data file using the \'Find File\' button to import data from an appropriate CSV.' 
    'If everything looks correct press \'Save Data\' to produce the standard file format.' )

def get_file_data():
    """Make the bow file in the standard file format"""
    
    if serial_number.get() == "" or run_num.get() == "" or module_box.curselection() == () :
        output_text.set('Please ensure all mandatory values have been entered and a data file has been choosen. Then try again.')
        return 

    try:
        file = filedialog.askopenfilename(title = 'Select Data File')
        data_dict = mm.read_cmm_file(file)
        data_dict = mm.tilt_correction(data_dict)
        date = mm.get_date(file)

        module_type = module_box.get(module_box.curselection()[0])

    except:
        output_text.set("Error in processing file. Likely an invalid file type.")
        return

    DATA_DICT['DATE'] = date
    DATA_DICT['MODULE_TYPE'] = module_type.split('_')[0]
    DATA_DICT['SENSOR'] = data_dict['Sensor']

    output_text.set("File found and data parsed. Can now save to standard file format.")


def save_data():
    """Saves a metrology data file in the standard file format"""

    if DATA_DICT == {}:
        output_text.set("No data to upload. Please look for a valid data file and try again.")
        return

    # Determine the data file to write to.
    module_ref = serial_number.get()
    run_number = run_num.get()
    module_type = module_box.get(module_box.curselection()[0])
    file_prefix = module_ref + "_" + module_type + '_MODULE_BOW_'
    path_to_save = PATH_TO_DATA + 'bow_data/'
    full_path = mm.get_file_output(file_prefix, path_to_save, int(run_number))
    
    #Open the data file and write to it.
    file = open(full_path,'w+')
    file.write('#---Header\n')
    file.write('EC or Barrel: ' + SITE_TYPE + '\n')
    file.write('Module type: ' + DATA_DICT['MODULE_TYPE'] + '\n')
    file.write('Module ref. Number: ' + module_ref + '\n')
    file.write('Date: ' + DATA_DICT['DATE'] + '\n')
    file.write('Institute: ' + INSTITUTE + '\n')
    file.write('Operator: ' + operator_display.get() + '\n')
    file.write('Instrument type: ' + INSTRUMENT + '\n')
    file.write('Run Number: ' + str(run_number) + '\n')
    file.write('Measurement program version: ' + PROGRAM_VERSION + '\n')
    file.write('#---Bow\n')
    file.write('#Location X[mm] Y[mm] Z[mm]\n')
    for point in DATA_DICT['SENSOR'] :
        file.write(f'Sensor {point[X]:0.4f} {point[Y]:0.4f} {point[Z]:0.4f}\n')
    file.close()
    output_text.set('Output saved to ' + full_path)

    sensor_x, sensor_y, sensor_z = [],[],[]

    # produce plot of bow data 
    for point in DATA_DICT['SENSOR']:
        sensor_x.append(point[X])
        sensor_y.append(point[Y])
        sensor_z.append(point[Z])
    # convert to numpy arrays
    sensor_x = np.array(sensor_x)
    sensor_y = np.array(sensor_y)
    sensor_z = np.array(sensor_z)
    
    print(sensor_x)
    print(sensor_y)
    print(sensor_z)
        
    fig = plt.figure(figsize=(12,14))
    ax = plt.axes(projection='3d')
    # ax.scatter(sensor_x, sensor_y, sensor_z, c='blue', marker='o', s=50) 
    ax.plot_trisurf(sensor_x, sensor_y, sensor_z, vmin=sensor_z.min() * 2, cmap=cm.YlGnBu)
    plt.title(module_ref)
    ax.set_xlabel('[mm]')
    ax.set_ylabel('[mm]')
    ax.set_zlabel('[mm]')
    fig.tight_layout()
    fig.savefig(path_to_save + 'bow_plots/' + module_ref)
    # fig.colorbar(surf, shrink=0.5, aspect=5)   
    # plt.show()

# GUI Definition
root = tk.Tk()
frame = tk.Frame(root, height = 450, width = 500)
frame.pack()

#Define String Variables of GUI
serial_number = tk.StringVar()
operator_display = tk.StringVar()

run_num = tk.StringVar()
output_text = tk.StringVar()

#Define the boxes to dontain the string variables.
title = tk.Label(frame, text = 'Module Bow CMM Parsing GUI', font = ('calibri', 18))
title.place(x = 115, y = 10 )

save_button = tk.Button(frame, text = "Save Data", command = lambda: save_data())
save_button.place(x = ENTRY_X + 115, y = ENTRY_Y + 360)

browser_button = tk.Button(frame, text = "Find File", command = lambda: get_file_data())
browser_button.place(x = ENTRY_X + 300, y = ENTRY_Y + 40)

clear_button = tk.Button(frame, text = "Clear Data", command = lambda: clear_data())
clear_button.place(x = ENTRY_X + 300, y = ENTRY_Y + 100)

module_label = tk.Label(frame, text='Sensor Type')
module_label.place(x = ENTRY_X + 90, y = ENTRY_Y + 80)
module_box = tk.Listbox(frame, width = 10, relief = 'groove', height = '9')
module_box.place(x = ENTRY_X + 170, y = ENTRY_Y + 80)
module_box.insert(0,"M0")
module_box.insert(1,"M1")
module_box.insert(2,"M2")
module_box.insert(3,"3R")
module_box.insert(4,"3L")
module_box.insert(5,"4R")
module_box.insert(6,"4L")
module_box.insert(7,"5R")
module_box.insert(8,"5L")

id_label = tk.Label(frame, text='SN')
id_label.place(x = ENTRY_X - 70, y = ENTRY_Y + 40)
id_box = tk.Entry(frame, textvariable = serial_number, justify = 'left' , width = 20)
id_box.place(x = ENTRY_X - 50 , y = ENTRY_Y + 40)

run_num_label = tk.Label(frame, text='Run Number')
run_num_label.place(x = ENTRY_X - 60, y = ENTRY_Y + 80)
run_num_box = tk.Entry(frame, textvariable = run_num, justify = 'left' , width = 5)
run_num_box.place(x = ENTRY_X + 15 , y = ENTRY_Y + 80)

operator_label = tk.Label(frame, text='Operator')
operator_label.place(x = ENTRY_X + 80, y = ENTRY_Y + 40)
operator_box = tk.Entry(frame, textvariable = operator_display, justify = 'left', width = 20)
operator_box.place(x = ENTRY_X + 135, y = ENTRY_Y + 40)

output_text_box = tk.Message(frame, textvariable = output_text, font = ('calibri', 10), width = 344, relief = 'sunken', justify = 'left')
output_text_box.place(x = ENTRY_X - 30, y = ENTRY_Y + 250)
output_text.set('Please enter the database serial number, operator name and run number. Select the module type. '
'Look for a data file using the \'Find File\' button to import data from an appropriate CSV.' 
'If everything looks correct press \'Save Data\' to produce the standard file format.' )


root.mainloop()