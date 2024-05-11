import time, math
from logger import FileLogger
from toolhead import ToolHead
from responsehdl import ResponseHandler
from serialhdl import SerialObject
from extruder import Extruder, HeaterBed, Fan
from dispatcher import GcodeDispatcher, PrintTaskQueue
from webhooks import WebServer
from configloader import ConfigLoader
from globalvars import *

class Printer:
    def __init__(self):
        self.running = False
        self.is_ready = False
        self.is_printing = False
        self.start_time = time.time()
        self.last_sync_time = 0
        self.objects = {}
        self.request_macros = request_macros
        self.gcode_macros = {}
    def get_master_time(self):
        return (time.time() - self.start_time) * 1000000 ##in microseconds
    def get_last_sync_time(self):
        return self.last_sync_time
    def add_object(self, name, obj):
        if self.objects.get(name):
            raise Exception("object {} already exists".format(name))
        self.objects[name] = obj
        print("add {} to printer class".format(name))
    def get_object(self, name):
        try:
            return self.objects[name]
        except:
            raise Exception("object {} not found in printer class".format(name))
    def load_config(self):
        try:
            config = self.get_object('config_obj')
            gcode_macro_config = config.get_config('gcode_macro')
            self.gcode_macros = gcode_macro_config.gcode_macros
        except:
            raise Exception("printer_obj failed to load config")
    def add_required_objects(self):
        self.add_object('logger_obj', FileLogger())
        self.add_object('message_queue_obj', MessageQueue())
        self.add_object('config_obj', ConfigLoader(self))
        self.add_object('response_handler_obj', ResponseHandler(self))
        self.add_object('serial_obj', SerialObject(self))
        self.add_object('toolhead_obj', ToolHead(self))
        self.add_object('fan_obj', Fan(self))
        self.add_object('extruder_obj', Extruder(self))
        self.add_object('heater_bed_obj', HeaterBed(self))
        self.add_object('print_queue_obj', PrintTaskQueue(self))
        self.add_object('gcode_dispatcher_obj', GcodeDispatcher(self))
        self.add_object('webserver_obj', WebServer(self))
    def load_config_all(self):
        #load all the necessary configs
        object_names = ['serial_obj', 'toolhead_obj', 'extruder_obj', 'heater_bed_obj']
        for name in object_names:
            obj = self.get_object(name)
            obj.load_config()
    def run(self):
        self.add_required_objects()
        self.load_config()
        time.sleep(1)
        self.running = True
        serial_obj = self.get_object('serial_obj')
        serial_obj.connect()
        gcode_dispatcher = self.get_object('gcode_dispatcher_obj')
        gcode_dispatcher.start_main_thread()
        webserver_obj = self.get_object('webserver_obj')
        webserver_obj.start_server()
    def program_restart(self):
        os.execl(sys.executable, sys.executable, *sys.argv)
    def shutdown(self):
        self.running = False
    def add_to_message_queue(self, message):
        message_queue_obj = self.get_object('message_queue_obj')
        message_queue_obj.add_message(message)

from collections import deque
import threading

class MessageQueue():
    def __init__(self):
        self.queue = deque()
        self.message_queue_lock = threading.Lock()
        self.size = 0
    def add_message(self, message):
        with self.message_queue_lock:
            self.queue.append(message)
            self.size += 1
    def get_message(self):
        if self.size > 0:
            with self.message_queue_lock:
                popped_message = self.queue.popleft()
                self.size -= 1
                return popped_message
        return ''
