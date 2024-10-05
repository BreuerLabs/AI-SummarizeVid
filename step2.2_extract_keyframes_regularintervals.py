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


## NOTE: This script requires ffmpeg for frame extraction
## NOTE: We assume videos are stored in PRES_AD_VIDEOS/


METADATA_FNAME = 'METADATA.csv'


if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Create keyframe storage directory if they don't already exist:
    if rank == 0:
        if not os.path.exists("keyframes_regintervals"): 
            os.makedirs("keyframes_regintervals") 


    proc_time0 = datetime.now()
    local_errors = []

    metadata_df = pd.read_csv(METADATA_FNAME)

    # Each processor gets a list of CSV row indices we want to process in parallel
    local_mastercsv_idx_split = np.array_split(list(range(len(metadata_df))), size)[rank] 

    for local_count, idx in enumerate(local_mastercsv_idx_split):
        if local_count>1:
            proc_elapsed_min = (datetime.now()-proc_time0).total_seconds()/60.
            print('\nrank', rank, 'starting CSV row', idx, 'which is local workload', 
                local_count, 'of', len(local_mastercsv_idx_split), 'in', proc_elapsed_min, 'min;', 
                proc_elapsed_min * float(len(local_mastercsv_idx_split)-local_count)/float(local_count), 'mins remain')

        vid_fname = metadata_df['FILENAME'].values[idx]
        local_vid_fpath = 'PRES_AD_VIDEOS/' + vid_fname

        try:
            # Take frames at 3sec intervals until video end is reached:
            for frame_sample_time in range(3000, 180000, 3000):
                image_output_fpath = 'keyframes_regintervals/' + vid_fname + "_" + str(frame_sample_time) + ".jpg"
                # print('\n\n', local_vid_fname + "_" + str(frame_sample_time) + ".jpg")
                # ffmpeg -ss 12 -i P-1026-41628.mp4 -frames:v 1 testframe.jpg
                subprocess.run(['ffmpeg', '-ss', str(frame_sample_time/1000.),  '-i',  local_vid_fpath, 
                    '-frames:v', '1', image_output_fpath, '-y', '-hide_banner', '-loglevel', 'warning'] )

        except Exception as e:
            print('ERROR:', e, 'processor', rank, local_vid_fpath)
            local_errors.append([rank, e, local_vid_fpath])
            continue

    if len(local_errors):
        print(local_errors)


