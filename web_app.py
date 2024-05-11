from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop
import json
import sys, os
import datetime

GCODE_UPLOAD_PATH = os.getcwd() + "/upload_files/"
CONFIG_FILE_PATH = os.getcwd() + "/configs/config.cfg"

class GetGcodeFileListRequestHandler(RequestHandler):

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

  def get(self):
    print("Received GetGcodeFileListRequest")
    file_list = []
    try:
      for file in os.listdir(GCODE_UPLOAD_PATH):
        if file == '.DS_Store':
          continue
        path = GCODE_UPLOAD_PATH + file
        modified_t = int(os.path.getmtime(path))
        modified_t = datetime.datetime.fromtimestamp(modified_t)
        created_t = int(os.path.getctime(path))
        created_t = datetime.datetime.fromtimestamp(created_t)
        size = str(os.path.getsize(path))
        file_obj = {
          "name": file,
          "created": created_t.strftime("%m/%d/%Y, %H:%M:%S"),
          "modified": modified_t.strftime("%m/%d/%Y, %H:%M:%S"),
          "size": size,
        }
        file_list.append(file_obj)
      self.write({
      'action': "REQUEST_GCODE_FILE_LIST_SUCCESS",
      'payload': file_list,
      'status': 1,
      })
    except:
      self.write({
      'action': "REQUEST_GCODE_FILE_LIST_FAIL",
      'payload': '',
      'status': 0,
      })

class GetGcodeFileRequestHandler(RequestHandler):

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

  def get(self):
    print("Received GetGcodeFileRequest")
    filename = self.get_arguments("filename")[0]
    filepath = GCODE_UPLOAD_PATH + filename
    try:
      with open(filepath, 'r') as f:
        file = f.readlines()
        self.write({
        'action': "REQUEST_GCODE_FILE_SUCCESS",
        'payload': file,
        'status': 1,
        })
    except:
      self.write({
      'action': "REQUEST_GCODE_FILE_FAIL",
      'payload': '',
      'status': 0,
      })

class DeleteGcodeFileRequestHandler(RequestHandler):

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

  def get(self):
    print("Received DeleteGcodeFileRequest")
    filename = self.get_arguments("filename")[0]
    filepath = GCODE_UPLOAD_PATH + filename
    try:
      os.remove(filepath)
      self.write({
      'action': "DELETE_GCODE_FILE_SUCCESS",
      'payload': '',
      'status': 1,
      })
    except:
      self.write({
      'action': "DELETE_GCODE_FILE_FAIL",
      'payload': '',
      'status': 0,
      })


class GetConfigFileRequestHandler(RequestHandler):

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

  def get(self):
    print("Received GetConfigFileRequest")
    filepath = CONFIG_FILE_PATH
    try:
      with open(filepath, 'r') as f:
        file = f.read()
        self.write({
        'action': "REQUEST_CONFIG_FILE_SUCCESS",
        'payload': str(file),
        'status': 1
        })
    except:
      self.write({
      'action': "REQUEST_CONFIG_FILE_FAIL",
      'payload': '',
      'status': 0
      })

class UpdateGcodeFileRequestHandler(RequestHandler):

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

  def options(self):
    pass

  def post(self):
    print("Received UpdateGcodeFileRequest")
    filename = self.get_argument('filename')
    filepath = GCODE_UPLOAD_PATH + filename
    data = self.get_argument('payload')
    try:
      with open(filepath, 'w') as f:
        f.write(data)
        self.write({
        'action': "UPDATE_GCODE_FILE_SUCCESS",
        'payload': '',
        'status': 1,
        })
    except:
      self.write({
      'action': "UPDATE_GCODE_FILE_FAIL",
      'payload': '',
      'status': 0,
      })

class UpdateConfigFileRequestHandler(RequestHandler):

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header('Content-type', 'application/json')
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    self.set_header('Access-Control-Allow-Headers',
                        'Content-Type, Access-Control-Allow-Origin, Access-Control-Allow-Headers, X-Requested-By, Access-Control-Allow-Methods')

  def options(self):
    pass

  def post(self):
    print("Received UpdateConfigFileRequest")
    data = self.get_argument('payload')
    filepath = CONFIG_FILE_PATH
    try:
      with open(filepath, 'w') as f:
        f.write(data)
      self.write({
      'action': "UPDATE_CONFIG_FILE_SUCCESS",
      'payload': '',
      'status': 1,
      })
    except:
      self.write({
      'action': "UPDATE_CONFIG_FILE_FAIL",
      'payload': '',
      'status': 0,
      })

class UploadGcodeFileRequestHandler(RequestHandler):

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header("Access-Control-Allow-Headers", "x-requested-with")
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

  def options(self):
    pass

  def post(self):
    print("Received UploadGcodeFileRequest")
    filename = self.get_argument('filename')
    filepath = GCODE_UPLOAD_PATH + filename
    data = self.get_argument('payload')
    new_path = path = filepath
    root, ext = os.path.splitext(path)
    i = 0
    while os.path.exists(new_path):
      i += 1
      new_path = '%s_%i%s' % (root, i, ext)
    # print(new_path)
    try:
      with open(new_path, 'w') as f:
        f.write(data)
      self.write({
      'action': "UPLOAD_GCODE_FILE_SUCCESS",
      'payload': '',
      'status': 1,
      })
    except:
      self.write({
      'action': "UPLOAD_GCODE_FILE_FAIL",
      'payload': '',
      'status': 0,
      })

def make_app():
  urls = [
    ("/get_gcode_file_list", GetGcodeFileListRequestHandler),
    ("/get_gcode_file", GetGcodeFileRequestHandler),
    ("/delete_gcode_file", DeleteGcodeFileRequestHandler),
    ("/get_config_file", GetConfigFileRequestHandler),
    ("/update_gcode_file", UpdateGcodeFileRequestHandler),
    ("/update_config_file", UpdateConfigFileRequestHandler),
    ("/upload_gcode_file", UploadGcodeFileRequestHandler),
  ]

  return Application(urls, debug=True)

##the web app handles requests regarding the gcode files and the config file
def run_web_app():
  app = make_app()
  app.listen(5000)
  IOLoop.instance().start()
