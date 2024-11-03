from __future__ import unicode_literals
from flask import send_from_directory
# Make sure to import your VideoSummarizer class

from flask import Flask, request, jsonify
import nltk
import argparse
import subprocess
import sys
from datetime import datetime
from typing import Tuple, List, Optional, Dict
from pathlib import Path
import logging
import yt_dlp
import chardet
import pysrt
from moviepy.editor import VideoFileClip, concatenate_videoclips
from collections import defaultdict
import numpy as np
from nltk.tokenize import sent_tokenize
from nltk.tag import pos_tag
from flask_cors import CORS
import os
import tempfile
import yt_dlp  # Use yt_dlp instead of youtube_dl
from moviepy.editor import VideoFileClip
import google.generativeai as genai
import openai
from pydub import AudioSegment
from dotenv import load_dotenv
from app import VideoSummarizer
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'mp4'}
summary_chat = ""
# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Retrieve API keys from environment variables
genai_api_key = os.getenv("GENAI_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Configure the APIs with hardcoded keys
genai.configure(api_key=genai_api_key)
openai.api_key = openai_api_key

summary_prompt = """You are a YouTube video summarizer. You will be taking the transcript text
and summarizing the entire video and providing the important summary in points
within 100 words. Please provide the summary of the text given here:  """

chat_prompt = """You are a helpful AI assistant. Based on the context provided, answer the user's question accurately and concisely: """


def download_video_srt(url):
    """Downloads specified YouTube video's subtitles as a vtt/srt file and the video itself."""
    outtmpl = os.path.join(os.getcwd(), 'downloads',
                           '%(title)s-%(id)s.%(ext)s')
    # Create downloads directory if it doesn't exist
    os.makedirs(os.path.dirname(outtmpl), exist_ok=True)

    ydl_opts = {
        'format': 'best',
        'outtmpl': outtmpl,
        'subtitlesformat': 'srt',
        'writeautomaticsub': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=True)
        movie_filename = ydl.prepare_filename(result)
        subtitle_info = result.get("requested_subtitles", {})

        # Get the first available subtitle
        if subtitle_info:
            subtitle_language = next(iter(subtitle_info.keys()))
            subtitle_ext = subtitle_info[subtitle_language]['ext']
            subtitle_filename = movie_filename.replace(
                ".mp4", f".{subtitle_language}.{subtitle_ext}")
        else:
            subtitle_filename = None

    return movie_filename, subtitle_filename


def extract_transcript_from_video(video_file):
    """Extract audio from video and transcribe it using OpenAI Whisper."""
    try:
        video = VideoFileClip(video_file)
        audio_path = os.path.join(tempfile.gettempdir(), "temp_audio.wav")
        video.audio.write_audiofile(audio_path)

        audio = AudioSegment.from_wav(audio_path)
        chunk_length_ms = 25 * 1000  # 25 seconds
        chunks = [audio[i:i + chunk_length_ms]
                  for i in range(0, len(audio), chunk_length_ms)]

        transcript = ""

        # Transcribe each chunk
        for i, chunk in enumerate(chunks):
            chunk_path = os.path.join(
                tempfile.gettempdir(), f"temp_chunk_{i}.wav")
            chunk.export(chunk_path, format="wav")

            with open(chunk_path, 'rb') as audio_file:
                transcript_response = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file
                )
                transcript += transcript_response['text'] + " "

        return transcript.strip()

    except Exception as e:
        print("Error extracting transcript from video:", e)
        return None


def generate_gemini_content(transcript_text, prompt):
    """Generate summary using Google Gemini Pro."""
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt + transcript_text)
    return response.text


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"message": "Backend AI is running."})


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('video_summarizer.log')
    ]
)
logger = logging.getLogger(__name__)


@app.route('/summarize_video', methods=['POST'])
def summarize_video():
    # Parse JSON request
    data = request.get_json()

    # Extract parameters
    url = data.get('url')
    duration = int(data.get('length'))
    print(data)
    print(type(duration))
    duration = data.get('duration', duration)  # Default duration is 60 seconds
    output_dir = data.get('output_dir', 'output')  # Default output directory

    # Validate URL input
    if not url:
        return jsonify({'error': 'YouTube video URL is required'}), 400

    # Create a summarizer instance and process the video
    summarizer = VideoSummarizer(output_dir=output_dir)
    result_path = summarizer.process_video(url, duration)
    print(result_path)

    if result_path:
        # Assuming your app is served at http://localhost:5000, adjust as necessary
        video_url = f"http://localhost:5000/{output_dir}/{result_path.name}"

        return jsonify({'message': 'Summary video created successfully', 'path': video_url}), 200
    else:
        return jsonify({'error': 'Failed to create summary video. Check the logs for details.'}), 500


@app.route('/output/<path:filename>')
def serve_file(filename):
    return send_from_directory('output', filename)


@app.route('/summarize', methods=['POST'])
def summarize():
    if 'file' in request.files:
        file = request.files['file']

        if file and allowed_file(file.filename):
            # Set the uploads directory
            upload_folder = app.config['UPLOAD_FOLDER']
            # Create uploads directory if it doesn't exist
            os.makedirs(upload_folder, exist_ok=True)

            file_path = os.path.join(upload_folder, file.filename)
            file.save(file_path)
            modified_summary_prompt = f"{summary_prompt} Please summarize the text in {language}."

            transcript_text = extract_transcript_from_video(file_path)
            summary = generate_gemini_content(
                transcript_text, modified_summary_prompt)

            # Write summary to a text file
            with open('summary.txt', 'w', encoding='utf-8') as f:
                f.write(summary)

            return jsonify({"success": True, "summary": summary})

            print("Could not retrieve transcript from the video.")
            return jsonify({"success": False, "error": "Could not retrieve transcript from the video."}), 400

        return jsonify({"success": False, "error": "Unsupported file type. Only .mp4 files are allowed."}), 400

    elif request.is_json:
        data = request.get_json()
        print(data)
        youtube_url = data.get('url')
        language = data.get('language')
        print(language)
        modified_summary_prompt = f"{summary_prompt} Please summarize the text in {language}."

        if not youtube_url:
            return jsonify({"success": False, "error": "No URL provided"}), 400

        video_file, subtitle_file = download_video_srt(youtube_url)

        if os.path.isfile(video_file):
            transcript_text = extract_transcript_from_video(video_file)
            summary = generate_gemini_content(
                transcript_text, modified_summary_prompt)

            # Write summary to a text file
            with open('summary.txt', 'w', encoding='utf-8') as f:
                f.write(summary)

            return jsonify({"success": True, "summary": summary})

    return jsonify({"success": False, "error": "No file or URL provided"}), 400


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()

    user_input = next((message['content'] for message in reversed(
        data['messages']) if message['role'] == 'user'), None)
    print(data)

    # Read summary from the text file
    try:
        with open('summary.txt', 'r', encoding='utf-8') as f:
            summary_text = f.read()
    except FileNotFoundError:
        return jsonify({"success": False, "error": "Summary not found. Please summarize a video first."}), 400

    if not user_input or not summary_text:
        return jsonify({"success": False, "error": "User input and summary text are required."}), 400

    # Combine the chat prompt with the summary and the user input
    complete_prompt = chat_prompt + "\n\nContext:\n" + \
        summary_text + "\n\nUser Question:\n" + user_input

    # Use the ChatCompletion API for chat models
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or "gpt-4" if you have access
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": complete_prompt}
        ],
        max_tokens=150
    )

    answer = response['choices'][0]['message']['content'].strip()
    return jsonify({"success": True, "answer": answer})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
