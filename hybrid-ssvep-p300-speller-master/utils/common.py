from brainflow import BoardShim
import mne
import logging
from mne.datasets import eegbci
import os
from pathlib import Path
import argparse
import json
from psychopy import visual
import numpy as np
from utils.speller_config import *
import pickle

def create_session_folder(subj,dir):
    base_path = os.getcwd() + "\\"
    dir = base_path + dir
    folder_name = f'{subj}'
    print(folder_name)
    if os.path.isdir(os.path.join(dir, folder_name)):
        folder_path = os.path.join(dir, folder_name)
    else:
        folder_path = os.path.join(dir, folder_name)
        os.makedirs(folder_path)
    return folder_path

def getdata(data,board,clear_buffer=False,n_samples=None,dropEnable = False):
    """
        Get data that has been recorded to the board. (and clear the buffer by default)
        if n_samples is not passed all of the data is returned.
    """
    # Creating MNE objects from brainflow data arrays
    # the only relevant channels are eeg channels + marker channel
    # get row index which holds markers
    # print("INSIDE GET DATA")
    # print(data.shape)
    marker_channel = BoardShim.get_marker_channel(board)
    
    #row which hold eeg data
    eeg_channels = BoardShim.get_eeg_channels(board)
    #print(f'Before {data[eeg_channels]}')
    data[eeg_channels] = data[eeg_channels] / 1e6
    #print(f'After {data[eeg_channels]}')
    #eeg row + marker row (8 + 1)

    data = data[eeg_channels]
    
    #string of all channel name ['Fp1', 'Fp2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2']
    ch_names = BoardShim.get_eeg_names(board)
    ch_types = (['eeg'] * len(eeg_channels))

    
    # print(ch_names)
    #sample rate
    sfreq = BoardShim.get_sampling_rate(board)
    
    #Create Raw data from MNE
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
    raw = mne.io.RawArray(data, info)
    # print(raw)
    logging.info(f"{str(raw)}")
    raw_data = raw.copy()
    eegbci.standardize(raw_data)
    montage = mne.channels.make_standard_montage('standard_1020')
    raw_data.set_montage(montage)
  
    raw_data = raw_data.notch_filter([50,100], trans_bandwidth = 3)
    raw_data = raw_data.filter(4,77)

    # data = data[:8,:1740]
    # order = 1
    # l_freq = 4
    # sos = signal.butter(order, l_freq, 'highpass', analog=False, fs=250, output='sos')
    # notch_freq = 50
    # quality = 1
    # b,a = signal.iirnotch(notch_freq, quality, fs=250)
    # for i in range(8):
    #     data[i] = signal.lfilter(b, a, data[i])
    #     data[i] = signal.sosfilt(sos, data[i])
    # X = np.expand_dims(data[:],axis=0)

    # print("Shape of data", X.shape)
    #2 electrode
    
    if dropEnable == True:
        raw_data.pick_channels(['C3','C4','STIM MARKERS']) 
        #raw_data = raw_data.drop_channels(['Fp1', 'Fp2', 'P7', 'P8', 'O1', 'O2'])
        #raw_data = raw_data.drop_channels(['Fz'])

    # print(raw_data.info['ch_names'])

    return raw_data

