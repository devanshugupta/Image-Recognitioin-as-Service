from flask import Flask, request
import pandas as pd

app = Flask(__name__)

df = pd.read_csv('classification_face_images_1000.csv')

# Loading faces classification csv as dict
classification_data = dict(zip(df['Image'], df['Results']))

@app.route('/', methods=['POST'])
def classify_image():
    if 'inputFile' not in request.files:
        return "File not provided", 400

    file = request.files['inputFile']
    filename = file.filename.split('.')[0]

    # Get classification result value
    if filename in classification_data:
        prediction_result = classification_data[filename]
        return f"{filename}:{prediction_result}", 200
    else:
        return f"{filename}:No result found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)