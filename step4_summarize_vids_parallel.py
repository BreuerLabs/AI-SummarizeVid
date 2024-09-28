import os
os.environ["NUMEXPR_MAX_THREADS"]="272"

import openai 
import numpy as np
import pandas as pd 
from datetime import datetime, date
from time import sleep
import glob
from mpi4py import MPI

"""
This script summarizes videos in parallel.
"""


MY_OPENAI_API_KEY = "Replace-With-Your-API-Key"
if MY_OPENAI_API_KEY == "Replace-With-Your-API-Key":
  raise Exception("Add your own OpenAI API key") 



def gpt_summarize_ad(ELECTION_YEAR, PARTY, CANDIDATE, TRANSCRIPT, FRAMETIMES, FRAMEDESCRIPTIONS, response_wordcount=50):

    FRAMETIMES_argsort = np.argsort(FRAMETIMES)

    FRAMEDESCRIPTIONS_timesorted = np.asarray(FRAMEDESCRIPTIONS)[FRAMETIMES_argsort]

    prompt = 'Provide a '+str(response_wordcount)+' word summary of a political television ad for the academic community. Your summary should not exceed '+str(response_wordcount)+' words. For context, this ad was for the '+ ELECTION_YEAR +' presidential campaign of ' + PARTY +' candidate ' + CANDIDATE +'. The transcript of the entire ad is:\n' + TRANSCRIPT +'\n\nThe ad video depicts a set of scenes that can be described as follows:\n\n' + '\n\n'.join([str(idx+1) + ': ' + segment for idx, segment in enumerate(FRAMEDESCRIPTIONS_timesorted)])
    if 'anti' in CANDIDATE:
        prompt = 'Provide a '+str(response_wordcount)+' word summary of a political television ad for the academic community. Your summary should not exceed '+str(response_wordcount)+' words. For context, this ad was for the '+ ELECTION_YEAR +' presidential election. This ad is anti ' + CANDIDATE  + 'and pro-' + PARTY +'. The transcript of the entire ad is:\n' + TRANSCRIPT +'\n\nThe ad video depicts a set of scenes that can be described as follows:\n\n' + '\n\n'.join([str(idx+1) + ': ' + segment for idx, segment in enumerate(FRAMEDESCRIPTIONS_timesorted)])
    print('\n\n\n', prompt,'\n')

    PROMPT_MESSAGES = {
        "role": "user",
        "content": prompt
    }
    parameters = {
        "model": "gpt-4",#-vision-preview",
        "messages": [PROMPT_MESSAGES],
        # "headers": {"Openai-Version": "2020-11-07"},  # THIS IS WHERE Organization can go
        "max_tokens": 1000,
    }
    result = openai.chat.completions.create(**parameters)
    return result.choices[0].message.content


openai.api_key = MY_OPENAI_API_KEY

METADATA_FNAME = 'METADATA.csv'

already_summarized_videos = glob.glob('GPT_adcontent_descriptions_segplusregspaced/*.txt')