# This one for offline experiment
def getdata_offline(data,board,clear_buffer=False,n_samples=None,dropEnable = False):
    """
        Get data that has been recorded to the board. (and clear the buffer by default)
        if n_samples is not passed all of the data is returned.
    """
    # Creating MNE objects from brainflow data arrays
    # the only relevant channels are eeg channels + marker channel
    # get row index which holds markers
    # print("INSIDE GET DATA")
    # print(data.shape)
    marker_channel = BoardShim.get_marker_channel(board)
    
    #row which hold eeg data
    eeg_channels = BoardShim.get_eeg_channels(board)
    #print(f'Before {data[eeg_channels]}')
    data[eeg_channels] = data[eeg_channels] / 1e6
    #print(f'After {data[eeg_channels]}')
    #eeg row + marker row (8 + 1)
    data = data[eeg_channels + [marker_channel]]
    # data = data[eeg_channels]
    
    #string of all channel name ['Fp1', 'Fp2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2']
    ch_names = BoardShim.get_eeg_names(board)
    ch_types = (['eeg'] * len(eeg_channels)) + ['stim']
    # ch_types = (['eeg'] * len(eeg_channels))
    ch_names = ch_names + ["Stim Markers"]
    
    # print(ch_names)
    #sample rate
    sfreq = BoardShim.get_sampling_rate(board)
    
    #Create Raw data from MNE
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
    raw = mne.io.RawArray(data, info)
    # print(raw)
    logging.info(f"{str(raw)}")
    raw_data = raw.copy()
    eegbci.standardize(raw_data)
    montage = mne.channels.make_standard_montage('standard_1020')
    raw_data.set_montage(montage)
    # raw_data=raw_data.notch_filter([50,75,100], filter_length='auto')
    # raw_data = raw_data.notch_filter(np.arange(50, 125, 50), filter_length='auto', phase='zero')
    #2 electrode
    
    if dropEnable == True:
        raw_data.pick_channels(['C3','C4','STIM MARKERS']) 
        #raw_data = raw_data.drop_channels(['Fp1', 'Fp2', 'P7', 'P8', 'O1', 'O2'])
        #raw_data = raw_data.drop_channels(['Fz'])

    # print(raw_data.info['ch_names'])

    return raw_data

def save_raw(raw, name,dir, participant_id):
    folder_path = create_session_folder(participant_id,dir)
    raw.save(os.path.join(folder_path, f'{name}{TYPE_OF_FILE}'), overwrite = True)
    return os.path.basename(folder_path)

def save_ssvep_raw(raw, name,dir):
    folder_path = create_session_folder(name,dir)
    raw.save(os.path.join(folder_path, f'{name}{TYPE_OF_FILE}'), overwrite = True)
    return os.path.basename(folder_path)

def save_raw_to_dataframe(raw,name):
    epoch_dataframe = raw.copy().to_data_frame()
    csv_folder = create_session_folder(PARTICIPANT_ID,CSV_DIR)
    csv_name = f'{name}.csv'
    epoch_dataframe.to_csv(os.path.join(csv_folder,csv_name),encoding='utf-8')


def drawTextOnScreen(message,window) :
    message = visual.TextStim(window, text=message, color=(-1., -1., -1.))
    message.draw() # draw on screen
    window.flip()   # refresh to show what we have draw

# def get_stimuli_positions():
#     n_rows = NO_ROWS
#     n_cols = NO_COLUMNS
#     monitor_width = 60  # monitor width in cm
#     monitor_height = 33  # monitor height in cm
#     viewing_distance = 60  # viewing distance in cm
#     stim_size = [WIDTH, HEIGHT]  # size of each stimulus in degrees
#     gap_size = [12, 12]  # gap size between stimuli in degrees
#     stim_positions = []  # array to hold stimulus positions

#     # Calculate stimulus positions
#     x_start = -(n_cols-1)*(stim_size[0]+gap_size[0])/2  # starting x-position
#     y_start = (n_rows-1)*(stim_size[1]+gap_size[1])/2  # starting y-position
#     for i in range(n_rows):
#         for j in range(n_cols):
#             x_pos = x_start + j*(stim_size[0]+gap_size[0])
#             y_pos = y_start - i*(stim_size[1]+gap_size[1])
#             stim_positions.append((x_pos, y_pos))
#     return x_start, y_start, stim_positions

def save_csv(data, name, dir, participant_id):

    folder_path = create_session_folder(participant_id,dir)
    filename = os.path.join(folder_path, f'{name}')
    with open(filename + '.pickle', 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
