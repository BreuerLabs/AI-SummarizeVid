import os
os.environ["NUMEXPR_MAX_THREADS"]="272"

import openai 
import numpy as np
import pandas as pd 
from datetime import datetime, date
from time import sleep
import base64
import glob
import json
import os
from time import sleep

from mpi4py import MPI


"""
This script saves a still frame at evenly time-spaced intervals from each ad video
"""

MY_OPENAI_API_KEY = "Replace-With-Your-API-Key"  # REPLACE THIS LINE WITH YOUR OpenAPI Key

# APPLY WORKFLOW TO PROCESS SPEECH SEGMENT KEYFRAMES OR REGULAR INTERVAL KEYFRAMES?
# DIRECTORY_SUFFIX = 'speechcentered'
DIRECTORY_SUFFIX = 'regintervals'




openai.api_key = MY_OPENAI_API_KEY
METADATA_FNAME = 'METADATA.csv'

input_directory = 'keyframes_'+DIRECTORY_SUFFIX
output_directory = 'GPT_frame_descriptions_'+DIRECTORY_SUFFIX
# GPT_frame_descriptions_speechcentered
# GPT_frame_descriptions_regintervals


def send_frame_to_gpt(this_ad_frame, ELECTION_YEAR, PARTY, CANDIDATE, TRANSCRIPT):

    prompt = 'Describe what is depicted in this video frame in no more than 15 words. Do not state that the frame depicts a vintage advertisement, and do not comment on the image quality. If the image includes text, then state that it includes text and also include a summary of the text that is shown. For context, this video frame is a still taken from an advertisement for the '+ ELECTION_YEAR +' presidential campaign of ' + PARTY +' ' + CANDIDATE +'. The transcript of the entire ad is:\n ' + TRANSCRIPT 
    if 'anti' in CANDIDATE:
        prompt = 'Describe what is depicted in this video frame in no more than 15 words. Do not state that the frame depicts a vintage advertisement, and do not comment on the image quality. If the image includes text, then state that it includes text and also include a summary of the text that is shown. For context, this video frame is a still taken from an advertisement for the '+ ELECTION_YEAR +' presidential election. This ad is anti-' + CANDIDATE  + 'and pro-' + PARTY +'. The transcript of the entire ad is:\n ' + TRANSCRIPT 
    print('\n\n', prompt,'\n')

    PROMPT_MESSAGES = {
        "role": "user",
        "content": [prompt, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{this_ad_frame}"}}],
    }
    parameters = {
        "model": "gpt-4-vision-preview",
        "messages": [PROMPT_MESSAGES],
        # "api_key": os.environ["GPT_API_KEY"],
        # "response_format": {"type": "json_object"},  # Added response format
        # "headers": {"Openai-Version": "2020-11-07"},  # THIS IS WHERE Organization can go
        "max_tokens": 1000,
    }
    result = openai.chat.completions.create(**parameters)
    return result.choices[0].message.content



if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    print(rank, size)

    print('\n\nWorking on', DIRECTORY_SUFFIX, 'keyframes. CHANGE THIS IN THE SCRIPT to switch speech-centered or reg. intervals\n\n')
    sleep(3)

    if MY_OPENAI_API_KEY == "Replace-With-Your-API-Key": # LEAVE THIS ALONE (it just checks that you actually replaced the line above!)
      raise Exception("Add your own OpenAI API key") 

    # Initialize output storage directory if it doesn't exist
    if rank == 0:
        if not os.path.exists(output_directory): 
            os.makedirs(output_directory) 

    sleep(rank*0.2) # Avoid rate limit issue that arises when all procs make first API query simultaneously.

    metadata_df = pd.read_csv(METADATA_FNAME)

    already_donebyGPT_frames = glob.glob(output_directory+'/*.txt')
    tot_num_frames_to_do = len(glob.glob(input_directory+'/*'))
    num_frames_left_to_do = tot_num_frames_to_do - len(already_donebyGPT_frames)

    # Parallel split here
    proc_time0 = datetime.now()
    indices = list(range(len(metadata_df)))
    np.random.shuffle(indices) # randomly reshuffle these to better load balance across processors
    local_mastercsv_idx_split = np.array_split(indices, size)[rank]  # Each proc gets a list of CSV row indices we want to process

    totcount_of_frames_processed_thisproc = 0
    already_done = 0
    errors_thisprocessor = [] # storage for any errors

    for local_count, idx in enumerate(local_mastercsv_idx_split):
        if local_count>1:
            proc_elapsed_min = (datetime.now()-proc_time0).total_seconds()/60.
            print('\nrank', rank, 'starting CSV row', idx, 'which is local workload', local_count, 'of', len(local_mastercsv_idx_split), 'in', proc_elapsed_min, 'min;', 
                    proc_elapsed_min * float(len(local_mastercsv_idx_split)-local_count)/float(local_count), 'mins remain')

        inferred_end = metadata_df['DURATION'].values[idx]  # These are now trimmed videos and we are including scene...

        vid_fname = metadata_df['FILENAME'].values[idx]
        local_vid_fpath = 'PRES_AD_VIDEOS/' + vid_fname

        PARTY =  metadata_df['PARTY'].values[idx] 
        ELECTION_YEAR = str( metadata_df['ELECTION'].values[idx] )
        # print("metadata_df['FIRST_NAME'].values[idx]", metadata_df['FIRST_NAME'].values[idx], "metadata_df['LAST_NAME'].values[idx]", metadata_df['LAST_NAME'].values[idx])
        lastname = metadata_df['LAST_NAME'].values[idx] if not pd.isnull(metadata_df['LAST_NAME'].values[idx]) else ''
        firstname = metadata_df['FIRST_NAME'].values[idx] if not pd.isnull(metadata_df['FIRST_NAME'].values[idx]) else ''
        CANDIDATE = firstname + ' ' + lastname


        try:  # Handle openAPI errors and also handle case where you are only computing on subset of videos

            with open('pres_ad_whisptranscripts_txt/' + vid_fname +'.txt', "r") as text_file:
                TRANSCRIPT = text_file.read()

                if pd.isnull(TRANSCRIPT):
                    TRANSCRIPT = 'null, as no words are spoken in the ad'

            for this_frame_fpath in glob.glob(input_directory+'/'+vid_fname.split('.')[0] + '*'):
                totcount_of_frames_processed_thisproc += 1

                if output_directory+'/'+this_frame_fpath.split('/')[-1]+'.txt' in already_donebyGPT_frames:
                    already_done +=1
                    continue

                with open(this_frame_fpath, "rb") as tmp:
                    this_ad_frame_encoded = base64.b64encode(tmp.read()).decode("utf-8")

                time0 = datetime.now()
                result = send_frame_to_gpt(this_ad_frame_encoded, ELECTION_YEAR, PARTY, CANDIDATE, TRANSCRIPT)

                with open(output_directory+'/'+this_frame_fpath.split('/')[-1] + '.txt', 'w') as outfile:
                    outfile.write(result)
                print(this_frame_fpath, result, (datetime.now() - time0).total_seconds(), 
                    'local workload ', local_count, 'of', len(local_mastercsv_idx_split))
                SUCCESS = True
                    
        except Exception as e:
            print('\nError on', vid_fname, e)
            errors_thisprocessor.append({vid_fname: e})

    print('rank', rank, 'attempted to describe a total of', 
        totcount_of_frames_processed_thisproc, 'video stills. already done OF THESE=', already_done)





