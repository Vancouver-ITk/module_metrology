
import csv
import re
import module_metrology as mm
import tkinter as tk
from tkinter import filedialog


X_LIMIT = 0.1 #mm
Y_LIMIT = 0.3 #mm
INSTITUTE = 'SFU'
INSTRUMENT = "Smartscope Flash 302"
PATH_TO_DATA = 'module_metrology_data/'
PATH_TO_POSITION_FILES = 'metrology_position_files/'
SITE_TYPE = 'EC'
FLEX_THICKNESS = 0.270 #um (Endcap)
PROGRAM_VERSION = 'v1'
GLUE_RANGE = (0.80, 0.160) #um
X = 0
Y = 1
Z = 2
ENTRY_X = 100
ENTRY_Y = 20
DATA_DICT = dict()
HYBRID_GT_REGEX = '_R[0-5]H[0-1]_[0-9]+'
PB_GT_REGEX = 'PB_[0-5]'
SHIELD_REGEX = 'Shield'
CAP_REGEX = 'C[1-8]'

def clear_data():
    """Clears all data so one can start over"""
    DATA_DICT.clear()
    output_text.set('Please enter the database serial number, operator name and run number. Select the module type. '
    'Look for a data file using the \'Find File\' button to import data from an appropriate CSV.' 
    'If everything looks correct press \'Save Data\' to produce the standard file format.' )

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]

def sort_dict(dictionary):
    """Returns a sorted dictionary"""
    dict_keys = list(dictionary.keys())
    print(dict_keys)
    dict_keys.sort(key=natural_keys)
    print(dict_keys)
    sorted_dict = dict()
    for key in dict_keys:
        sorted_dict[key] = dictionary[key]
    return sorted_dict

def get_glue_thickness_dictionary(data_dictionary):
    """Generates the glue thickness dictionary.
    Module object can be either 'Power Board' or 'Hybrid' """
    glue_dict = dict()
    for key, values in data_dictionary.items():
        if re.search(HYBRID_GT_REGEX,key) :
            glue_dict[key] = values
    for key, values in data_dictionary.items():
        if re.search(PB_GT_REGEX,key) :
            glue_dict[key] = values
    print(glue_dict)
    return sort_dict(glue_dict)
    
def get_capacitor_heights(data_dictionary):
    """Gets a dictionary of capacitor heights"""
    cap_dict = dict()
    for key, value in data_dictionary.items():
        if re.search(CAP_REGEX,key) :      
            cap_dict[key] = value[0]
    return sort_dict(cap_dict)

def get_distance_dict(data_dictionary, module_type):
    """Determines the absolute distances in X and Y from the expected position
    for key points of interest"""
    filename = PATH_TO_POSITION_FILES + module_type + '_positions.csv'
    with open(filename, mode='r') as csv_file:
        reader = csv.reader(csv_file, delimiter = ',')
        data = list(reader)
        position_dict = dict()
        for row in data[1:]:
            point = data_dictionary.get(row[0],None)[0]
            if point != None:
                position_dict[row[0]] = [point[X],point[Y]]
    return sort_dict(position_dict)

def get_file_data():
    """Get the data from a file using the search function and format it into the standard JSON dictionary."""

    if serial_number.get() == "" or run_num.get() == "" or module_box.curselection() == () :
        output_text.set('Please ensure all mandatory values have been entered and a data file has been chosen. Then try again.')
        return 

    try:
        file = filedialog.askopenfilename(title = 'Select Data File')
        data_dict = mm.read_cmm_file(file)
        data_dict = mm.tilt_correction(data_dict)
        date = mm.get_date(file)

        module_type = module_box.get(module_box.curselection()[0])
        print("Data Collected")
        try:
            position_dict = get_distance_dict(data_dict, module_type)
        except:
            print("One or more fiducial locations are missing")
        print("Distances Parsed")
        cap_dict = get_capacitor_heights(data_dict)
        print("Capacitor Heights Collected")
        glue_dict = get_glue_thickness_dictionary(data_dict)
        print("Glue thicknesses data resolved.")
    except:
        output_text.set("Error in processing file. Likely an invalid file type or wrong module type.")
        return

    DATA_DICT['DATE'] = date
    DATA_DICT['MODULE_TYPE'] = module_type.split('_')[0]
    DATA_DICT['POSITIONS'] = position_dict
    DATA_DICT['GLUE_HEIGHTS'] = glue_dict
    DATA_DICT['CAP'] = cap_dict
    try:
        DATA_DICT["SHIELD"] = data_dict['Shield']
    except:
        print("There are no shieldbox points in raw data file")
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
    file_prefix = module_ref + "_" + module_type + '_MODULE_METROLOGY_'
    path_to_save = PATH_TO_DATA + 'metrology_data/'
    full_path = mm.get_file_output(file_prefix, path_to_save, int(run_number))
    print(DATA_DICT)
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
    file.write('#---Positions\n')
    file.write('#Location X[mm] Y[mm]\n')
    for key, point in DATA_DICT['POSITIONS'].items() :
        file.write(f'{key} {point[X]:0.4f} {point[Y]:0.4f}\n')
    file.write('#---Glue heights:\n')
    file.write('#Location Type X[mm] Y[mm] Z[mm]\n')
    for point in DATA_DICT['SENSOR']:
        file.write(f'Sensor\t1\t{point[X]:0.4f}\t{point[Y]:0.4f}\t{point[Z]:0.4f}\n')
    for key, points in DATA_DICT['GLUE_HEIGHTS'].items() :
        for point in points:
            file.write(f'{key}\t2\t{point[X]:0.4f}\t{point[Y]:0.4f}\t{point[Z]:0.4f}\n')
    if DATA_DICT['CAP'] != {} and DATA_DICT['SHIELD'] != {} :
        file.write('#---Other heights:\n')
        file.write('#Location\tType\tX[mm]\tY[mm]\tZ[mm]\n')
        for key, point in DATA_DICT['CAP'].items() :
            file.write(f'{key}\t4\t{point[X]:0.4f}\t{point[Y]:0.4f}\t{point[Z]:0.4f}\n')  
        for point in DATA_DICT['SHIELD'] :
            file.write(f'Shield\t4\t{point[X]:0.4f}\t{point[Y]:0.4f}\t{point[Z]:0.4f}\n') 
    file.close()    
    output_text.set('Output saved to ' + full_path)

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
title = tk.Label(frame, text = 'Module Metrology CMM Parsing GUI', font = ('calibri', 18))
title.place(x = 90, y = 10 )

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