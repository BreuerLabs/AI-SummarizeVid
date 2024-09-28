import os
#from openai import OpenAI
os.environ["NUMEXPR_MAX_THREADS"]="272"

import openai 
import numpy as np
import pandas as pd # only necessary to save csv of analyzed solution objective values
from datetime import datetime, date
from time import sleep
import base64
import glob
import json

from mpi4py import MPI

# from openai import OpenAI
# scp -r GPT_videoframesummaries_v6_manuallabelset_v3_regularspaced.py breuer@34.145.117.67:~/GPT_videoframesummaries_v6_manuallabelset_v3_regularspaced.py


def send_frame_to_gpt(this_ad_frame, ELECTION_YEAR, PARTY, CANDIDATE, TRANSCRIPT):
    #previous_frames_result_thisad_str = ' '.join(previous_frames_result_thisad_list)

    # prompt = 'Describe what is depicted in this video frame in no more than 10 words. \
    #             For context, this video frame is a still taken from an advertisement \
    #             for the '+ ELECTION_YEAR +' presidential campaign of ' + PARTY +' ' + CANDIDATE +'. \
    #             Before this video frame appears, the ad depicts the following:' + str(previous_frames_result_thisad_str) + \
    #             ' The transcript of the entire ad is: ' + TRANSCRIPT #+ \
    #             #' This frame was taken when the following line of the transcript is heard: ' + SEGMENT 

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


adam_API_key = "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"
openai.api_key = adam_API_key
# MASTERCSV_FNAME = 'MASTER_CSV_01252023_based12062022_WITH_INFERRED_INTROOUTRO_V5_2023-10-28.csv'
# MANUALLABELERCSV_FNAME = 'DONTSHARE_manual_check_introoutro_with_key_may10_final.csv'
# manual_transc_fname  = 'transcriptions_manual_feb2_2024_v2.csv' #v2 means i sublime saved it as utf-8 bc they had weird chars
# csv_fname = 'validation_DONTSHARE_manual_check_introoutro_with_key_may10_final_with_batch.csv'
# whisper_directory = 'pres_trimmed_inclscene_whisptrans_largev3_json'
# master_csv = 'MASTER_CSV_01252023_based12062022_WITH_INFERRED_INTROOUTRO_V5_2023-1-11.csv'
MASTERCSV_FNAME = 'MASTER_CSV_01252023_based12062022_WITH_INFERRED_INTROOUTRO_V5_2023-1-11_withWHISPERlargev3.csv'

DO_ONLY_MANUAL_VALIDATION_SET = True

# # organization_id = org-G0G79DbBsTqqeOCIVO99uKJh


