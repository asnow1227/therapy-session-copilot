import streamlit as st
import cv2
import os
import base64
import requests
from moviepy import VideoFileClip
from openai import AzureOpenAI
import math
import json


def process_video(video_path, seconds_per_frame=1):
    base64Frames = []
    base_video_path, _ = os.path.splitext(video_path)

    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    frames_to_skip = int(fps * seconds_per_frame)
    curr_frame=0

    # Loop through the video and extract frames at specified sampling rate
    while curr_frame < total_frames - 1:
        video.set(cv2.CAP_PROP_POS_FRAMES, curr_frame)
        success, frame = video.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
        curr_frame += frames_to_skip
    video.release()

    # print(f"Extracted {len(base64Frames)} frames")
    return base64Frames

def process_audio(video_path, audio_file_path):
# Get Audio
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_file_path)
    video.close()
    audio.close()
    return open(audio_file_path, "rb")

def get_audio_transcription(audio_bytes):
    url = "https://usecase1hub1533117385.cognitiveservices.azure.com/speechtotext/transcriptions:transcribe?api-version=2024-11-15"
    headers = {
        "Ocp-Apim-Subscription-Key": "EtQkrbu2AazF9oNNHr7wZ0Vf7CSJTHwxvsqbiinQO9AHsjBHIEpoJQQJ99BDAC4f1cMXJ3w3AAAAACOG3E6M",
        "Accept": "application/json"
    }
    files = {
        "audio": audio_bytes,
        "definition": (None, '{"locales":["en-US"], "diarization": {"maxSpeakers": 4,"enabled": true}}', 'application/json')
    }
    response = requests.post(url, headers=headers, files=files)
    return response.json()

def get_script(audio_transcription):
    script = ""
    for phrase in audio_transcription["phrases"]:
        script += f"Speaker {phrase['speaker']}: {phrase['text']}\n\r"
        # script += f"\n\r"
    return script

def get_script_audio(audio_transcription):
    script_txt = ""
    for phrase in audio_transcription["phrases"]:
        script_txt += f"Speaker {phrase['speaker']}: {phrase['text']}\n\r"

    # add formatted timestamps for the video
    for phrase in audio_transcription["phrases"]:
        phrase["offsetSeconds"] = convert_milliseconds_to_minute_timestamps(phrase['offsetMilliseconds'])
    return json.dumps(audio_transcription["phrases"]), script_txt

def talk_to_chatbot(script, previous_messages, frame_start):
    system = """
    You are a behavioral analyst that focuses on therapy sessions for patients with autism.
    You will be provided a video recording of a therapy session.
    Your job is to analyze the video to determine if the patient displays any common "stimming"
    patterns. Common examples of stimming patterns include:

    Hand-flapping: Rapid movement of the hands, often seen when an individual is excited or agitated.
    Rocking: Body rocking back and forth while sitting or standing.
    Spinning: Turning in circles or spinning objects repetitively.
    Echolalia: Repetitive vocal sounds or phrases, often repeated immediately after hearing them.
    Tapping: Tapping hands or objects repeatedly.
    Visual Stimming: Staring at lights, moving fingers in front of the eyes, or watching objects spin.
    Chewing or Biting: Chewing on objects, clothing, or oneself.

    Here is the conversation that took place within the video:
    {script}

    Provide your output as an array of items whether each of these different patterns were, observed in the video and a summary of the patient's
    particular behavior corresponding to this pattern if it was observed, e.g.:

    [
      {
        "stimming_type": ...Example stimming pattern 1...
        "summary": ...Example summary 1...
      },
      {
        "stimming_type": ...Example stimming pattern 2...
        "summary": ...Example summary 2...
      }, ...
    ]

    Only provide your output as json per the abovementioned format, and nothing more.
    """.replace("{script}", script)


    endpoint = "https://usecase1hub1533117385.openai.azure.com/"
    deployment = "gpt-4"

    subscription_key = "EtQkrbu2AazF9oNNHr7wZ0Vf7CSJTHwxvsqbiinQO9AHsjBHIEpoJQQJ99BDAC4f1cMXJ3w3AAAAACOG3E6M"
    api_version = "2024-12-01-preview"

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=subscription_key,
    )

    messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": [
            *map(lambda x: {"type": "image_url",
                            "image_url": {"url": f'data:image/jpg{x[0]};base64,{x[1]}', "detail": "low"}},
                 enumerate(st.session_state.b64frames[frame_start:st.session_state.frame_end]))
            ],
        }
        ]

    # st.text(messages[0]["content"] + "\n\r")
    st.text(f"Processing Frames: {frame_start} to {st.session_state.frame_end} out of {len(st.session_state.b64frames)}")

    for message in previous_messages:
        messages.append(message)

    response = client.chat.completions.create(
        messages=messages,
        max_tokens=4096,
        temperature=0,
        top_p=1.0,
        model=deployment
    )
    return response.choices[0].message.content


