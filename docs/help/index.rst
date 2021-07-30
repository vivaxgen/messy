
HELP
====


Introduction
------------

MESSy (Molecular Epidemiology and Surveillance System) is a system that combines data management and simple LIMS, and its source code is deposited at https://github.com/trmznt/messy.

The system is designed to work in conjunction with NGS data analysis pipeline at https://github.com/trmznt/ncov19-pipeline.


Basic Concept
-------------

The data in MESSy is modelled as following:

**Institution** - any official entity that relates to any sample

**Collection** - a sample set container that relates to one or more entities and user groups.
Only user member of the group can manage or view the samples in the collection.

**Sample** - the main object that holds all metadata related to the samples.

**Plate** - this object is used to holds observable or measureable data that relate to each sample, such as RNA
extraction content results, amplification results, quantification results, etc.

**Run** - represents a sequencing run

**Sequence** - represents results of data analysis of each sample from the sequencing run


Data Processing
---------------

Preparation
~~~~~~~~~~~

Data can either be entered to the system using form-based web interface or uploaded to system using csv (comma
separated value) or tsv (tab-separated value) files.
The csv/tsv files can be prepared using software environments that have user-friendly ways to work with column-based text files (such as R or Python with Pandas) or a spreadsheet software (such as Microsoft Excel, Libreoffice Calc or Google Sheet).

Date Format
~~~~~~~~~~~

To avoid confusion, all dates are represented as **YYYY/MM/DD** (or **YYYY-MM-DD**) format.

Please be when you are using spreadsheet software since some of the software perform automatic formatting of the date values (or values that look like dates).
It is best to recheck the content of the csv/tsv file saved by spreadsheet software using plain text editors (Notepad, Wordpad, ConTEXT) or using R or Python before uploading just to make sure that dates are formatted properly.
