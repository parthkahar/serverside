from flask import Flask, request, jsonify
from pydub import AudioSegment
import speech_recognition as sr
import os
from flask_cors import CORS
import subprocess
import logging
from datetime import datetime
import pyodbc

app = Flask(__name__)

server = 'DESKTOP-CCGKBQ7'
database = 'GyanShaktiStudent'
username = 'sa'
password = 'baba'





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

import subprocess
import os

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
        
        # Redirect both stdout and stderr to suppress verbose output
        with open(os.devnull, 'w') as null_file:
            subprocess.run(ffmpeg_cmd, stdout=null_file, stderr=null_file, check=True)
        
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

def store_transcription_result_in_database(StudentCode, transcription_result, server, database, username, password):
    print("running111")
    try:
        # Establish a connection to the database
        connection = pyodbc.connect(
            driver='{SQL Server}',
            server=server,
            database=database,
            uid=username,
            pwd=password,
            autocommit=True
        )

        # Create a cursor
        cursor = connection.cursor()

        # Prepare SQL query to update the transcription result in the database
        query = "INSERT INTO dbo.TBLStudentTest (StudentCode, StudentAns) VALUES (?, ?)"

        # Execute the query with the transcription result and student code as parameters
        cursor.execute(query, (StudentCode, transcription_result))

        # Commit the transaction
        connection.commit()

        # Close the cursor and connection
        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Error storing transcription result in database: {e}")

@app.route('/save_video', methods=['POST'])
def save_and_transcribe():
    print('calll')
    try:
        if 'recording' not in request.files:
            raise ValueError('No recording file in the request')

        recording_file = request.files['recording']
        StudentCode = request.form["StudentCode"]
        #Id=request.form["Id"]
        ExamCode = request.form["ExamCode"]
        QuestionId = request.form["QuestionId"]
        #StudentAns = request.form["StudentAns"]

        print("step 1")
        print(ExamCode)
        print(QuestionId)
        #print(StudentAns)
        print(StudentCode)
        #print(Id)

        # Get a unique filename for the webm file
        webm_filename, webm_path = get_unique_filename(save_directory, base_filename, file_counter, 'webm')
        print(webm_filename)

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
        transcription_result = transcribe_audio_offline(wav_file_path)
        
        print(transcription_result)
        
        ret_value(StudentCode, ExamCode, QuestionId)

        # Store the transcription result in the database
        if transcription_result == "Speech Recognition could not understand audio":
            # Store the error message in the database
            store_transcription_result_in_database(StudentCode, server, database, username, password)
        else:
            # Store the transcription result in the database
            # store_transcription_result_in_database(StudentCode, transcription_result, server, database, username, password)

         return jsonify({'status': 'success', 'message': 'Recording saved, transcoded, and transcribed successfully',
                        'duration': duration, })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})



def ret_value(StudentCode, ExamCode, QuestionId, StudentAns):
    print('value is being returned')
    try:
        connection = pyodbc.connect(
            driver='{SQL Server}',
            server=server,
            database=database,
            uid=username,
            pwd=password
        )
        
        
        cursor = connection.cursor()
        query = "INSERT INTO dbo.TBLStudentTest (StudentCode, ExamCode, QuestionId, StudentAns) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (StudentCode, ExamCode, QuestionId, StudentAns))
        connection.commit()
        cursor.close()
        connection.close()
        return "Data inserted successfully"
    except Exception as e:
        return str(e)