if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    print(rank, size)

    metadata_df = pd.read_csv(METADATA_FNAME)
    manuallabel_subset_df = metadata_df  # placeholder for subsetting

    proc_time0 = datetime.now()
    already_done = 0
    local_errors=[]

    indices = list(range(len(manuallabel_subset_df)))
    np.random.shuffle(indices) # randomly reshuffle these to better load balance across processors
    local_mastercsv_idx_split = np.array_split(indices, size)[rank]  # Each proc gets a list of CSV row indices we want to process


    totcount_of_frames_processed_thisproc = 0
    already_done = 0
    for local_count, idx in enumerate(local_mastercsv_idx_split):
        if local_count>1:
            proc_elapsed_min = (datetime.now()-proc_time0).total_seconds()/60.
            print('\nrank', rank, 'starting CSV row', idx, 'which is local workload', local_count+1, 
                'of', len(local_mastercsv_idx_split), 'in', proc_elapsed_min, 'min;', 
                proc_elapsed_min * float(len(local_mastercsv_idx_split)-local_count)/float(local_count), 'mins remain')

        #previous_frames_result_thisad_list = []
        vid_fpath = manuallabel_subset_df['vid_fpath_new'].values[idx]
        if not pd.isnull(manuallabel_subset_df['LOCATION'].values[idx]):
            vid_fpath = manuallabel_subset_df['LOCATION'].values[idx] # for some videos we need to use old file because new one is corrupted, and some are also in the missing folder bc they forgot.
        local_vid_fname = vid_fpath.split('/')[-1].split('.')[0]+'.mp4'
        local_vid_fpath = 'pres_trimmed_incl_scene/' + vid_fpath

        if 'GPT_adcontent_descriptions_segplusregspaced/'+local_vid_fname + '.txt' in already_summarized_videos:
            already_done += 1
            continue


        PARTY =  manuallabel_subset_df['PARTY'].values[idx] 
        ELECTION_YEAR = str( manuallabel_subset_df['ELECTION_YEAR'].values[idx] )

        lastname = manuallabel_subset_df['LAST_NAME'].values[idx] if not pd.isnull(manuallabel_subset_df['LAST_NAME'].values[idx]) else ''
        firstname = manuallabel_subset_df['FIRST_NAME'].values[idx] if not pd.isnull(manuallabel_subset_df['FIRST_NAME'].values[idx]) else ''
        CANDIDATE = firstname + ' ' + lastname
        TRANSCRIPT = manuallabel_subset_df['whisper_largev3'].values[idx]

        if pd.isnull(TRANSCRIPT):
            TRANSCRIPT = 'null, as no words are spoken in the ad'

        FRAMETIMES_SEGMENTS = []
        FRAMEDESCRIPTIONS_SEGMENTS = []
        for this_framedescription_fpath in glob.glob('GPT_frame_descriptions/'+local_vid_fname.split('.')[0] + '*'):
            frametime = float( this_framedescription_fpath.split('_')[-1].split('.')[0] )
            FRAMETIMES_SEGMENTS.append(frametime)
            with open(this_framedescription_fpath, 'r') as tmp:
                description = tmp.read()
                FRAMEDESCRIPTIONS_SEGMENTS.append(description)

        FRAMETIMES_REGSPACED = []
        FRAMEDESCRIPTIONS_REGSPACED = []
        for this_framedescription_fpath in glob.glob('GPT_frame_descriptions_regularspaced/'+local_vid_fname.split('.')[0] + '*'):
            frametime = float( this_framedescription_fpath.split('_')[-1].split('.')[0] )
            FRAMETIMES_REGSPACED.append(frametime)
            with open(this_framedescription_fpath, 'r') as tmp:
                description = tmp.read()
                FRAMEDESCRIPTIONS_REGSPACED.append(description)
            
        FRAMETIMES = FRAMETIMES_SEGMENTS + FRAMETIMES_REGSPACED
        FRAMEDESCRIPTIONS = FRAMEDESCRIPTIONS_SEGMENTS + FRAMEDESCRIPTIONS_REGSPACED

        try:
            time0 = datetime.now()
            result = gpt_summarize_ad(ELECTION_YEAR, PARTY, CANDIDATE, TRANSCRIPT, FRAMETIMES, FRAMEDESCRIPTIONS)
            # print('RESULT:\n', result)

            if not len(result):
                raise Exception("Empty result from OpenAI!") 

            with open('GPT_adcontent_descriptions_segplusregspaced/'+local_vid_fname + '.txt', 'w') as outfile:
                outfile.write(result)
            print('RESULT:\n', local_vid_fname, result, 
                'GPT Response time (sec):', (datetime.now() - time0).total_seconds())
            SUCCESS = True
            pass

        except Exception as e:
            print('\nError on', local_vid_fpath.split('/')[-1], e)
            local_errors.append(e, rank, local_vid_fpath)
            pass

    print(local_errors)
    print('rank', rank, 'attempted to describe a total of', 
        local_count+1, 'videos. Already done =', already_done)




