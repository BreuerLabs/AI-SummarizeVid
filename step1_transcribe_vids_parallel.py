import numpy as np
from datetime import datetime
import pandas as pd
from mpi4py import MPI
import subprocess
import whisper
from whisper.utils import get_writer
import glob


"""
This script whisper-transcribes videos in parallel.
"""

whispermodel = whisper.load_model("large-v3")

vidfilepaths_local = glob.glob('pres_trimmed_incl_scene/*.mp4')
filepaths_transcripts_local = glob.glob('pres_trimmed_inclscene_whisptrans_largev3_json/*.json')
transcribed_videos_local = [x.split('/')[-1].split('.')[0] for x in filepaths_transcripts_local]
print('Local video count:', len(vidfilepaths_local))
print('Local transcript count:', len(transcribed_videos_local))

options = {
    'max_line_width': None,
    'max_line_count': None,
    'highlight_words': False
}

if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    time_start = datetime.now()
    error_files_thisproc = []
    error_msgs_thisproc = []
    vid_count = 0

    client = storage.Client()

    all_vid_localcopy_TRIMMEDname = [vid_fpath.split('/')[-1].split('.')[0] for vid_fpath in vidfilepaths_local]
    all_vid_localcopy_TRIMMEDname_LEFTTODO = list(set(all_vid_localcopy_TRIMMEDname).difference(transcribed_videos_local))

    this_proc_left_to_do = np.array_split(all_vid_localcopy_TRIMMEDname_LEFTTODO, size)[rank]
 
    for idx, vid_fpath_id in enumerate( this_proc_left_to_do ): 
        vid_fpath = 'pres_trimmed_incl_scene/' + vid_fpath_id + '.mp4'

        transcription = whispermodel.transcribe(vid_fpath, fp16=False)
        with open('pres_trimmed_inclscene_whisptrans_largev3_txt/' + vid_fpath_id +'.txt', "w") as text_file:
            text_file.write(transcription['text'])

        # Occassionally whisper throws an arbitrary error, so we wrap this in a try
        try: 
            tsv_writer = get_writer("tsv", 'pres_trimmed_inclscene_whisptrans_largev3_tsv')
            tsv_writer(transcription, vid_fpath_id +'.tsv', options)
            json_writer = get_writer("json", 'pres_trimmed_inclscene_whisptrans_largev3_json')
            json_writer(transcription,  vid_fpath_id +'.json', options)
        except:
            print('ERROR saving transcript with file: '+ vid_fpath_id, 'note that transcript[text] is', transcription['text'])

        vid_count += 1
        elapsed = (datetime.now()-time_start).total_seconds()
        print('\n\nRank', rank, 'Completed', vid_count, 'of', len(this_proc_left_to_do)/float(size),\
                'elapsed:', elapsed//60, 'minutes','remaining time:', (elapsed/vid_count)*(len(this_proc_left_to_do)/float(size) - vid_count)/60., 'minutes',
                'ERRORS:', error_files_thisproc, 'num errors', len(error_files_thisproc),'ErrorMessages', error_msgs_thisproc)
        
    error_messages = comm.gather(error_msgs_thisproc, root=0)
    error_files = comm.gather(error_files_thisproc, root=0)

    if rank == 0:
        print('\n\nerror messages:', error_messages)
        print('\n\nerror files:', error_files)