def summarize_chatbot(previous_messages):
    system = """
    You are a behavioral analyst that focuses on therapy sessions for patients with autism.
    You will be provided a video recording of a therapy session.
    Your job is to analyze the video to determine if the patient displays any common "stimming"
    patterns. Common examples of stimming patterns include:

    Hand-flapping: Rapid movement of the hands, often seen when an individual is excited or agitated.
    Rocking: Body rocking back and forth while sitting or standing.
    Spinning: Turning in circles or spinning objects repetitively.
    Echolalia: Repetitive vocal sounds or phrases, often repeated immediately after hearing them.
    Tapping: Tapping hands or objects repeatedly.
    Visual Stimming: Staring at lights, moving fingers in front of the eyes, or watching objects spin.
    Chewing or Biting: Chewing on objects, clothing, or oneself.

    Here is an array of json data from every 10 frame snippet of the video. Every frame is taken every second.
    Summarize the json data and provide a output in the markdown format. Also make sure to note down which part of
    the video in seconds each observation came from.

    Data: {data}

    Only provide your output as markdown and nothing more.
    """.replace("{data}", str(previous_messages))


    endpoint = "https://usecase1hub1533117385.openai.azure.com/"
    deployment = "gpt-4"

    subscription_key = "EtQkrbu2AazF9oNNHr7wZ0Vf7CSJTHwxvsqbiinQO9AHsjBHIEpoJQQJ99BDAC4f1cMXJ3w3AAAAACOG3E6M"
    api_version = "2024-12-01-preview"

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=subscription_key,
    )

    messages=[
        {"role": "system", "content": system},
        ]

    response = client.chat.completions.create(
        messages=messages,
        max_tokens=4096,
        temperature=.5,
        top_p=.7,
        model=deployment
    )
    return response.choices[0].message.content

