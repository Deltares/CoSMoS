@ echo off
DATE /T > running.txt

rem How to run a Python script in a given conda environment from a batch file.

rem Define here the path to your conda installation
set CONDAPATH=c:\Users\%username%\Anaconda3
rem Define here the name of the environment
set ENVNAME=cosmos

rem The following command activates the base environment.
call %CONDAPATH%\Scripts\activate.bat

set ENVPATH=CONDAPATHKEY\envs\%ENVNAME%

rem Activate the conda environment
rem Using call is required here, see: https://stackoverflow.com/questions/24678144/conda-environments-and-bat-files
call %CONDAPATH%\Scripts\activate.bat %ENVNAME%

rem Run a python script in that environment
python EXEPATHKEY\run_beware.py 

rem Deactivate the environment
call conda deactivate

move running.txt finished.txt