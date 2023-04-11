import argparse
import numpy as np
from sys import argv,exit
import pyedflib.highlevel as EDFHL
from numpy.random import default_rng
from scipy.stats import chisquare,ks_2samp

def time_slice_across_channels(filename,t_start,t_end,f_obs):
    """
    Return the data across all channels between the start time and end time.

    Parameters
    ----------
    filename : STR
        Path to EDF file.
    t_start : FLOAT
        Start time in seconds relative to first recording.
    t_end : FLOAT
        End time in seconds relative to first recording.
    f_obs : INT
        The observed/recording frequency.

    Returns
    -------
    Array with EEG measurements of shape [MxN] where
    M = Number of channels
    N = (t_end-t_start)*freq_obs

    """
    
    # Read in the channel names and total time
    header   = EDFHL.read_edf_header(filename)
    channels = np.array(header['channels'])
    t_tot    = header['Duration']
    
    # Make an array for searching times again and convert start and end to ind
    inds      = np.arange(t_tot*f_obs)
    ind_start = np.round(t_start*f_obs).astype('int')
    ind_end   = np.round(t_end*f_obs).astype('int') 
        
    # Loop over channel
    for idx,ichannels in enumerate(channel_bin):
        rawdata = EDFHL.read_edf(filename,ch_names=ichannels[(ichannels!='')].tolist())[0]
        rawdata = rawdata[:,ind_start:ind_end]
        
        try:
            output = np.vstack((output,rawdata))
        except NameError:
            output = rawdata

    return output

def channel_comparison(channels_truth,channels_test):
    """
    Confirms whether two channel maps agree. This allows us to make sure versions
    do not alter this sensitive information.

    Parameters
    ----------
    channels_truth : ARRAY
        Array of channel names in our source file.
    channels_test : ARRAY
        Array of channel names in a submitted file.

    Returns
    -------
    None.

    """

    # Confirm that the sizes match.
    if channels_truth.size != channels_test.size:
        raise Exception("Unequal number of channels. Code exited with a failure.")

    # Get the channels that only appear in one array of the other
    channel_setdiff = np.setdiff1d(channels_truth,channels_test)
    
    # Alert user to unique channels if needed
    if channel_setdiff.size>1:
        print('Channels do not map between versions.')
        print("The following channels appear in source version that do not appear in submitted version.")
        for ival in channel_setdiff:
            print("+ %s" %(ival))
        print("Qutting step with exception.")
        raise Exception("Code exited with a failure.")

def time_relative_diff(data_truth,data_test,stype,dbin=100,nbin=100):
    
    # Clip the data to make it fit with the requested bin size
    rmndr = (data_truth.size%dbin)
    
    # Transpose the raw data into column-wise bins
    data_truth_raw_bin = data_truth[:-rmndr].reshape((-1,dbin)).T
    data_test_raw_bin  = data_test[:-rmndr].reshape((-1,dbin)).T

    # Get the binning
    mn  = np.amin([data_truth.min(),data_test.min()])
    mx  = np.amax([data_truth.max(),data_test.max()])
    bns = np.linspace(mn,mx,nbin)
    
    # Make new outputs
    data_truth_bins = np.zeros((nbin-1,data_truth_raw_bin.shape[1]))
    data_test_bins  = np.zeros((nbin-1,data_test_raw_bin.shape[1]))
    
    # Populate the new outputs
    for icol in range(data_truth_bins.shape[1]):
        data_truth_bins[:,icol] = np.histogram(data_truth_raw_bin,bins=bns)[0]
        data_test_bins[:,icol]  = np.histogram(data_test_raw_bin,bins=bns)[0]
    
    # Calculate the chi-squared score
    if stype == 'ks2samp':
        return ks_2samp(data_truth, data_test)
    elif stype == 'chi2':
        return chisquare(data_test_bins,data_truth_bins)

