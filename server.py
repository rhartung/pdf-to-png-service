from flask import Flask, request, send_from_directory
from flask import jsonify
from werkzeug.utils import secure_filename
from image_conversion import allowed_file, get_url_manifest
from wand.image import Image

import os
import boto3


UPLOAD_FOLDER = "static/uploads"


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.environ["SECRET_KEY"]

s3 = boto3.client("s3")
BUCKET_NAME = "pdf-to-png-files"


@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    """Accepts HTTP POST request containing PDF files - convert to PNG.

    Returns URL manifest for each page of doc as PNG"""

    if 'file' not in request.files:
        return jsonify("No file submitted")

    file = request.files['file']
    filename = secure_filename(file.filename)

    if file and allowed_file(file, filename):

        # ImageMagick requires PDF to exist in current directory
        # prior to converting file to PNG
        file.save(filename)
        new_filename = "{}.png".format(filename.split(".")[0])

        converted_img = Image(filename=str(filename)).convert("png")
        converted_img.save(filename=new_filename)

        for i in range(len(converted_img.sequence)):

            current = "{}-{}.png".format(filename.split(".")[0], i)
            print current
            s3.upload_file(current, BUCKET_NAME, current)

        return "Done"

        # Remove temporarily saved PDF after converting to PNG
        # os.remove(filename)
        # os.remove(new_filename)

    #     return get_url_manifest(converted_img, filename)

    # else:
    #     return jsonify("/upload-pdf route accepts only PDF file format.")


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Display uploaded file."""

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":

    app.run(port=8000, host="0.0.0.0")
