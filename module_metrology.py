import numpy as np
import matplotlib.pyplot as plt
import csv
from scipy.linalg import lstsq
import math
import os
import re
from datetime import datetime

X_LIMIT = 0.1 #mm
Y_LIMIT = 0.3 #mm
PATH_TO_DATA = 'C:/Users/Graham Greig/Desktop/Sensor Probing/module_metrology/'
PATH_TO_POSITION_FILES = 'C:/Users/Graham Greig/Desktop/Sensor Probing/module_metrology/metrology_position_files'
FLEX_THICKNESS = 0.270 #um (Endcap)
GLUE_RANGE = (0.80, 0.160) #um
X = 0
Y = 1
Z = 2

def read_cmm_file(filename):
    """Reads a CMM file and returns a dictionary of lists of data points"""
    with open(filename) as csv_file:
        data = csv.reader(csv_file)
        data = list(data)
    data_dictionary = {}
    temp_list = []
    for row in data[1:]:
        if len(row) == 4 :
            name, element, value = row[1:4]
        else :
            name, feature_id, element, value = row[1:5]
        name = name.upper()
        if re.search("_[A-Z]$", name) :
            name = name[0:-2]
        if "SENSOR" in name or "SHIELD" in name:
            name = name.capitalize()
        if 'Sensor' in name :
            name = 'Sensor'
        if 'Y' in element :
            temp_list.append(-(float(value))) #Y needs to be flipped for the desired co-ordinate system.
        elif 'Z' in element:
            temp_list.append(float(value))
            temp_entry = data_dictionary.get(name, [])
            temp_entry.append(temp_list)
            data_dictionary[name] = temp_entry
            temp_list = []
        else:
            temp_list.append(float(value))
    print(data_dictionary)
    return data_dictionary

def get_date(filename):
    """Gets the date of a file in ISO8601 format"""
    creation_time = os.path.getctime(filename) 
    creation_time = datetime.utcfromtimestamp(creation_time)
    return creation_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

def tilt_correction(data_dictionary):
    """Correct the tilt of the data using the vacuumed down surface of the sensor as the Z=0 plane.
    Perfroms a least squares regression fit to the data cloud and subtracts the normal distance to 
    to the plane from each data point to correct for tilt."""
    sensor_data = data_dictionary.get('Sensor')
    temp_xy = []
    temp_z = []
    for row in sensor_data:
        temp_xy.append([row[X], row[Y], 1])
        temp_z.append(row[Z])
    z = np.matrix(temp_z).T
    xy = np.matrix(temp_xy)
    
    c = (xy.T * xy).I * xy.T * z
    for point_lists in data_dictionary.values():
        for point in point_lists:
            point[Z] = float(-(c[X]*point[X] + c[Y]*point[Y] - point[Z] + c[Z]) / np.sqrt(c[X]**2 + c[Y]**2 + 1))
    return data_dictionary

def plot_data(data_dictionary, key):
    """Produces a 3D plot of the data point cloud for the key of interest.
       Also plots plane of best fit for sensor data."""
    data = np.array(data_dictionary.get(key))
    x = data[:,X]
    y = data[:,Y]
    z = data[:,Z]
    ax = plt.axes(projection='3d')
    ax.scatter3D(x, y, z)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    if key == "Sensor":
        xx, yy = np.meshgrid([min(x),max(x)],[min(y),max(y)])
        A = np.c_[x, y, np.ones(len(z))]
        C, _, _, _ = lstsq(A, z)
        z_pred = C[0]*xx + C[1]*yy + C[2]
        ax.plot_surface(xx, yy, z_pred, rstride=1, cstride=1, alpha=0.2)
    plt.show()


def get_data_array(data_dictionary, key):
    """returns an array of x,y,z data for easy processing for the given key"""
    return np.array(data_dictionary.get(key))

    
def get_file_output(file_prefix, path_to_save, run_number):
    """Determines the name of the file path and file path by searching if previous files have been saved.
    Returns the file name and the full path to the file."""
    file_name = file_prefix + f"{run_number:03d}.dat"
    full_path = path_to_save + file_name
    return full_path

