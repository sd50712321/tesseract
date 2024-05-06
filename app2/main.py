from flask import Flask, request
from flask import render_template
import settings
import utils
import numpy as np
import cv2
import predictions as pred
import json
import os
import datetime
import base64
import re
import subprocess

app = Flask(__name__)
app.secret_key = 'document_scanner_app'

docscan = utils.DocumentScan()

def base64_to_cv2_image(base64_string):
    # Decode Base64 to binary data
    base64_data = re.sub('^data:image/.+;base64,', '', base64_string)
    binary_data = base64.b64decode(base64_data)
    # Convert binary data to NumPy array and then to OpenCV image
    np_arr = np.frombuffer(binary_data, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)


def save_base64_image(base64_string, directory, filename):
    # Decode the base64 string to binary image data
    base64_data = re.sub('^data:image/.+;base64,', '', base64_string)
    image_data = base64.b64decode(base64_data)

    # Create the directory if it does not exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Write the image data to a file
    with open(os.path.join(directory, filename), 'wb') as f:
        f.write(image_data)
        
def run_makebox(tiff_path, box_output_path):
    """Executes Tesseract's makebox command to generate a Box file."""
    try:
        command = ['tesseract', tiff_path, box_output_path, '-c', 'batch.nochop=true', 'makebox']
        subprocess.run(command, check=True)
        print(f"Box file created: {box_output_path}.box")
    except subprocess.CalledProcessError as e:
        print(f"Error during makebox execution: {e}")
        raise

def create_box_files(annotations_data, docscan_image, timestamp):
    box_filename = f"{timestamp}.box"

    # Set paths for the image and box file
    box_file_path = os.path.join('./boxes/', box_filename)

    # Load the saved image to perform further processing
    image = cv2.imread(docscan_image)
    if image is None:
        print("Error: Image could not be loaded.")
        return

    height, width, _ = image.shape
    box_lines = []

    for annot in annotations_data:
        # Convert annotations to box file format
        # x1, y1, x2, y2 = annot['x1'], height - annot['y2'], annot['x2'], height - annot['y1']
        x1, y1, x2, y2 = annot['x1'], annot['y2'], annot['x2'], annot['y1']
        print(f"Box coordinates: ({x1}, {y1}) ({x2}, {y2})")
        text = annot['text']
        # Assuming text contains only one character per box for simplicity
        for char in text:
            box_line = f"{char} {x1} {y1} {x2} {y2} 0"
            box_lines.append(box_line)

    # Ensure the box directory exists
    if not os.path.exists('./boxes/'):
        os.makedirs('./boxes/')

    # Save the box file
    with open(box_file_path, 'w', encoding='utf8') as f:
        for line in box_lines:
            f.write(line + '\n')

    print("Box file created:", box_file_path)


@app.route('/',methods=['GET','POST'])
def scandoc():
    if request.method == 'POST':
        file = request.files['image_name']
        upload_image_path = utils.save_upload_image(file)
        print('Image saved in = ', upload_image_path)

        # Attempt to get document coordinates
        try:
            four_points, size = docscan.document_scanner(upload_image_path)
            print(four_points, size)
            if four_points is None:
                message = 'Unable to locate the coordinates of the document: points displayed are random'
                points = [{'x': 10, 'y': 10}, {'x': 120, 'y': 10}, {'x': 120, 'y': 120}, {'x': 10, 'y': 120}]
                return render_template('scanner.html',
                                       points=points,
                                       fileupload=True,
                                       message=message)
            else:
                points = utils.array_to_json_format(four_points)
                message = 'Located the coordinates of the document using OpenCV'
                return render_template('scanner.html',
                                       points=points,
                                       fileupload=True,
                                       message=message)
        except Exception as e:
            print("Error processing document scan:", str(e))
            # Handle the case where `four_points` is not generated
            return render_template('scanner.html', fileupload=False, message=str(e))

        return render_template('scanner.html', fileupload=False)

    return render_template('scanner.html', fileupload=False)


@app.route('/submit_annotations', methods=['POST'])
def submit_annotations():
    print('request.form = ', request.form)
    # Get the annotations data and the annotated image
    annotations = request.form['annotations']
    annotated_image = request.form['annotated_image']  # Base64 인코딩된 이미지 데이터
    annotations_data = json.loads(annotations)

    # Generate a unique filename for the original image
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    image_filename = f"{timestamp}.jpg"  # Ensure JPEG extension
    tiff_filename = f"{timestamp}.tiff"  # TIFF extension
    origin_image_directory = './images/origin'
    boundary_image_directory = './images/boundary'
    tiff_image_directory = './images/tiff'

    # Create directories if they don't exist
    if not os.path.exists(origin_image_directory):
        os.makedirs(origin_image_directory)
    if not os.path.exists(boundary_image_directory):
        os.makedirs(boundary_image_directory)
    if not os.path.exists(tiff_image_directory):
        os.makedirs(tiff_image_directory)

    # Load the original image from the static path
    upload_image_path = './static/media/upload.jpg'
    if not os.path.exists(upload_image_path):
        return "Error: No upload image found."
    
    # Save the original image as both JPEG and TIFF to the origin directory
    origin_jpg_path = os.path.join(origin_image_directory, image_filename)
    origin_tiff_path = os.path.join(tiff_image_directory, tiff_filename)
    image = cv2.imread(upload_image_path)
    cv2.imwrite(origin_jpg_path, image)
    cv2.imwrite(origin_tiff_path, image)

    # Load the original image for boundary processing
    docscan_image = cv2.imread(upload_image_path)

    # Apply the annotations to the original image (boundary processing)
    for annot in annotations_data:
        x1, y1, x2, y2 = annot['x1'], annot['y1'], annot['x2'], annot['y2']
        text = annot['text']
        cv2.rectangle(docscan_image, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Red rectangle
        cv2.putText(docscan_image, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    # Save the annotated (boundary) image to the boundary directory
    boundary_image = base64_to_cv2_image(annotated_image)
    
    boundary_image_path = os.path.join(boundary_image_directory, image_filename)
    cv2.imwrite(boundary_image_path, boundary_image)
    
    print('origin_jpg_path = ', origin_jpg_path)
    
    create_box_files(annotations_data, origin_jpg_path, timestamp)

    return "Annotations received successfully!"


@app.route('/transform',methods=['POST'])
def transform():
    try:
        points = request.json['data']
        array = np.array(points)
        magic_color = docscan.calibrate_to_original_size(array)
        #utils.save_image(magic_color,'magic_color.jpg')
        filename =  'magic_color.jpg'
        magic_image_path = settings.join_path(settings.MEDIA_DIR,filename)
        cv2.imwrite(magic_image_path,magic_color)
        
        return 'sucess'
    except:
        return 'fail'
        
    
@app.route('/prediction')
def prediction():
    # load the wrap image
    wrap_image_filepath = settings.join_path(settings.MEDIA_DIR, 'magic_color.jpg')
    image = cv2.imread(wrap_image_filepath)
    if image is None:
        return "Error: Image could not be loaded."

    try:
        image_bb = pred.getPredictions(image)  # Now only expecting one return value

        bb_filename = settings.join_path(settings.MEDIA_DIR, 'bounding_box.jpg')
        cv2.imwrite(bb_filename, image_bb)
        
        # Optionally, return the path to the image, or any other information
        return render_template('predictions.html', image_path=bb_filename)
    except Exception as e:
        return f"An error occurred: {str(e)}"


@app.route('/about')
def about():
    return render_template('about.html')



if __name__ == "__main__":
    app.run(debug=True)