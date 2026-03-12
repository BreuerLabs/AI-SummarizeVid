import numpy as np
from datetime import datetime
import pandas as pd
from mpi4py import MPI
import subprocess
import whisper
from whisper.utils import get_writer
import glob
import os # create output storage directories


"""
This script whisper-transcribes videos in parallel.
"""

## NOTE: ad videos should be stored in directory called "PRES_AD_VIDEOS"

whispermodel = whisper.load_model("large-v3")

options = {
    'max_line_width': None,
    'max_line_count': None,
    'highlight_words': False
}


def get_video_duration_ms(video_path: str) -> int:
    """Return video duration in milliseconds from ffprobe."""
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            video_path,
        ],
        text=True,
    ).strip()
    return int(float(out) * 1000.0)


def trim_transcription_to_duration(
    transcription: dict,
    duration_ms: int,
    start_pad_ms: int = 250,
    end_pad_ms: int = 1500,
) -> tuple[dict, int]:
    """
    Drop/trim Whisper segments that run beyond true video duration.
    Returns (updated_transcription, dropped_segment_count).
    """
    segments = transcription.get("segments", [])
    kept_segments = []
    dropped = 0
    start_limit_ms = duration_ms + start_pad_ms
    end_drop_limit_ms = duration_ms + end_pad_ms

    for seg in segments:
        start_ms = int(float(seg.get("start", 0.0)) * 1000.0)
        end_ms = int(float(seg.get("end", 0.0)) * 1000.0)

        # Drop segments that clearly start after the video ends.
        if start_ms > start_limit_ms:
            dropped += 1
            continue

        # Also drop segments that run far past the end (hallucinated tails).
        if end_ms > end_drop_limit_ms:
            dropped += 1
            continue

        # Keep borderline segments but clamp their end to true duration.
        if end_ms > duration_ms:
            seg["end"] = duration_ms / 1000.0
        kept_segments.append(seg)

    transcription["segments"] = kept_segments
    transcription["text"] = " ".join(
        str(seg.get("text", "")).strip() for seg in kept_segments if str(seg.get("text", "")).strip()
    ).strip()
    return transcription, dropped

if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    time_start = datetime.now()
    error_files_thisproc = []
    error_msgs_thisproc = []
    vid_count = 0

    if rank == 0:  # Root processor does bookkeeping
        if not os.path.exists("PRES_AD_VIDEOS"): 
            raise Exception("Error: Videos should be stored in directory 'PRES_AD_VIDEOS'")
        # Create transcript storage directories if they don't already exist:
        if not os.path.exists("pres_ad_whisptranscripts_json"): 
            os.makedirs("pres_ad_whisptranscripts_json") 
        if not os.path.exists("pres_ad_whisptranscripts_tsv"): 
            os.makedirs("pres_ad_whisptranscripts_tsv") 
        if not os.path.exists("pres_ad_whisptranscripts_txt"):
            os.makedirs("pres_ad_whisptranscripts_txt")

    comm.Barrier()  # Ensure rank 0 finishes creating directories before all ranks proceed

    vidfilepaths_local = glob.glob('PRES_AD_VIDEOS/*.mp4')
    filepaths_transcripts_local = glob.glob('pres_ad_whisptranscripts_json/*.json')
    transcribed_videos_local = [os.path.basename(x).rsplit('.json', 1)[0] for x in filepaths_transcripts_local]
    if rank == 0:
        print('Local video count:', len(vidfilepaths_local))
        print('Local transcript count:', len(transcribed_videos_local))

    all_vid_fpaths = [os.path.basename(vid_fpath) for vid_fpath in vidfilepaths_local]
    all_vid_fpaths_LEFTTODO = list(set(all_vid_fpaths).difference(transcribed_videos_local))

    this_proc_left_to_do = np.array_split(all_vid_fpaths_LEFTTODO, size)[rank]
 
    for idx, vid_fpath_id in enumerate( this_proc_left_to_do ): 
        vid_fpath = 'PRES_AD_VIDEOS/' + vid_fpath_id 

        try:
            duration_ms = get_video_duration_ms(vid_fpath)
            transcription = whispermodel.transcribe(vid_fpath, fp16=False)
            transcription, n_dropped = trim_transcription_to_duration(transcription, duration_ms=duration_ms)
            if n_dropped:
                print('Trimmed', n_dropped, 'hallucinated tail segments from', vid_fpath_id)

            with open('pres_ad_whisptranscripts_txt/' + vid_fpath_id +'.txt', "w") as text_file:
                text_file.write(transcription['text'])

            # Occassionally whisper throws an arbitrary error, so we wrap this in a try
            write_error = False
            try:
                tsv_writer = get_writer("tsv", 'pres_ad_whisptranscripts_tsv')
                tsv_writer(transcription, vid_fpath_id +'.tsv', options)
                json_writer = get_writer("json", 'pres_ad_whisptranscripts_json')
                json_writer(transcription,  vid_fpath_id +'.json', options)
            except Exception as e:
                write_error = True
                print('ERROR saving transcript with file: '+ vid_fpath_id, 'note that transcript[text] is', transcription['text'], e)
                error_files_thisproc.append(vid_fpath_id)
                error_msgs_thisproc.append(str(e))
        except Exception as e:
            print('ERROR transcribing file: '+ vid_fpath_id, e)
            error_files_thisproc.append(vid_fpath_id)
            error_msgs_thisproc.append(str(e))
            continue

        if not write_error:
            vid_count += 1
        elapsed = (datetime.now()-time_start).total_seconds()
        print('\n\nRank', rank, 'Completed', vid_count, 'of', len(this_proc_left_to_do),\
                'elapsed:', elapsed//60, 'minutes','remaining time:', \
                    (elapsed/max(vid_count,1))*(len(this_proc_left_to_do) - vid_count)/60., 'minutes',
                'ERRORS:', error_files_thisproc, 'num errors', len(error_files_thisproc),'ErrorMessages', error_msgs_thisproc)
        
    error_messages = comm.gather(error_msgs_thisproc, root=0)
    error_files = comm.gather(error_files_thisproc, root=0)

    if rank == 0:
        print('\n\nerror messages:', error_messages)
        print('\n\nerror files:', error_files)
