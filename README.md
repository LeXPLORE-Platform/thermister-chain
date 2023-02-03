# LéXPLORE Thermister Chain


## Project Information / Abstract

[LéXPLORE](https://lexplore.info) is research platform on Lake Geneva for a broad range of limnological research. The platform results from a collaboration between five partner institutions ([Eawag](https://www.eawag.ch/en/), [EPFL](https://www.epfl.ch/en/), [INRAE](https://www6.lyon-grenoble.inrae.fr/carrtel/), [UNIGE](https://unige.ch), [UNIL](https://www.unil.ch/index.html)). The LéXPLORE platform is anchored since February 2019 at a position reaching 110 m depth off the lake's north-shore.
The data presented here is part of the core dataset maintained by the technical team of LéXPLORE.
The data is used and displayed on the [Datalakes website](https://www.datalakes-eawag.ch/). related data or products can be visualised and downloaded on the [Datalakes website](https://www.datalakes-eawag.ch/).


### References

Wüest, A., Bouffard, D., Guillard, J., Ibelings, B. W., Lavanchy, S., Perga, M. ‐E., & Pasche, N. (2021). LéXPLORE: a floating laboratory on Lake Geneva offering unique lake research opportunities. Wiley Interdisciplinary Reviews: Water, 8(5), e1544 (15 pp.). https://doi.org/10.1002/wat2.1544

See also the [360° virtual tour](https://www.eawag.ch/repository/lexplore/index.htm)

### Citation
Bouffard, D., Ballu, A., Cunillera, G., Fillion, R., Gios, M., Guillard, J., Ibelings, B., Lavanchy, S., Miesen, F., Pasche, N., Perga, M-E., Plüss, M., Quetin, P., Runnalls, J., Wüest, A. (2022). Data and products from LéXPLORE Therminster Chain, 2019 - 2023. DOI

DOI attribution pending.


### Time Frame
- Begin date: 19-06-2019
- End data: continuous data set - live

### Geographic coverage
Lake Geneva [46.50, 6.66]


## Sensors

The Temperature Chain measures the temperature at various depths at a 10 seconds resolution. The chain is located at the LéXPLORE platform (46°30’0.819″ N, 6°39’39.007″ E) 

### Thermistor Chain
- **Brand, Model & SN**: RBR, Concerto T24, 0.25 m to 18 m : SN 62944,  21 m to 90 m SN 62955 or SN 206659, see `sensor_history`
- **System integration**: Data logged into a cambell scientific CR6, loggernet for near realtime transmission 
- **Initial Accuracy**: ±0.005 °C
- **Setup** depth of the sensors(m): 0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 21, 24, 27, 30, 33, 36, 39 42, 45, 48, 51, 54, 57, 60, 63, 66, 69, 72, 75, 78, 81, 84, 87, 90, sampling period: 10 min


## Code

[![License: MIT][mit-by-shield]][mit-by]

**You need to have [git](https://git-scm.com/downloads) installed in order to successfully clone the repository.**

- Clone the repository to your local machine using the command: 

 `git clone https://renkulab.io/gitlab/lexplore/thermister-chain.git`
 
 Note that the repository will be copied to your current working directory.

- Use Python 3 and install the requirements with:

 `pip install -r requirements.txt`

 The python version can be checked by running the command `python --version`. In case python is not installed or only an older version of it, it is recommend to install python through the anaconda distribution which can be downloaded [here](https://www.anaconda.com/products/individual). 

## Usage

### Process new data

In order to process new data locally on your machine the file path needs to be adapted to your local file system. The following steps are therefore necessary: 

- Edit the `scripts/input_batch.bat` file. Change all the directory paths to match your local file system. This file contains all the file paths necessary to launch the batch scripts `runfile.bat`.

- Edit the `scripts/input_python.py` file. Change all the directory paths to match your local file system. This file contains all the directories where the python script outputs data to.

To process new data, place the data in the input directory which you specified in the `scripts/input_batch.bat` file. Double-clicking on the `runfile.bat` file will automaticall process all the data in the input directory and store the output in the directories specified in the `scripts/input_python.py` file.

### Adapt/Extend data processing piepeline

The python script `scripts/main.py` defines the different processing steps while the python script `scripts/intruments.py` contains the python classes for each iteration of the thermister chain with all the corresponding class methods to process the data. To add a new processing or visualization step, a new class method can be created in the `instruments.py` file and the step can be added in `main.py` file. Both above mentioned python scripts are independent of the local file system.

## Data

### Access

Data for this repository is stored in a remote object store. In order to work with the data you need 
to run `scripts/download_remote_data.py`, this will syncronise the local `data` folder with the remote 
data folder on the server. 

### License

[![CC BY 4.0][cc-by-shield]][cc-by] 

This data is released under the Creative Commons license - Attribution - CC BY (https://creativecommons.org/licenses/by/4.0/). This license states that consumers ("Data Users" herein) may distribute, adapt, reuse, remix, and build upon this work, as long as they give appropriate credit, provide a link to the license, and indicate if changes were made.
 
The Data User has an ethical obligation to cite the data source (see the DOI number) in any publication or product that results from its use. Communication, collaboration, or co-authorship (as appropriate) with the creators of this data package is encouraged. 
 
Extensive efforts are made to ensure that online data are accurate and up to date, but the authors will not take responsibility for any errors that may exist in data provided online. Furthermore, the Data User assumes all responsibility for errors in analysis or judgment resulting from use of the data. The Data User is urged to contact the authors of the data if any questions about methodology or results occur. 



### Data Structure

The data can be found in the folder `data`. The data is structured as follows:

- **Level 0**: Raw data collected from the different sensors.
- **Level 1**: Data is converted to NetCDF and quality assurance is applied. Quality flag "1" indicates that the data point didn't pass the quality checks and further investigation is needed, quality flag "0" indicates that the data has passed the quality assurance check. Do not forget to apply the quality check mask when analysing the data.
- **Level 2**: Resampled and filled. The data is downsampled to 10min resolution and some of the smaller gaps are filled with linear interpolation.

## Quality assurance

Quality checks include but are not limited to range validation, data type checking and flagging missing data.
The automatic quality check is controlled by the package [Envass](https://pypi.org/project/envass/). The specific methods implemented for this dataset are listed in `notes/quality_assurance.json`. 

###  Events 

Maintenance dates, interesting or surprising events, non identified by the quality assurance outliers are listed in the folder `notes/events.csv`.
Check also the `notes/sensor_history.csv` (if existing)

## Collaborators

- **Concept, finances, project management** Damien Bouffard, Jean Guillard, Bas Ibelings, Natacha Pasche, Marie-Elodie Perga, Alfred Wüest   
- **Installation, maintenance, data collection** Aurélien Ballu, Guillaume Cunillera, Roxane Fillion, Matteo Gios, Sébastien Lavanchy, Floreana Miesen, Michael Plüss, Philippe Quetin 
- **Data pipeline** James Runnalls
- **Data review** Damien Bouffard
- **Contact tech** Sébastien Lavanchy, sebastien.lavanchy@epfl.ch 
- **Contact science** Damien Bouffard. damien.bouffard@eawag.ch

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-g.svg?label=Data%20License
[mit-by]: https://opensource.org/licenses/MIT
[mit-by-shield]: https://img.shields.io/badge/License-MIT-g.svg?label=Code%20License
