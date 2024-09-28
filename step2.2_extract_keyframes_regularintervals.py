import numpy as np
from datetime import datetime
import pandas as pd
import subprocess
import os
import glob
from mpi4py import MPI


"""
This script saves a still frame at evenly time-spaced intervals from each ad video
"""

METADATA_FNAME = 'METADATA.csv'


if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    proc_time0 = datetime.now()
    local_errors = []

    mastercsv_df = pd.read_csv(METADATA_FNAME)

    # Each processor gets a list of CSV row indices we want to process in parallel
    local_mastercsv_idx_split = np.array_split(list(range(len(mastercsv_df))), size)[rank] 

    for local_count, idx in enumerate(local_mastercsv_idx_split):
        if local_count>1:
            proc_elapsed_min = (datetime.now()-proc_time0).total_seconds()/60.
            print('\nrank', rank, 'starting CSV row', idx, 'which is local workload', 
                local_count, 'of', len(local_mastercsv_idx_split), 'in', proc_elapsed_min, 'min;', 
                proc_elapsed_min * float(len(local_mastercsv_idx_split)-local_count)/float(local_count), 'mins remain')

        vid_fpath = metadata_df['FILENAME'].values[idx]
        local_vid_fname = 'pres_trimmed_incl_scene/' + vid_fpath

        try:
            # Take frames at 3sec intervals until video end is reached:
            for frame_sample_time in range(3000, 180000, 3000):
                image_output_fpath = 'pres_trimmed_inclscene_whisper_segment_centerframes_regularspaced/' + local_vid_fname + "_" + str(frame_sample_time) + ".jpg"
                # print('\n\n', local_vid_fname + "_" + str(frame_sample_time) + ".jpg")
                # ffmpeg -ss 12 -i P-1026-41628.mp4 -frames:v 1 testframe.jpg
                subprocess.run(['ffmpeg', '-ss', str(frame_sample_time/1000.),  '-i',  local_vid_fpath, 
                    '-frames:v', '1', image_output_fpath, '-y', '-hide_banner', '-loglevel', 'warning'] )

        except Exception as e:
            print('ERROR:', e, 'processor', rank, vid_fpath)
            local_errors.append([rank, e, vid_fpath])
            continue

    if len(local_errors):
        print(local_errors)


