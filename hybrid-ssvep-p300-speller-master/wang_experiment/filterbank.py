# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 10:16:21 2019

@author: ALU
"""
import warnings
import scipy.signal
import numpy as np

def filterbank(eeg, fs, idx_fb):
    if idx_fb == None:
        warnings.warn('stats:filterbank:MissingInput '\
                          +'Missing filter index. Default value (idx_fb = 0) will be used.')
        idx_fb = 0
    elif (idx_fb < 0 or 9 < idx_fb):
        raise ValueError('stats:filterbank:InvalidInput '\
                          +'The number of sub-bands must be 0 <= idx_fb <= 9.')
            
    if (len(eeg.shape)==2):
        num_chans = eeg.shape[0]
        num_trials = 1
    else:
        _, num_chans, num_trials = eeg.shape
    
    # Nyquist Frequency = Fs/2N
    Nq = fs/2
    
    passband = [6, 14, 22, 30, 38, 46, 54, 62, 70, 78]
    stopband = [4, 10, 16, 24, 32, 40, 48, 56, 64, 72]
    Wp = [passband[idx_fb]/Nq, 90/Nq]
    
    #print("Wp: ", Wp)
    Ws = [stopband[idx_fb]/Nq, 100/Nq]
    
    #print("Ws: ", Ws)
    [N, Wn] = scipy.signal.cheb1ord(Wp, Ws, 3, 40) # band pass filter StopBand=[Ws(1)~Ws(2)] PassBand=[Wp(1)~Wp(2)]
    [B, A] = scipy.signal.cheby1(N, 0.5, Wn, 'bandpass') # Wn passband edge frequency
    
    y = np.zeros(eeg.shape)
    
    if (num_trials == 1):
        for ch_i in range(num_chans):
            #apply zero-phase filter
            y[ch_i, :] = scipy.signal.filtfilt(B, A, eeg[ch_i, :], method='gust')  
        
    else:
        for trial_i in range(num_trials):
            for ch_i in range(num_chans):
                y[:, ch_i, trial_i] = scipy.signal.filtfilt(B, A, eeg[:, ch_i, trial_i], method='gust')
                
    return y
