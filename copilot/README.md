# Copilot for therapy session
This section is part of the repository Therapy Session Copilot (https://github.com/fsi-hack4autism/therapy-session-copilot), hosted as a part of FSI Hackathon for Autism (https://github.com/fsi-hack4autism).

* Focus is on retrieving data using a copilot
  * This module will specifically look for pre-designed triggers - emotional (frustration, accomplishment, etc.), or physical (completion of task, eye contact, etc.)
  * The objective is to track progress along specific markers
  * The copilot will assist through various interfaces - summary reports, chatbots, images & screenshots, video snippets, etc.


# 2025 Case Overview
The 2025 use case focused on two main aspects:

1. Visual Stimming Analysis: Searching for indicators of specific stemming behavior from an uploaded therapy session recording.
1. Transcript Analysis: Searching for specific auditory indicators across within the transcript of an uploaded video.

The final project provides an interface for a BCBA to upload a therapy session recording and perform either of the two analyses above, with the aid of a language model. 


# Tech Stack
A high level overview of the tech stack is provided below:

**All code is written in python**

* Front End
    * Streamlit (for demo purposes)
* Backend
    * Azure Services
        * ChatGPT 4/4o model deployments, API Version "2024-12-01-preview" (for visual stimming analysis and transcript analysis, respectively)
        * Azure Cognitive Services STT Fast Transcription, API Version "2024-11-15" (for transcript analysis, STT)
    * Other Noteable Resources:
        * MoviePy (for extraction of audio file from uploaded videos)
        * OpenCV2 (for extraction of frames from uploaded videos)
 

# How it Works

## 1. Visual Stimming Analysis
The visual stimming analysis follows the below steps:

1. OpenCV is used to process the uploaded video to a series of image files
1. The image files are passed in batches to GPT 4o model (due to model context limits), along with a system prompt. 
    * The system prompt tells the model to process the series of frames as images and determine if the patient exhibits any common stimming behaviors. 
    * In current demo, the model only analyzes common stimming behaviors. **This can be extended in the future to allow the user to ask the model to observe patient specific behaviors**
    * The model returns a json output that includes the behaviors observed and their approximate timestamps in the video
        * **This output could be stored in the future and used to analyze changes in patient behavior overtime**
1. The json output from above is passed to GPT 4 model, which provides a summary of the behaviors observed in the video to the analyst on the front end

## 2. Transcript Analysis
The transcript analysis follows the below steps:

1. MoviePy is used to extract a .wav file from the uploaded video
1. The .wav file is passed to Azure Cognitive Services STT Transcription model, which provides a transcript of the audio file in json format that includes timestamps for words and phrases 
    * **This performs diarization, so speakers can be distinguished in the transcript output**
1. The transcript json output above is used to provide a cleaned dialogue for the analyst to review on the frontend
1. The transcript json output from above is passed to the GPT 4 model as context, along with a system prompt that instructs the model to use the transcript to answer user natural language queries provided by the user in the frontend


# Limitations and Potential Future Enhancements
Some limitations and potential enhancements are outlined below:

**Limitation**: Image and Audio are processed separately, as a video processing model was not accessible in the Azure foundry for our resource group. As a result, some context that relies on the interplay of different modalities is lost.
**Suggested Enhancement**: Use a multi-modal model/service such as the Content Understanding service in AI Foundry to process videos directly.

**Limitation**: Data is not persisted from the analyst sessions, as access to blob storage was causing issues that could not be resolved timely.
**Suggested Enhancement**: Persist the model outputs to use for patient trend analysis, etc.

**Limitation**: Analyses are retrospective.
**Suggested Enhancement**: Adapt the code to allow for real time data feeds and analytics

**Limitation**: GPT 4 struggles with identifying visual stimming cues from a series of images.
**Suggested Enhancement**: Further engineer the system prompt used in the current version or test different models such as the Content Understanding Service discussed above.

**Limitation**: Transcript analysis does not include acoustics.
**Suggested Enhancement**: Integrate acoustic analysis to allow for refined sentiment analysis on audio files.

**Limitation**: The analyses are not refined for specific patients.
**Suggested Enhancement**: Potentially create derivative model deployments that are patient specific and are updated overtime based on analyst feedback and persisted data.






 
    
