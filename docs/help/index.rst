
HELP
====


Introduction
------------

MESSy (Molecular Epidemiology and Surveillance System) is a system that combines data management and simple LIMS.
It is designed to work in conjunction with NGS data analysis pipeline at https://github.com/trmznt/ncov19-pipeline.


Basic Concept
-------------

The data in MESSy is modelled as following:

Institution - any official entity that relates to the sample

Collection - a sample set container that relates to one or more entities and user groups.
Only user member of the group can manage or view the samples in the collection.

Sample - the main object that holds all metadata related to the samples.

Plate - this object is used to holds data that relate to each sample and can be observed or measured, such as RNA
extraction results, amplification results, quantification results, etc.

Run - represents a sequencing run

Sequence - represents results of data analysis of each sample from the sequencing run


Data Processing
---------------

Data can either be entered to the system using form-based web interface or uploaded to system using csv (comma
separated value) or tsv (tab-separated value) files.
The csv/tsv files can be prepared using software environments that have user-friendly ways to work with column-based text files (such as R or Python with Pandas) or a spreadsheet software (such as Microsoft Excel, Libreoffice Calc or Google Sheet).
Please be careful that if you are using spreadsheet software, some of the software perform automatic formatting of the date value (or values that look like dates).
To avoid confusion, all date are represented as YYYY-MM-DD format. It is best to recheck the content of the csv/tsv file saved by spreadsheet software using plain text editors (Notepad, Wordpad, ConTEXT) or using R or Python.
