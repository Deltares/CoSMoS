.. _super_regions:

Defining super regions
------------

For large scale storm forecasting, it is often necessary to run multiple models. 
These models can be referenced individually in the scenario file or per region.
You can also combine different regions into a super_region file.
These models can be called individually in the scenario file, or per region.
However, you can also aggregrate different regions in a super region file, located in the *super_regions* folder. 
You can then refer to this super_region in your scenario file with the keyword <super_region>.
By using a super region file, you can simplify the structure of your scenario file.
An example of a super_region file is given below.  

.. include:: examples/super_region.xml
       :literal: 
       