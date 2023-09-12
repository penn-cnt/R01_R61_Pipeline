import re
import os
import time
import random
import calendar
import numpy as np
from sys import argv
from datetime import datetime as DT

def check_for_names(data):
    
    # Read in the name list
    names = []
    fp    = open(argv[2],'r')
    tmp   = fp.readline()[:-1]
    while tmp:
        names.append(tmp.lower())
        tmp = fp.readline()
    fp.close()
    
    # Make a list of possible words
    words = data.split()
    for iword in words:
        if iword.lower() in names:
            raise Exception("PHI Leak found. Code exited with a failure.")        
    

def check_for_dates(data,raiseExcept=True):
    
    # Create various date format strings in regex
    regex_frmt_list = []
    regex_frmt_list.append(re.compile("^[A-Za-z]*-[0-9]{2}-[0-9]{4}"))  # e.g. Jan-01-2020
    regex_frmt_list.append(re.compile("^[0-9]{2}-[A-Za-z]*-[0-9]{4}"))  # e.g. 01-Jan-2020
    regex_frmt_list.append(re.compile("^[A-Za-z]*/[0-9]{2}/[0-9]{4}"))  # e.g. Jan/01/2020
    regex_frmt_list.append(re.compile("^[0-9]{2}/[A-Za-z]*/[0-9]{4}"))  # e.g. 01/Jan/2020 (The "but why?" format)
    regex_frmt_list.append(re.compile("^[0-9]{2}-[0-9]{2}-[0-9]{4}"))   # e.g. 01-01-2020 (The cursed formats)
    regex_frmt_list.append(re.compile("^[0-9]{2}/[0-9]{2}/[0-9]{4}"))   # e.g. 01/01/2020 (The cursed formats)
    
    # Associate each entry with datetime object to ensure date shift
    dtime_frmt_list = []
    dtime_frmt_list.append('%b-%d-%Y')
    dtime_frmt_list.append('%d-%b-%Y')
    dtime_frmt_list.append('%b/%d/%Y')
    dtime_frmt_list.append('%d/%b/%Y')
    dtime_frmt_list.append('%m-%d-%Y')
    dtime_frmt_list.append('%d/%m/%Y')
    
    # Loop over a whitespace split data string
    for idx,ival in enumerate(data.split()):
        flags = [iprog.search(ival) for iprog in regex_frmt_list]
        bools = np.array([iflag!=None for iflag in flags])
        if bools.any():
            if data.split()[idx-1] == 'startdate':
                fstr      = dtime_frmt_list[np.where(bools)[0][0]]
                dtime_obj = DT.strptime(ival,fstr)
                
                if dtime_obj.year > 2000:
                    print("Start time %s appears to be date-shifted." %(ival))                
            else:
                if raiseExcept:
                    print("Possible PHI Leak in dates. Please confirm data is properly secure.")
                    print("If data is secure, you can skip this exception by passing raiseExcept=False")
                    raise Exception("PHI Leak found. Code exited with a failure.")


def clean_data(fn):
    """
    Create a somewhat cleaner copy of the binary data. This is just meants to give
    us an idea of what human readable strings might be hiding within.

    Parameters
    ----------
    fn : String
        Path to binary file to read in.

    Returns
    -------
    String Object

    """

    fp        = open(fn,'rb')
    data      = fp.readline()
    data_cln  = ''
    nflag     = False
    blacklist = ['\\x','\\t','\\n','\\r','\\\\']
    prog      = re.compile("[^A-Za-z0-9_-][A-Za-z0-9_-][^A-Za-z0-9_-]|[A-Za-z0-9_-][^A-Za-z0-9_-][A-Za-z0-9_-]|[A-Za-z0-9_-][^A-Za-z0-9_-]|[^A-Za-z0-9_-][A-Za-z0-9_-]")
    while data:
        
        # Convert to string type
        data_str = str(data).lower()

        # Clean up the string
        for val in data_str.split():
            ival = val.strip("b'")
            ival = ival.strip('b"')
            if not any(substring in ival for substring in blacklist):
                if prog.search(ival) == None:
                    if len(ival)>1:
                        data_cln += ' ' + ival
                        nflag     = True

        # Add carriage return as needed
        if nflag:
            data_cln += '\n'
            nflag     = False

        data = fp.readline()
    fp.close()
    return data_cln

if __name__=='__main__':

    fn   = argv[1] 
    data = clean_data(fn)
    check_for_dates(data)
    check_for_names(data)

