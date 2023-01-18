# Lake Murten Temperature Chain

## Project Information

This is a pilot project from Eawag on behalf of the Swiss Federal Office for the Environment (FOEN) in view of a Swiss monitoring network for lake temperature. Eawag tests several measurement stations from 2021 to 2024.
Contact: Fabian Bärenbold (fabian.baerenbold@eawag.ch), Damien Bouffard (damien.bouffard@eawag.ch) and Martin Schmid (martin.schmid@eawag.ch).

## Sensors

The 24-node temperature chain from RBR measures the temperature at a 1 m depth resolution between 1 and 17 m and at 20, 25, 30, 35, 40 and 45 m.
Initial accuracy is 0.005 °C, typical stability is < 0.002 °C/yr and the time constant is ~30 seconds (https://rbr-global.com/products/standard-loggers/thermistor-strings/).

## Installation

- Clone the repository to your local machine using the command: 

 `git clone https://renkulab.io/gitlab/eawag-surf/lake-murten-monitoring.git`
 
 Note that the repository will be copied to your current working directory.

- Use Python 3 and install the requirements with:

 `pip install -r requirements.txt`

 The python version can be checked by running the command `python --version`. In case python is not installed or only an older version of it, it is recommend to install python through the anaconda distribution which can be downloaded [here](https://www.anaconda.com/products/individual). 

## Usage

### Process new data

In order to process new data locally on your machine the file path needs to be adapted to your local file system. The following steps are therefore necessary: 

- Edit the `scripts/input_batch.bat` file. Change all the directory paths to match your local file system. This file contains all the file paths necessary to launch the batch scripts `runfile.bat`.

- Edit the `scripts/input_python.py` file. Change all the directory paths to match your local file system. This file contains all the directories where the python script outputs data to.

To process new data, place the data in the input directory which you specified in the `scripts/input_batch.bat` file. 
Double-clicking on the `runfile.bat` file will automaticall process all the data in the input directory and store the output 
in the directories specified in the `scripts/input_python.py` file. Note that the input files need to have the same 
directory structure as the already existing files in the `data/Level0` folder. 

### Adapt/Extend data processing piepeline

The python script `scripts/main.py` defines the different processing steps while the python script `scripts/temperaturechain.py` contains the python class TemperatureChain with all the corresponding 
class methods to process the data. To add a new processing or visualization step, a new class method can be created in the `temperaturechain.py` file and the step can be added in `main.py` file.
Both above mentioned python scripts are independent of the local file system.

## Data

The data can be found in the folder `data`. The data is structured as follows:

### Data Structure

- **Level 0**: Raw data collected from the different sensors.

- **Level 1**: Raw data stored to NetCDF file where attributes (such as sensors used, units, description of data, etc.) are added to the data. Column with quality flags are added to the Level 1A data. Quality flag "1" indicates that the data point didn't pass the 
quality checks and further investigation is needed, quality flag "0" indicates that no further investiagion is needed.

- **Level 2**: The data from all the different depth levels is transformed into a temporal grid with a temporal spacing of 10 minutes and stored to a 
NetCDF file spanning over a time period of 10 days.

## Quality assurance

Quality checks include but are not limited to range validation, gradient check, data type checking and flagging missing data.
