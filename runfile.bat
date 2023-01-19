@echo off
setlocal enabledelayedexpansion

:: Ensure correct location
cd "C:\Users\Seatronic 1147\Documents\Data_Lexplore\git\thermister-chain"

:: Load input variables
call "scripts\input_batch.bat"

:: Backup files
md %backup%
robocopy %in% %backup% /NFL /NDL /NJH /NJS /nc /ns /np

:: Process meteostation data
for %%a in (%in%"\*.dat") do (
	%pythonenv% %script% "%%a"
)

%pythonenv% %upload% -w

curl "https://api.datalakes-eawag.ch/update/448"


