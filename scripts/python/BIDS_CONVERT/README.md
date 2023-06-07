> %run DICOM_TO_BIDS.py --dataset RAW/ --datefile DICOM_DATES.csv --datalake HUP_BIDS_DATALAKE.pickle --bidsroot ./BIDSROOT/ --subject 0 --wrapper

I ran this from a python terminal. It requires nibabel and pybids to run.

It also import pydicom, but does not use it at present. So you can comment out that import if needed.

The dataset keyword points to the folder where your niftii files reside.

The datefile is a generated file. It store the session names used for a particular subject on a given date. 

The datalake is just the dictionary file we use to store protocol names. I've included the original csv and the pickle file for you. You may need to make some changes and add new keywords for your institution. I will be updating this code soon 
to make updating it easier to manage. But for now you can unpickle it and add keywords in python, or use the convert_legacy_datalake.py by adding entries to the csv file it reads in. 

The bidsroot flag is where you want the bids data to go.

Subject is the subject id

Wrapper is a necessary flag at present, but doesn't do anything important. It is a vestigial piece of code from development.
