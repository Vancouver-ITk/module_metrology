# module_metrology_upload

GUIs for upload bow and metrology test data.

# Dependencies

Depends on the GUI library tkinter, numpy, itkdb and requests.
itkdb version must be newer than v0.4, this will affect ITkDB access. 

# Installation
Windows: 

To create a virtual environment to ensure correct package versions are installed, running the following commands: 
```
python -m venv venv 
venv\Scripts\activate
```
Then run the following command to install all requireed packages
```
pip install -r requirements.txt
```
To close virtual environment, if desired, run following command: 
```
deactivate
```

To reopen virtual environment, simply run (has be to be done before using upload script): 
```
venv\Scripts\activate
```

Linux: 
To create a virtual environment to ensure correct package versions are installed, running the following commands: 
```
python -m venv venv 
source .venv/bin/activate
```
Then run the following command to install all requireed packages
```
pip install -r requirements.txt
```
To close virtual environment, if desired, run following command: 
```
deactivate
```

To reopen virtual environment, simply run (has be to be done before using upload script): 
```
source .venv/bin/activate
```

# Edits

At the top of the script there are a few variables which may need to be edited for proper upload. These are all under the heading 

```
# Institute Specific Constants - MODIFY THESE!
INSTITUTE = 'TRIUMF'
INSTRUMENT = "Mitutoyo_CMM"
SITE_TYPE = 'EC'
...
```

# Running

To run the file, open a terminal and navigate to the folder containing this program and enter the following command:

Metrology:
Windows:
```
python module_metrology_upload.py 
```

Linux/MAC:
```
python3 module_metrology_upload.py
```

Bow:
Windows:
```
python module_bow_upload.py 
```

Linux/MAC:
```
python3 module_bow_upload.py
```

The GUI will pop up and request that you find a file, the run number and if problems have occured or not. Then, the file can be uploaded to the database by entering your DB credentials. Sequential uploads are allowed as data cache is cleared between searching for files.


# Other

There are two other scripts in this folder:

``module_bow_file_conversion.py`` and ``module_metrology_file_conversion.py``. These are for converting files from the TRIUMF CMM raw data file format to the format expected by the database.

Running them is similar to above except each needs more user entered parameters like the DB serial number and operator. Raw data files need to be converted to the DB standard format before upload. 

