FROM continuumio/miniconda3

# Create a new Conda environment
RUN conda create -n cosmos3 python=3.10

#COPY ./cosmos_clean_floris_02/cosmos_runfolder/scenarios/hurricane_ian_01/20220928_00z/models/gulf_of_mexico/sfincs/sfincs_gom_500m_ensemble/input /input
#Change to where you have cht
#COPY ./CoastalHazardsToolkit /cht
#COPY c:/work/checkouts/git/CoastalHazardsToolkit /cht

RUN pip install deltares-coastalhazardstoolkit
RUN pip install boto3

# Activate the Conda environment
SHELL ["conda", "run", "-n", "cosmos3", "/bin/bash", "-c"]

RUN mkdir output
WORKDIR /input

CMD ["python", "run_job.py"]