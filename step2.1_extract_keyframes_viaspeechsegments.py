import numpy as np
import pandas as pd
from mpi4py import MPI
import subprocess
import os
import glob
import cv2



"""
This script saves a frame from the middle instant of each segment of whisper-transcribed text
for each ad video in the master CSV (parallelized across videos)
"""

## NOTE: This script requires ffmpeg for frame extraction
## NOTE: We assume videos are stored in pres_ad_videos/ and transcripts are stored as in step1 script


METADATA_FNAME = 'METADATA.csv'


filepaths_transcripts_local = glob.glob('pres_ad_whisptranscripts_json/*.json')
transcribed_videos_local = [x.split('/')[-1].split('.')[0] for x in filepaths_transcripts_local]


if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Create keyframe storage directory if they don't already exist:
    if rank == 0:
        if not os.path.exists("keyframes_speechcentered"): 
            os.makedirs("keyframes_speechcentered") 

    metadata_df = pd.read_csv(METADATA_FNAME)

    # Each processor gets a list of CSV row indices we want to process in parallel
    for idx in np.array_split(list(range(len(metadata_df))), size)[rank]:
        
        vid_fname = metadata_df['FILENAME'].values[idx]
        local_vid_fpath = 'pres_ad_videos/' + vid_fname

        try:
            tsv = pd.read_csv('pres_ad_whisptranscripts_tsv/' + vid_fname.split('.')[0]+'.tsv', sep='\t')

            segment_starts = tsv['start'].values
            segment_ends = tsv['end'].values
            segment_middles = [ int(segment_starts[ii] + (segment_ends[ii] - segment_starts[ii])/2.0)  for ii in range(len(segment_starts))]

            # If we already finished all of the images then continue
            if os.path.isfile( 'keyframes_speechcentered/' + str(vid_fname.split('.')[0]) + "_" + str(segment_middles[-1]) + ".jpg" ) :
                print('\n\ncontinuing bc found this last file for this vid: ',  'keyframes_speechcentered/' + str(vid_fname.split('.')[0]) + "_" + str(segment_middles[-1]) + ".jpg" )
                continue

            for fidx, frame_sample_time in enumerate(segment_middles):
                if (frame_sample_time > metadata_df['DURATION'].values[idx]*1000.):
                    continue
                
                image_output_fpath = 'keyframes_speechcentered/' + str(vid_fname.split('.')[0]) + "_" + str(frame_sample_time) + ".jpg"
                
                # ffmpeg -ss 12 -i P-1026-41628.mp4 -frames:v 1 testframe.jpg
                # print('saving:  ' + image_output_fpath)
                subprocess.run(['ffmpeg', '-ss', str(frame_sample_time/1000.),  '-i',  local_vid_fpath, '-frames:v', '1', image_output_fpath, '-y'] )

        except:
            print('ERROR-opening '+ 'pres_ad_whisptranscripts_tsv/' + vid_fname.split('.')[0]+'.tsv')


