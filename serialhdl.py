import serial
import queue
import threading
import time
from instructions import *
from globalvars import *
from util import *

class SerialObject:
    def __init__(self, printer):
        self.printer = printer
        self.response_handler = self.printer.get_object('response_handler_obj')
        self.serial_main_queue = queue.Queue(maxsize=16) ##this buffers moves commands when print starts
        self.serial_lock = threading.Lock()
        self.port = None
        self.baudrate = 230400
        self.main_thread_flag = False
        self.sub_thread_flag = False
        self.timeout = 0.05
        self.fd_ser = None
        self.is_connected = False
        self.queue_status = {"X": 0, "Y": 0, "Z": 0, "E": 0}
        self.load_config()
        self.generate_needed_packages()
        self.create_threads()
    def create_threads(self):
        self.serial_main_thread = threading.Thread(target=self.main_thread) #the main thread deals with buffered move commands
        self.serial_sub_thread = threading.Thread(target=self.sub_thread) #the sub thread does time sync and some other stuffs
    def load_config(self):
        try:
            config = self.printer.get_object('config_obj')
            mcu_config = config.get_config('mcu')
            self.port = mcu_config.port
            self.baudrate = mcu_config.baudrate
        except:
            raise Exception("serial_obj failed to load config")
    ##pre-generate packages that is required to constantly interact with the printer
    def generate_needed_packages(self):
        self.package_get_num_of_items = {}
        self.package_enable_mosfets = {}
        self.package_reset_time = {}
        self.package_get_freq = {}
        for axis in ALL_AXIS_LIST:
            cmd_get_num_of_items = inst_get_num_of_items_in_queue(axis)
            package = Package(cmd_get_num_of_items, 4, 'check_get_num_of_items_in_queue')
            self.package_get_num_of_items[axis] = package
        for axis in ALL_AXIS_LIST:
            cmd_enable_mosfet = inst_enable_MOSFETS(axis)
            package = Package(cmd_enable_mosfet, 3, 'check_default_response')
            self.package_enable_mosfets[axis] = package
        for axis in ALL_AXIS_LIST:
            cmd_reset_time = inst_reset_time(axis)
            package = Package(cmd_reset_time, 3, 'check_default_response')
            self.package_reset_time[axis] = package
        for axis in ALL_AXIS_LIST:
            cmd_get_freq = inst_get_update_frequency(axis)
            package = Package(cmd_get_freq, 7, 'check_get_update_frequency_response')
            self.package_get_freq[axis] = package
        cmd_get_extruder_temp = inst_get_extruder_temperature(EXTRUDER_TEMP_CONTROL_FLAG)
        self.package_get_extruder_temp = Package(cmd_get_extruder_temp, 5, 'check_get_extruder_temp_response')
        cmd_get_bed_temp = inst_get_bed_temperature(BED_TEMP_CONTROL_FLAG)
        self.package_get_bed_temp = Package(cmd_get_bed_temp, 5, 'check_get_bed_temp_response')
    def connect(self):
        try:
            fd_ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            if fd_ser.is_open:
                self.fd_ser = fd_ser
                self.is_connected = True
                print("Successfully connect to serial port:", self.port)
                self.printer.add_to_message_queue("Successfully connect to serial port: {}".format(self.port))
                self.main_thread_flag = True
                self.sub_thread_flag = True
                self.start_sub_thread()
                self.start_main_thread()
        except Exception as e:
            print(e)
            self.printer.add_to_message_queue("Failed to connect to serial port {}".format(self.port))
    def do_system_reset(self):
        cmd_system_reset = inst_system_reset()
        package_system_reset = Package(cmd_system_reset, 0, 'check_no_response')
        self.write(package_system_reset)
        time.sleep(2)
    def reset_time_for_all(self):
        self.printer.start_time = time.time()
        for axis in AXIS_LIST:
            cmd_reset_time = inst_reset_time(axis)
            package_reset_time = Package(cmd_reset_time, 3, 'check_default_response')
            self.write(package_reset_time)
        time.sleep(1)
    def check_temperatures(self):
        if self.printer.get_master_time() - self.printer.last_sync_time > 700000:
            with self.serial_lock:
                self.fd_ser.write(self.package_get_extruder_temp.payload)
            with self.serial_lock:
                self.fd_ser.write(self.package_get_bed_temp.payload)
    def check_time_sync(self):
        if self.printer.get_master_time() - self.printer.last_sync_time > 50000: #do time sync 10 times a second
            cmd_time_sync = inst_time_sync(255, self.printer.get_master_time())
            package_time_sync = Package(cmd_time_sync, 0, 'check_no_response')
            with self.serial_lock:
                # print("[time-sync]: ", package_time_sync.payload)
                self.fd_ser.write(package_time_sync.payload)
            self.printer.last_sync_time = self.printer.get_master_time()
    def check_time_sync_with_response(self):
        if self.printer.get_master_time() - self.printer.last_sync_time > 50000:
            cmd_time_sync = inst_time_sync('E', self.printer.get_master_time())
            package_time_sync = Package(cmd_time_sync, 9, 'check_time_sync_response')
            with self.serial_lock:
                print("[time-sync]: ", package_time_sync.payload)
                self.fd_ser.write(package_time_sync.payload)
                resp = self.fd_ser.read(package_time_sync.resp_size)
                time_error, RCC_ICSCR = self.response_handler.check_time_sync_response(resp)
            self.printer.last_sync_time = self.printer.get_master_time()
    def write(self, package, print_detail=True): ##this function writes non-move or unbuffered-move commands
        with self.serial_lock:
            self.fd_ser.write(package.payload)
            start_time = time.time()
            resp = self.fd_ser.read(package.resp_size)
            if print_detail:
                print("[SER_SUB] write: ", package.payload)
                print("[SER_SUB] read: ", resp)
                print()
            fn = getattr(self.response_handler, package.resp_handler)
            fn(resp)
    def write_moves(self, package, print_detail=True):##this function writes !only buffered-move! commands
        start_time = time.time()
        axis = package.axis
        while 1:
            package_get_num_of_item = self.package_get_num_of_items[axis]
            with self.serial_lock:
                self.fd_ser.write(package_get_num_of_item.payload)
                resp = self.fd_ser.read(package_get_num_of_item.resp_size)
                num_of_items = self.response_handler.check_get_num_of_items_in_queue(resp, axis)
                print("items in queue[{}]: {}".format(axis, num_of_items))
                if num_of_items is None:
                    exit(1)
                else:
                    if 32 - num_of_items - 1 > package.num_of_moves:
                        break
        with self.serial_lock:
            print("[SER_MAIN] write {} moves: {}".format(package.num_of_moves, axis))
            self.fd_ser.write(package.payload)
            resp = self.fd_ser.read(package.resp_size)
            print("[SER_MAIN] read: ", resp)
            fn = getattr(self.response_handler, package.resp_handler)
            if fn(resp):
                ##update toolhead's actual position
                toolhead_obj = self.printer.get_object("toolhead_obj")
                toolhead_obj.toolhead_curr_move_speed = package.speed_in_this_move
                toolhead_obj.toolhead_actual_pos = package.pos_after_this_move
                pass
            else:
                exit(1)
        print("time taken(Move): {}".format(time.time() - start_time))
        print()
    def start_sub_thread(self):
        self.serial_sub_thread.start()
    def start_main_thread(self):
        self.serial_main_thread.start()
    def sub_thread(self):
        if True:
            # reset
            cmd_system_reset = inst_system_reset()
            package_reset = Package(cmd_system_reset, 0, 'check_no_response')
            self.write(package_reset)
            time.sleep(1)
            self.reset_time_for_all()
            self.printer.is_ready = True

            # constanly time-sync with printer and check temperatures
            while 1:
                self.check_time_sync_with_response()
                self.check_temperatures()
        else:
            pass
    def main_thread(self):
        while 1:
            if self.printer.is_printing:
                try:
                    package = self.serial_main_queue.get(block=True, timeout=0.05)
                    self.write_moves(package)
                except queue.Empty:
                    pass
            else:
                pass

class Package:
    def __init__(self, payload, resp_size, resp_handler='check_default_response'):
        self.axis = chr(payload[0])
        self.payload = payload
        self.resp_size = resp_size #number of bytes to read from the response
        self.resp_handler = resp_handler
        self.num_of_moves = 0 #non-zero if it is a move instruction
        self.pos_after_this_move = None
        self.speed_in_this_move = 0