if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    print(rank, size)

    sleep(rank*0.2) # Avoid rate limit issue that arises when all procs make first API query simultaneously.


    # mastercsv_df = pd.read_csv(MASTERCSV_FNAME)
    # # whisper_files = glob.glob(whisper_directory)
    # # manual_transc = pd.read_csv(manual_transc_fname, engine='python') #they have weird character encodings and this fixes it
    # manual_transc = pd.read_csv(manual_transc_fname, encoding='utf-8') #they have weird character encodings and this fixes it
    # manual_transc['have_manual_transcription'] = 1 #they have weird character encodings and this fixes it
    # # csv = pd.read_csv(csv_fname)
    # # print('len csv', len(csv), "len_manual_transc", len(manual_transc))
    # joined = manual_transc.merge(mastercsv_df, how='outer', on='COMPONENT_ID')
    # joined['have_manual_transcription'] = joined['have_manual_transcription'].fillna(0)

    # print('len mastercsv', len(mastercsv_df), 'len joined', len(joined), "len_manual_transc", len(manual_transc))
    # ghghgh
    # # components_in_csv = joined['COMPONENT_ID'].values
    # # components_in_manual = manual_transc['COMPONENT_ID'].values
    # # id_in_csv_not_manual = set(components_in_csv).difference(set(components_in_manual))
    # # id_in_manual_not_csv = set(components_in_manual).difference(set(components_in_csv))
    # # print('id_in_manual_not_csv', id_in_manual_not_csv, 'len(id_in_manual_not_csv)', len(id_in_manual_not_csv))

    # LOCATION = joined['LOCATION'].values
    # for idx, vid_fpath in enumerate( joined['vid_fpath_new'].values ):
    #     if not pd.isnull(LOCATION[idx]):
    #         vid_fpath = LOCATION[idx] # for some videos we need to use old file because new one is corrupted, and some are also in the missing folder bc they forgot.
    #     vid_fname = vid_fpath.split('/')[-1].split('.')[0] 
    #     whisper_vid_file = whisper_directory + '/' + vid_fname + '.json'
    #     try:
    #         with open(whisper_vid_file) as f:
    #             whisper_json = json.load(f)
    #             vid_transcript = whisper_json['text']
    #             whisper_transcripts.append(vid_transcript)
    #     except:
    #         whisper_transcripts.append('')
    #         print('Issues with '  + vid_fname + '.json')
    #         errors.append(vid_fname)
    # joined['whisper_largev3'] = whisper_transcripts
    # joined_keepcols = joined[ list(manual_transc.columns) + ['whisper_largev3'] + ['LOCATION', 'vid_fpath_new'] ]
    # joined_keepcols.to_csv('manual_transc_fname_withwhisperlargev3_inner_cols.csv', index=False)
    # print('errors\n', errors)





    mastercsv_df = pd.read_csv(MASTERCSV_FNAME)
    # manuallabel_subset_df = mastercsv_df.loc[mastercsv_df['have_manual_transcription']==1]
    manuallabel_subset_df = mastercsv_df  # placeholder for subsetting


    # manuallabelcsv_df = pd.read_csv(MANUALLABELERCSV_FNAME)
    # already_donebyGPT_frames = glob.glob('GPT_frame_descriptions/*.txt')
    # tot_num_frames_to_do = len(glob.glob('pres_trimmed_inclscene_whisper_segment_centerframes_largev3/*'))
    already_donebyGPT_frames = glob.glob('GPT_frame_descriptions_regularspaced/*.txt')
    tot_num_frames_to_do = len(glob.glob('pres_trimmed_inclscene_whisper_segment_centerframes_regularspaced/*'))
    num_frames_left_to_do = tot_num_frames_to_do - len(already_donebyGPT_frames)

    # Parallel split here
    # for idx in list(range(len(mastercsv_df))):
    proc_time0 = datetime.now()

    # local_mastercsv_idx_split = np.array_split(list(range(len(mastercsv_df))), size)[rank]
    # local_mastercsv_idx_split = np.array_split(list(range(len(manuallabel_subset_df))), size)[rank]  # Each proc gets a list of CSV row indices we want to process
    indices = list(range(len(manuallabel_subset_df)))
    np.random.shuffle(indices) # randomly reshuffle these to better load balance across processors
    local_mastercsv_idx_split = np.array_split(indices, size)[rank]  # Each proc gets a list of CSV row indices we want to process



    totcount_of_frames_processed_thisproc = 0
    already_done = 0
    for local_count, idx in enumerate(local_mastercsv_idx_split):
        if local_count>1:
            proc_elapsed_min = (datetime.now()-proc_time0).total_seconds()/60.
            print('\nrank', rank, 'starting CSV row', idx, 'which is local workload', local_count, 'of', len(local_mastercsv_idx_split), 'in', proc_elapsed_min, 'min;', 
                    proc_elapsed_min * float(len(local_mastercsv_idx_split)-local_count)/float(local_count), 'mins remain')

        #previous_frames_result_thisad_list = []
        inferred_end = manuallabel_subset_df['duration_inferred_incl_scene'].values[idx]  # These are now trimmed videos and we are including scene...
        vid_fpath = manuallabel_subset_df['vid_fpath_new'].values[idx]


        if not pd.isnull(manuallabel_subset_df['LOCATION'].values[idx]):
            vid_fpath = manuallabel_subset_df['LOCATION'].values[idx] # for some videos we need to use old file because new one is corrupted, and some are also in the missing folder bc they forgot.
        local_vid_fname = vid_fpath.split('/')[-1].split('.')[0]+'.mp4'
        local_vid_fpath = 'pres_trimmed_incl_scene/' + vid_fpath

        PARTY =  manuallabel_subset_df['PARTY'].values[idx] 
        ELECTION_YEAR = str( manuallabel_subset_df['ELECTION_YEAR'].values[idx] )
        print("manuallabel_subset_df['FIRST_NAME'].values[idx]", manuallabel_subset_df['FIRST_NAME'].values[idx], "manuallabel_subset_df['LAST_NAME'].values[idx]", manuallabel_subset_df['LAST_NAME'].values[idx])
        lastname = manuallabel_subset_df['LAST_NAME'].values[idx] if not pd.isnull(manuallabel_subset_df['LAST_NAME'].values[idx]) else ''
        firstname = manuallabel_subset_df['FIRST_NAME'].values[idx] if not pd.isnull(manuallabel_subset_df['FIRST_NAME'].values[idx]) else ''
        CANDIDATE = firstname + ' ' + lastname
        TRANSCRIPT = manuallabel_subset_df['whisper_largev3'].values[idx]

        # print('CANDIDATE', CANDIDATE)
        # print('TRANSCRIPT', TRANSCRIPT)
        # print('ELECTION_YEAR', ELECTION_YEAR)
        # print('local_vid_fpath', local_vid_fpath)
        
        # with open( 'pres_trimmed_inclscene_whisptrans_largev3_json/' + vid_fpath.split('/')[-1].split('.')[0]+'.json' ) as f:
        #     d = json.load(f)
        #     TRANSCRIPT = d['text']
        if pd.isnull(TRANSCRIPT):
            TRANSCRIPT = 'null, as no words are spoken in the ad'

        for this_frame_fpath in glob.glob('pres_trimmed_inclscene_whisper_segment_centerframes_regularspaced/'+local_vid_fname.split('.')[0] + '*'):
            totcount_of_frames_processed_thisproc += 1

            if 'GPT_frame_descriptions_regularspaced/'+this_frame_fpath.split('/')[-1]+'.txt' in already_donebyGPT_frames:
                already_done +=1
                continue

            with open(this_frame_fpath, "rb") as tmp:
                this_ad_frame_encoded = base64.b64encode(tmp.read()).decode("utf-8")

            try:
                time0 = datetime.now()
                result = send_frame_to_gpt(this_ad_frame_encoded, ELECTION_YEAR, PARTY, CANDIDATE, TRANSCRIPT)
                # print(result)
                with open('GPT_frame_descriptions_regularspaced/'+this_frame_fpath.split('/')[-1] + '.txt', 'w') as outfile:
                    outfile.write(result)
                print(this_frame_fpath, result, (datetime.now() - time0).total_seconds(), 'local workload ', local_count, 'of', len(local_mastercsv_idx_split))
                SUCCESS = True
                


            except Exception as e:
                print('\nError on', this_frame_fpath.split('/')[-1], e)
                # print('result', result)


    print('rank', rank, 'attempted to describe a total of', totcount_of_frames_processed_thisproc, 'video stills. already done OF THESE=', already_done)




