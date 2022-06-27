This folder is where CoSMoS configuration files are stored.

The config file can be specified in the call to cosmos.initialize().

E.g. cosmos.initialize("d:\\cosmos", "gom_forecast", config_file="default.xml")

With no configuration file specified in cosmos.initialize(), CoSMoS will use default.xml.

You'll need to copy template.xml to default.xml, and edit default.xml.

Enter correct paths to model executables, and ftp connection parameters. 

The delft3dfm_exe_path should look something like this:

<delft3dfm_exe_path>"c:\\Program Files (x86)\\Deltares\\Delft3D Flexible Mesh Suite HMWQ (2021.02)\\plugins\\DeltaShell.Dimr\\kernels"</delft3dfm_exe_path>

Make sure that there are double quotes around paths with spaces !
