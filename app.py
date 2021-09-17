from flask import Flask, request, render_template, make_response, send_file
# from flask_restful import Api, Resource
from flask import send_from_directory
from bokeh.embed import components
# from functions import *
import os

app = Flask(__name__)
# api = Api(app)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'),'favicon.ico', mimetype='image/png')
    
@app.route('/')
def home():
   return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)