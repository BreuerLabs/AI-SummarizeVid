


# Code for "Using AI to Transcribe \& Summarize a New Dataset of US Presidential Campaign TV Ad Videos, 1952-2012"


This code library automates the process of producing an AI-generated summary of a video, and applies this process to generate summaries of 9,707 historical US presidential campaign TV ads.

###Workflow overview:


###Parallelization
We design our codebase to accommodate even very large-scale applications (including those that are orders of magnitude larger than the project described here) by using the MPI parallelization standard via *openMPI*  and the *MPI4py* python module. Specifically, we note that the workflow described above is embarrassingly parallelizable at the level of videos.

**NOTE:** New users should ensure that *openMPI* is installed on their machines, then install *mpi4py*. 

**RUNNING A SCRIPT IN PARALLEL should be accomplished via the command (for e.g. 50 processors):**
     
     mpirun -np 50 python step4_summarize_vids_parallel.py



###Step 1: Transcription and transcript segmentation

We conduct automated transcription and transcript segmentation using the largest and most performant version of OpenAI's LLM-based Whisper transcription model: *whisper-large-v3*. This model improves upon a previous version (*v2*) that already obtained transcription accuracy within a fraction of a percent of professional human transcribers across a variety of text benchmarks in terms of word error rates. 

Transcription with Whisper returns two outputs: the video transcripts, and the segmentation of the transcript into short phrases that are separated by a natural pause in the speaker's voice (or a change in the person speaking).

###Step 2: Video key frame extraction

Our second task is to extract an ordered set of keyframes (i.e. images of video frames) from each video that are *comprehensive* in terms of reflecting each video's visual contents and progression of imagery. More specifically, we seek a time-ordered set of frames that contains all of the important visual contents of the ad. 

We accomplish this via two complementary strategies. First, we determine when important images are shown according to its narrator or speaker, per the transcription segments detected in **Step 1** above. Specifically, for each video, we extract a frame corresponding to the central moment of each speech segment. Second, we also extract a `transcription-agnostic' set of video frames at regular $3$-second intervals. We then merge this set with the transcription-directed video frames described above.

###Step 3: Obtaining video key frame descriptions

We generate a brief summary of each video keyframe by submitting it to a multimodal LLM: *GPT-4-vision*, accompanied by a custom prompt that provides context using the ad metadata. Specifically, we submit the following prompt for each keyframe:

###Step 4: Video summarization
We generate each ad summary by querying GPT using a customized summarization prompt that provides (1) the ad transcript generated in **Step 1**; (2) the time-ordered set of approximately 20 descriptions of video imagery generated in **Step 3** above including the merged speech-segment-based key frames and regular interval frames (merged by ascending timestamps); and (3) a contextual description of the ad that contains relevant ad metadata. 