@app.route('/GET_tbl_student', methods=['GET'])
def get_tbl_city_data():
    try:
        # Establish a connection
        connection = pyodbc.connect(
            driver='{SQL Server}',
            server=server,
            database=database,
            uid=username,
            pwd=password,
            autocommit=True
        )

        # Create a cursor from the connection
        cursor = connection.cursor()

        # Example query for TBLCity
        query = "SELECT * FROM dbo.TBLStudent"

        # Execute the query
        cursor.execute(query)

        # Fetch all rows and convert to a list of dictionaries
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return jsonify(data)

    except pyodbc.Error as ex:
        # If there is an error, print the error message and return an error response
        print(f"Error: {ex}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/GET_TBLExam', methods=['GET'])
def tbl_exam():
    try:
        # Establish a connection
        connection = pyodbc.connect(
            driver='{SQL Server}',
            server=server,
            database=database,
            uid=username,
            pwd=password,
            autocommit=True
        )

        # Create a cursor from the connection
        cursor = connection.cursor()

        # Example query for TBLExam
        query = "SELECT * FROM dbo.TBLExam"

        # Execute the query
        cursor.execute(query)

        # Fetch all rows and convert to a list of dictionaries
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return jsonify(data)

    except pyodbc.Error as ex:
        # If there is an error, print the error message and return an error response
        print(f"Error: {ex}")
        return jsonify({'error': 'Internal Server Error'}), 500
     
    
@app.route('/GET_test_questions', methods=['GET'])
def tbl_testquestion():
    try:
        # Establish a connection
        connection = pyodbc.connect(
            driver='{SQL Server}',
            server=server,
            database=database,
            uid=username,
            pwd=password,
            autocommit=True
        )

        # Create a cursor from the connection
        cursor = connection.cursor()

        # Example query for TBLExam
        query = "SELECT * FROM dbo.TBLTestQuestion"

        # Execute the query
        cursor.execute(query)

        # Fetch all rows and convert to a list of dictionaries
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return jsonify(data)

    except pyodbc.Error as ex:
        # If there is an error, print the error message and return an error response
        print(f"Error: {ex}")
        return jsonify({'error': 'Internal Server Error'}), 500
    
    
    

@app.route('/GET_StudentTest', methods=['GET'])
def tbl_student_test():
    try:
        # Establish a connection
        connection = pyodbc.connect(
            driver='{SQL Server}',
            server=server,
            database=database,
            uid=username,
            pwd=password,
            autocommit=True
        )

        # Create a cursor from the connection
        cursor = connection.cursor()

        # Example query for TBLExam
        query = "SELECT * FROM dbo.TBLStudentTest"

        # Execute the query
        cursor.execute(query)

        # Fetch all rows and convert to a list of dictionaries
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return jsonify(data)

    except pyodbc.Error as ex:
        # If there is an error, print the error message and return an error response
        print(f"Error: {ex}")
        return jsonify({'error': 'Internal Server Error'}), 500
    
    


@app.route('/GET_questions_by_exam/<exam_code>', methods=['GET'])
def get_questions_by_exam(exam_code):
    try:
        # Validate the exam code (add your own validation logic)
        if not exam_code:
            return jsonify({'error': 'Exam code is required'}), 400

        # Establish a connection
        connection = pyodbc.connect(
            driver='{SQL Server}',
            server=server,
            database=database,
            uid=username,
            pwd=password,
            autocommit=True
        )

        # Create a cursor from the connection
        cursor = connection.cursor()

        # Example query for questions related to a specific exam code
        query = f"SELECT * FROM dbo.TBLTestQuestion WHERE ExamCode = '{exam_code}'"

        # Execute the query
        cursor.execute(query)

        # Fetch all rows and convert to a list of dictionaries
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return jsonify(data)

    except pyodbc.Error as ex:
        # If there is an error, print the error message and return an error response
        print(f"Error: {ex}")
        return jsonify({'error': 'Internal Server Error'}), 500
    
    
    
@app.route('/GET_questionsbyid/<ExamCode>/<Qestionid>', methods=['GET'])
def get_question(ExamCode, Qestionid):
    try:
        # Validate the exam code and question id
        if not ExamCode:
            return jsonify({'error': 'Exam code is required'}), 400
        if not Qestionid:
            return jsonify({'error': 'Question id is required'}), 400

        # Establish a connection
        connection = pyodbc.connect(
            driver='{SQL Server}',
            server=server,
            database=database,
            uid=username,
            pwd=password,
            autocommit=True
        )

        # Create a cursor from the connection
        cursor = connection.cursor()

        # Example query to fetch the question by exam code and question id
        query = f"SELECT Question FROM dbo.TBLTestQuestion WHERE ExamCode = '{ExamCode}' AND Qestionid = '{Qestionid}'"

        # Execute the query
        cursor.execute(query)

        # Fetch all rows
        rows = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        # If no rows are returned, return a message
        if not rows:
            return jsonify({'message': 'Question not found'})

        # Extract the questions from the rows
        questions = [row[0] for row in rows]

        return jsonify({'questions': questions})

    except pyodbc.Error as ex:
        # If there is an error, print the error message and return an error response
        print(f"Error: {ex}")
        return jsonify({'error': 'Internal Server Error'}), 500

    
    

@app.route('/POST/Attendence',methods=['POST'])
def attendence():
    
    data = request.json

    # Extract parameters from the request data
    StudentCode = data.get('StudentCode')
    InOutDate = data.get('InOutDate')
    InOutTime = data.get('InOutTime')
    CreatedBy = data.get('CreatedBy')

    in_out_datetime = datetime.strptime(f"{InOutDate} {InOutTime}", "%Y-%m-%d %H:%M:%S")
    in_out_date = in_out_datetime.date()
    in_out_time = in_out_datetime.time()
    
    print(in_out_date)
    print(in_out_time)

    print(StudentCode,InOutDate,InOutTime,CreatedBy)
    print('value is being returned')
    try:
        connection = pyodbc.connect(
            driver='{SQL Server}',
            server=server,
            database=database,
            uid=username,
            pwd=password
        )
        print("Connected to the database successfully.")
        table_exists("TBLAttendance",connection)
        table_name="TBLAttendance"
        if table_exists(table_name, connection):
            print(f"Table '{table_name}' exists.")
        else:
            print(f"Table '{table_name}' does not exist.")

        CreatedDate=datetime.now()
        print(StudentCode,InOutDate,InOutTime,CreatedBy,CreatedDate)
        cursor = connection.cursor()
        query = "INSERT INTO dbo.TBLAttendance (StudentCode, InOutDate,InOutTime,CreatedBy) VALUES (?, ?, ?, ?)"
        #query = f"INSERT INTO dbo.TBLAttendance (StudentCode, InOutDate,InOutTime,CreatedBy) VALUES ({StudentCode},{in_out_date},{in_out_time},{CreatedBy})"
        #query='INSERT INTO dbo.TBLAttendance (StudentCode, InOutDate, InOutTime, CreatedDate, CreatedBy) VALUES ('S-002', '2024-01-13', '11:00:00', '2024-03-16T15:47:21', 'Admin')'
        #query = "INSERT INTO dbo.testtable (testdata) VALUES (?)"
        
        print(query)
        #cursor.execute(query, (StudentCode))
        cursor.execute(query, (StudentCode,InOutDate,InOutTime,CreatedBy))
       
        #cursor.execute(query)
        connection.commit()
        cursor.close()
        connection.close()
        return "Data inserted successfully"
    except Exception as e:
        return str(e)

def table_exists(table_name, connection):
    query = f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table_name}'"
    cursor = connection.cursor()
    cursor.execute(query)
    row = cursor.fetchone()
    cursor.close()
    return row[0] > 0

# Example usage
table_name = 'dbo.TBLAttendance'  # Adjust this to your table name
connection = pyodbc.connect(
    driver='{SQL Server}',
    server=server,
    database=database,
    uid=username,
    pwd=password
)

if table_exists(table_name, connection):
    print(f"Table '{table_name}' exists.")
else:
    print(f"Table '{table_name}' does not exist.")






@app.route('/GET/Attendence', methods=['GET'])
def get_attendance():
    try:
        # Establish a connection
        connection = pyodbc.connect(
            driver='{SQL Server}',
            server=server,
            database=database,
            uid=username,
            pwd=password,
            autocommit=True
        )

        # Create a cursor from the connection
        cursor = connection.cursor()

        # Example query for TBLExam
        query = "SELECT * FROM dbo.TBLAttendance"

        # Execute the query
        cursor.execute(query)

        # Fetch all rows and convert to a list of dictionaries
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Close the cursor and connection
        cursor.close()
        connection.close()

        return jsonify(data)

    except pyodbc.Error as ex:
        # If there is an error, print the error message and return an error response
        print(f"Error: {ex}")
        return jsonify({'error': 'Internal Server Error'}), 500




    

if __name__ == '__main__':
    app.run(debug=True, host = '192.168.29.16', port=5001)
