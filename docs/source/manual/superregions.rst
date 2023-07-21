.. _super_regions:

Defining super regions
------------

For large scale storm forecasting, it is often necessary to run multiple models. For example, you can have several models for each US state. 
These models can be referenced individually in the scenario file, or per region.
However, you can also combine different regions into a super region file, located in the *super_regions* folder. 
You can then refer to this *super_region* in your scenario file with the keyword *super_region*, simplifying the structure of your scenario file.
An example of a super_region file is given below: 

.. include:: examples/super_region.xml
       :literal: 
       