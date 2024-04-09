# -*- coding: utf-8 -*-
"""
Created on Tue Apr  9 10:49:34 2024

@author: U013179
"""

conda create --name whisperx python=3.12

conda activate whisperx

import whisper
import os
import glob
import csv
import git

repo = git.Repo('.', search_parent_directories=True)
repo.working_tree_dir

audio_folder = os.path.join(repo.working_tree_dir,'audio','raw','mm_pilots','PTB_audio','mmpilot_06','cov')
transcription_folder = os.path.join(repo.working_tree_dir, 'data', 'raw_transcriptions','overt_phase_transcriptions')


audio_files = glob.glob(os.path.join(audio_folder, "*trial_*.wav"))
for audio_file in audio_files:
    print(audio_file)
    
model = whisper.load_model("large-v2")

from whisper.utils import get_writer
tsv_writer = get_writer("tsv", transcription_folder)

# loop transcribing audio files
# Save transcription as .tsv

os.chdir(audio_folder)

for audio_file in audio_files:
        
        print("Transcribing: " + audio_file)
        
        audio_filename = os.path.basename(audio_file)
        audio_transcription = model.transcribe(audio_filename,
                                               fp16=False, 
                                               verbose=True, 
                                               language="dutch")
        
        transcription_filename = os.path.splitext(audio_filename)[0] + '_transcription.tsv'
        transcription_file_path = os.path.join(transcription_folder, transcription_filename)
        
        print("saving transcription")
        tsv_writer(audio_transcription, audio_filename)
                    
        os.chdir(audio_folder)