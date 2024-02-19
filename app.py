from flask import Flask, request, jsonify, send_file
from io import BytesIO
import os
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Define the save directory
save_directory = r'C:\Users\parthcsssss\Desktop\flask python\8feb\ownserber'

@app.route('/save_video', methods=['POST'])
def save_video():
    try:
        # Get the recording data from the request
        recording_data = request.get_data()

        # Generate a unique file name using a timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'video_{timestamp}.webm'
        save_path = os.path.join(save_directory, filename)

        # Save the video in binary write mode, flush, and close the file
        with open(save_path, 'wb') as file:
            file.write(recording_data)
            file.flush()
            os.fsync(file.fileno())

        return send_file(BytesIO(recording_data), mimetype='video/webm', as_attachment=True)
    
    

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, port=5001)