def data_handler(ftruth,ftest,channel_names,duration,metric_dict,stype,metric='time'):
    
    # Read in the relevant data
    data_truth = EDFHL.read_edf(ftruth,ch_names=channel_names.tolist())[0]
    data_test  = EDFHL.read_edf(ftest,ch_names=channel_names.tolist())[0]
    
    # Quick check if arrays are equa
    if not np.array_equal(data_truth, data_test):     # Remove not for production. This is to enforce test on sample.
        return
    else:
        if not np.allclose(data_truth,data_test):  # Remove not for production. This is to enforce test on sample.
            return
        else:
            if metric == 'time':
                for irow in data_truth.shape[0]:
                    metric_dict[channel_names[irow]] = time_relative_diff(data_truth[irow],data_test[irow],stype)
                return metric_dict
            elif metric == 'channel':

                # Get number of samples
                nind      = int(duration/10.)
                if nind%2==1:
                    nind -= 1

                # Randomly grab time samples and save them
                rng       = default_rng(seed=42)
                tinds     = np.sort(rng.choice(duration,size=nind,replace=False)).reshape((-1,2))
                new_truth = {}
                new_test  = {}
                for itime in tinds:
                    itruth = data_truth[:,itime[0]:itime[1]].flatten()
                    itest  = data_test[:,itime[0]:itime[1]].flatten()                    
                    new_truth[tuple(itime)] = itruth
                    new_test[tuple(itime)]  = itest
                        
                return new_truth,new_test

def main():
    
    # Add command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_truth', required=True, help="File containing the truth/reference data.")
    parser.add_argument('--file_test', required=True, help="File containing the test/proposed data.")
    parser.add_argument('--test_type', default='time', choices=['time','channel'], help="Test distribution across input type.)")
    parser.add_argument('--stat_type', default='ks2samp', choices=['ks2samp','chi2'], help="Statistic to use.)")
    args=parser.parse_args()
    
    # Save the arguments to shorter variable name
    ftruth = args.file_truth
    ftest  = args.file_test
    ttype  = args.test_type
    stype  = args.stat_type
    
    # Read in the file header
    header_truth = EDFHL.read_edf_header(ftruth)
    header_test  = EDFHL.read_edf_header(ftest)
    
    # Get the channel names
    channels_truth = np.array(header_truth['channels'])
    channels_test  = np.array(header_test['channels'])
    
    # Get the duration
    duration = header_truth['Duration']

    # Remap the channel array for bulk reading in of data
    chnbin      = 10
    channel_bin = np.pad(channels_truth,(0,chnbin-(channels_truth.size%chnbin)),constant_values='')
    channel_bin = channel_bin.reshape((-1,chnbin))

    # Test the channel mapping
    channel_comparison(channels_truth, channels_test)    
    
    # Test the data for each channel to confirm if it is within acceptance criteria
    GoF = {}
    for ichannels in channel_bin[:2]:
        if ttype == 'time':
            GoF = data_handler(ftruth,ftest,ichannels,duration,GoF,stype)
        if ttype == 'channel':
            new_truth,new_test = data_handler(ftruth,ftest,ichannels,duration,GoF,stype,metric=ttype)

            try:
                data_truth = data_truth|new_truth
                data_test  = data_test|new_test
            except NameError:
                data_truth = new_truth
                data_test = new_test

    if ttype == 'channel':
        
        for ikey in data_truth.keys():

            # Make binning variables            
            nbin = 100
            mn   = np.amin([np.amin(data_truth[ikey]),np.amin(data_test[ikey])])
            mx   = np.amax([np.amax(data_truth[ikey]),np.amax(data_test[ikey])])
            bns  = np.linspace(mn,mx,nbin)

            # Get the fit
            cnts_truth,edges = np.histogram(data_truth[ikey],bins=bns)
            cnts_test,edges  = np.histogram(data_test[ikey],bins=bns)
            if stype == 'ks2samp':
                GoF[ikey] = ks_2samp(cnts_truth,cnts_test)
            elif stype == 'chi2':
                GoF[ikey] = chisquare(cnts_truth,cnts_test)
        
        return GoF


if __name__ == '__main__':
    
    # Call main function
    GoF = main()
    
