To make a html build, please follow these steps:

1. install sphinx:
pip install sphinx

2. Go to the docs folder in your python terminal:
..\CoSMoS\docs

3. Run the following command:
./make html

This should create the folders:
..\CoSMoS\docs\_build\
..\CoSMoS\docs\source\_generated\

Open this file to view your manual:
..\CoSMoS\docs\_build\html\index.html

Debugging:

- failed to import XXX: no module named XXX
	->If autosummary is not created, check if all the packages / modules in the script can be imported. If not, the summary will not be generated.
- when the autosummary is fixed (or other fixes), it can still not appear in the html code. Delete the _build folder and run the ./make html again.