def convert_milliseconds_to_minute_timestamps(ms):
    seconds = ms/1000
    minutes = int(seconds//60)
    rem_seconds = int(math.floor(seconds - minutes * 60))
    return f'{minutes}:{rem_seconds:02}'


st.title('Use Case 1 Demo')

video, audio = st.tabs(["Video", "Audio"])

with video:
    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0
    if "button_key" not in st.session_state:
        st.session_state["button_key"] = 10
    if "script" not in st.session_state:
        st.session_state.script = ''
    if "b64frames" not in st.session_state:
        st.session_state.b64frames = []

    uploaded_video = st.file_uploader("Upload a video of the session",
                                      type=["mp4"],
                                      key=st.session_state["file_uploader_key"])
    if uploaded_video is not None:
        video_path = './data/155659/20230613_155659.mp4'
        audio_path = './data/155659/20230613_155659.wav'

        with open(video_path, "wb") as f:
            f.write(uploaded_video.getbuffer())

        # Process Video into Frames and Audio
        st.session_state.b64frames = process_video(video_path)
        audio_bytes = process_audio(video_path, audio_path)

        # Process Transcription of Wav file
        audio_transcription = get_audio_transcription(audio_bytes)
        st.session_state.script = get_script(audio_transcription)

        st.session_state["file_uploader_key"] += 1
        st.rerun()


    if "prompt_history" not in st.session_state:
        st.session_state.prompt_history = []
    if "frame_start" not in st.session_state:
        st.session_state.frame_start = 0
    if "frame_end" not in st.session_state:
        st.session_state.frame_end = 10
    if "finished_processing" not in st.session_state:
        st.session_state.finished_processing = False

    button = st.button("Process Video", key=st.session_state["button_key"])
    if button:
        st.session_state.frame_start = 0
        st.session_state.frame_end = 10
        # while st.session_state.frame_start < len(st.session_state.b64frames)-1:
        while st.session_state.frame_start < 50:
            if st.session_state.frame_end > len(st.session_state.b64frames) - 1:
                st.session_state.frame_end = len(st.session_state.b64frames) - 1
            chat_response = talk_to_chatbot(st.session_state.script,
                                            [],
                                            st.session_state.frame_start)
            st.session_state.prompt_history.append({"role": "assistant",
                                                    "content": chat_response,
                                                    "frame_start": st.session_state.frame_start,
                                                    "frame_end": st.session_state.frame_end,
                                                    "total_frames": len(st.session_state.b64frames)})
            st.session_state.frame_start += 10
            st.session_state.frame_end = st.session_state.frame_start + 10
        else:
            st.session_state.finished_processing = True
            st.session_state["button_key"] += 1
            st.rerun()

    if st.session_state.finished_processing:
        chat_response = summarize_chatbot(st.session_state.prompt_history)
        st.markdown(chat_response)

with audio:
    def talk_to_chatbot_audio(script, previous_messages):
        system = """
        You will be given a json object that is an audio transcription of a therapy session with a patient with autism.
        Your job is to answer questions about the data, e.g. at what time stamps did speaker 1 start and end conversations,
        or where did speaker 1 hesitate?

        Return your output as a markdown, with bulleted lists where appropriate.

        If you provide any relevant time stamps, always include the transcript for words or phrases that were spoken at those
        time stamps. Only refer to the "offsetSeconds" attributes for phrases when providing timestamps.
        """

        endpoint = "https://usecase1hub1533117385.openai.azure.com/"
        deployment = "gpt-4"

        subscription_key = "EtQkrbu2AazF9oNNHr7wZ0Vf7CSJTHwxvsqbiinQO9AHsjBHIEpoJQQJ99BDAC4f1cMXJ3w3AAAAACOG3E6M"
        api_version = "2024-12-01-preview"

        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key,
        )

        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": [
                    {
                        "type": "text",
                        "text": script
                    }
                ],
            }
        ]

        for message in previous_messages:
            messages.append(message)

        response = client.chat.completions.create(
            messages=messages,
            max_tokens=4096,
            temperature=0,
            top_p=1.0,
            model=deployment
        )
        return response.choices[0].message.content

    if "file_uploader_key_audio" not in st.session_state:
        st.session_state["file_uploader_key_audio"] = 100
    if "script" not in st.session_state:
        st.session_state.script = ''
    if "script_txt" not in st.session_state:
        st.session_state.script_txt = ''

    uploaded_video = st.file_uploader("Upload a video of the session",
                                      type=["mp4"],
                                      key=st.session_state["file_uploader_key_audio"])
    if uploaded_video is not None:
        video_path = './data/155659/20230613_155659.mp4'
        audio_path = './data/155659/20230613_155659.wav'

        audio_bytes = process_audio(video_path, audio_path)

        # Process Transcription of Wav file
        audio_transcription = get_audio_transcription(audio_bytes)
        st.session_state.script, st.session_state.script_txt = get_script_audio(audio_transcription)

        st.success("Uploaded and Processed Audio")
        st.session_state["file_uploader_key_audio"] += 1
        st.rerun()

    if "prompt_history_audio" not in st.session_state:
        st.session_state.prompt_history_audio = []

    prompt = st.chat_input("Input your prompt to the model")
    if prompt:
        st.text("Transcription: \n\r")
        st.text(st.session_state.script_txt)

        if prompt == "clear":
            st.session_state.prompt_history_audio = []
            st.text(f"Cleared Chat History")
        else:
            st.session_state.prompt_history_audio.append({"role": "user", "content": prompt})
            chat_response = talk_to_chatbot_audio(st.session_state.script,
                                                  st.session_state.prompt_history_audio)
            st.session_state.prompt_history_audio.append({"role": "assistant", "content": chat_response})

            st.text("Chat History: \n\r")
            for message in st.session_state.prompt_history_audio:
                st.text(message["content"] + "\n\r")


