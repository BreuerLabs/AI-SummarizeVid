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

## NOTE: This script requires ffmpeg


METADATA_FNAME = 'METADATA.csv'


filepaths_transcripts_local = glob.glob('pres_trimmed_inclscene_whisptrans_largev3_json/*.json')
transcribed_videos_local = [x.split('/')[-1].split('.')[0] for x in filepaths_transcripts_local]


if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    vid_count = 0
    metadata_df = pd.read_csv(METADATA_FNAME)

    # Each processor gets a list of CSV row indices we want to process in parallel
    for idx in np.array_split(list(range(len(metadata_df))), size)[rank]:
        
        vid_fpath = metadata_df['vid_fpath_new'].values[idx]
        if not pd.isnull(metadata_df['LOCATION'].values[idx]):
            vid_fpath = metadata_df['LOCATION'].values[idx] # for some videos we need to use old file because new one is corrupted, and some are also in the missing folder bc they forgot.

        local_vid_fname = 'pres_trimmed_incl_scene/' + vid_fpath.split('/')[-1].split('.')[0]+'.mp4'


        try:
            tsv = pd.read_csv('pres_trimmed_inclscene_whisptrans_largev3_tsv/' + vid_fpath.split('/')[-1].split('.')[0]+'.tsv', sep='\t')

            segment_starts = tsv['start'].values
            segment_ends = tsv['end'].values
            segment_middles = [ int(segment_starts[ii] + (segment_ends[ii] - segment_starts[ii])/2.0)  for ii in range(len(segment_starts))]

            # If we already finished all of the images then continue
            if os.path.isfile( 'pres_trimmed_inclscene_whisper_segment_centerframes_largev3/' + str(vid_fpath.split('/')[-1].split('.')[0]) + "_" + str(segment_middles[-1]) + ".jpg" ) :
                print('\n\ncontinuing bc found this last file for this vid: ',  'pres_trimmed_inclscene_whisper_segment_centerframes_largev3/' + str(vid_fpath.split('/')[-1].split('.')[0]) + "_" + str(segment_middles[-1]) + ".jpg" )
                continue

            for fidx, frame_sample_time in enumerate(segment_middles):
                if (frame_sample_time > metadata_df['duration_inferred_incl_scene'].values[idx]*1000.):
                    continue
                
                image_output_fpath = 'pres_trimmed_inclscene_whisper_segment_centerframes_largev3/' + str(vid_fpath.split('/')[-1].split('.')[0]) + "_" + str(frame_sample_time) + ".jpg"
                
                # ffmpeg -ss 12 -i P-1026-41628.mp4 -frames:v 1 testframe.jpg
                # print('saving:  ' + image_output_fpath)
                subprocess.run(['ffmpeg', '-ss', str(frame_sample_time/1000.),  '-i',  local_vid_fname, '-frames:v', '1', image_output_fpath, '-y'] )

        except:
            print('ERROR-opening '+ 'pres_trimmed_inclscene_whisptrans_largev3_tsv/' + vid_fpath.split('/')[-1].split('.')[0]+'.tsv')


