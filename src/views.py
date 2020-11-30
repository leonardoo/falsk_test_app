import json

import flask
import jsonschema

from flask import request, render_template, Blueprint
from business import Builder
from datahandler import DatabaseMongo
from streamhandler import StreamHandlerSocketIO


blueprint = Blueprint("simple_page", __name__, template_folder='templates')


@blueprint.route("/", methods=["GET"])
def index():
    return render_template('index.html')


@blueprint.route('/process_json', methods=['POST'])
def upload_file():
    stream_handler = StreamHandlerSocketIO()
    if 'file' not in request.files:
        stream_handler.send("No file", "error")
        return flask.jsonify(error="No file"), 400
    file = request.files['file']
    if not file:
        stream_handler.send("Invalid file", "error")
        return flask.jsonify(error="Invalid file"), 400
    try:
        json_data = json.loads(file.read())
    except:
        stream_handler.send("File Error: No Json", "error")
        return flask.jsonify(status="Invalid Schema"), 400

    stream_handler.send("File Start to Process", "ok")
    try:
        manager = Builder(json_data, stream_handler).generate_manager(DatabaseMongo())
        manager.execute()
    except jsonschema.exceptions.ValidationError as e:
        stream_handler.send("File Error Invalid Schema", "error")
        return flask.jsonify(status="Invalid Schema"), 400

    stream_handler.send("File Processed", "ok")
    return flask.jsonify(status="File Processed"), 200
