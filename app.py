from flask import Flask, request, jsonify
from pydub import AudioSegment
import speech_recognition as sr
import os
from flask_cors import CORS
import subprocess
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Video processing configuration
save_directory = r'C:\Users\parthcsssss\Desktop\final'
ffmpeg_path = r'E:\ffmpeg\ffmpeg.exe'
file_counter = 1

# Audio transcription configuration
base_filename = 'demo'

def get_unique_filename(directory, base_filename, file_counter, extension):
    while True:
        filename = f'{base_filename}{file_counter}.{extension}'
        file_path = os.path.join(directory, filename)
        if not os.path.exists(file_path):
            return filename, file_path
        file_counter += 1

def get_video_duration(file_path):
    try:
        ffmpeg_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=duration',
                      '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        duration = float(result.stdout)
        return duration
    except Exception as e:
        print(f"Error getting video duration with ffmpeg: {e}")
        return None

def transcode_video(input_path, output_directory, filename, ffmpeg_path='E:\\ffmpeg\\ffmpeg.exe'):
    try:
        output_path = os.path.join(output_directory, filename)
        ffmpeg_cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-strict', 'experimental',
            output_path
        ]
        print(f"Executing FFmpeg command: {ffmpeg_cmd}")
        subprocess.run(ffmpeg_cmd, check=True)
        logging.info(f"Video transcoding successful. Output saved as {filename}")

        return output_path
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during transcoding: {e}")
        return None

def convert_mp4_to_wav(mp4_file_path, wav_file_path):
    try:
        print(f"Converting MP4 to WAV. Input: {mp4_file_path}, Output: {wav_file_path}")
        audio = AudioSegment.from_file(mp4_file_path)
        audio.export(wav_file_path, format="wav")
    except Exception as e:
        print(f"Error during MP4 to WAV conversion: {e}")

def transcribe_audio_offline(wav_file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_file_path) as source:
        audio = recognizer.record(source)

    try:
        transcript = recognizer.recognize_google(audio)
        print(f"Transcription: {transcript}")
        return transcript
    except sr.UnknownValueError:
        print("Speech Recognition could not understand audio")
        return "Speech Recognition could not understand audio"
    except sr.RequestError as e:
        print(f"Error during transcription: {e}")
        return f"Could not request results from Google Speech Recognition service; {e}"

@app.route('/save_video', methods=['POST'])
def save_and_transcribe():
    try:
        if 'recording' not in request.files:
            raise ValueError('No recording file in the request')

        recording_file = request.files['recording']
        print("Call")
        # Get a unique filename for the webm file
        webm_filename, webm_path = get_unique_filename(save_directory, base_filename, file_counter, 'webm')

        app.logger.info('Saving webm video to: %s', webm_path)
        recording_file.save(webm_path)

        # Get video duration using ffmpeg
        duration = get_video_duration(webm_path)
        app.logger.info('Webm video duration: %s seconds')

        # Get a unique filename for the mp4 file
        mp4_filename, mp4_path = get_unique_filename(save_directory, base_filename, file_counter, 'mp4')

        # Transcode the saved webm video and delete the original file
        transcode_video(webm_path, save_directory, mp4_filename)

        # Get a unique filename for the wav file
        wav_filename, wav_file_path = get_unique_filename(save_directory, base_filename, file_counter, 'wav')

        # Convert MP4 to WAV
        convert_mp4_to_wav(mp4_path, wav_file_path)

        # Perform offline transcription
        result = transcribe_audio_offline(wav_file_path)

        return jsonify({'status': 'success', 'message': 'Recording saved, transcoded, and transcribed successfully',
                        'duration': duration, 'transcription': result})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host = '192.168.29.16', port=5001)
