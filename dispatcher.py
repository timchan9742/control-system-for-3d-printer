import os, time
import queue
import threading
from enum import Enum, IntEnum
from collections import deque
from moves import *
from globalvars import *
from instructions import *
from serialhdl import Package
from gcode import GcodeParser

class GcodeDispatcher():
    def __init__(self, printer):
        self.printer = printer
        self.toolhead = self.printer.get_object('toolhead_obj')
        self.extruder = self.printer.get_object('extruder_obj')
        self.heater_bed = self.printer.get_object('heater_bed_obj')
        self.fan = self.printer.get_object('fan_obj')
        self.serial_obj = self.printer.get_object('serial_obj')
        self.move_queue = MoveQueue(self.toolhead)
        self.new_move_queue = NewMoveQueue(self.toolhead)
        self.gcode_parser = GcodeParser(self.printer)
        self.request_queue = queue.Queue(maxsize=16) ##This buffers commands from the web client
        self.gcode_handlers = ['G0', 'G1', 'G20', 'G21', 'G28', 'G80',
        'M82', 'M83', 'M84', 'G90', 'G91', 'G92', 'M220', 'M221', 'M104', 'M106', 'M107', 'M109', 'M140', 'M190']
        self.other_handlers = ['relative_move', 'absolute_move', 'closed_loop', 'system_reset', 'motors_off', 'emergency_stop', 'comment']
        self.absolute_positioning = True
        self.absolute_extrusion = True
        self.ongoing_task = PrintTask("None")
        self.main_thread = threading.Thread(target=self.handle_client_request)
        self.register_handler_functions()
    def check_if_heaters_ready(self):
        return self.extruder.has_reached_set_temp and self.heater_bed.has_reached_set_temp
    def start_main_thread(self):
        self.main_thread.start()
    def register_handler_functions(self):
        self.func_dict = {}
        for h in self.gcode_handlers:
            fn = getattr(self, 'cmd_' + h)
            self.func_dict[h] = fn
        for h in self.other_handlers:
            fn = getattr(self, 'cmd_' + h)
            self.func_dict[h] = fn
        for h in self.printer.request_macros:
            fn = getattr(self, 'macro_' + h)
            self.func_dict[h] = fn
    def handle_client_request(self):
        while 1:
            try:
                command = self.request_queue.get(block=True, timeout=0.02)
                fn = self.func_dict[command.cmd]
                fn(command)
            except queue.Empty:
                pass
            time.sleep(0.1)
    def dispatch_print_task(self):
        while self.printer.is_ready == False:
            time.sleep(3)
        self.print_task_queue = self.printer.get_object('print_queue_obj')
        self.ongoing_task = curr_task = self.print_task_queue.queue[0]
        curr_task.parse(self.gcode_parser)
        curr_task.start_print()
        self.toolhead.toolhead_pos = [0.0, 0.0, 10.0, 0.0]
        self.printer.is_printing = True
        self.serial_obj.reset_time_for_all()
        for axis in AXIS_LIST:
            cmd_move = inst_move_with_acceleration(axis, 0, int(31250 * 2))
            package_move = Package(cmd_move, 3, 'check_default_response')
            package_move.num_of_moves = 1
            self.add_to_serial_main_queue(package_move)
        while 1:
            self.serial_obj.check_time_sync()
            command = curr_task.get_next_command()
            if command is not None:
                fn = self.func_dict[command.cmd]
                fn(command)
            else:
                self.printer.is_printing = False
                if curr_task.state == PrintState.CANCELED or curr_task.state == PrintState.COMPLETED:
                    break
                else:
                    pass
            # time.sleep(0.5)
        self.printer.is_printing = False
        self.print_task_queue.pop_task() #pop the finished task
        time.sleep(10)
        if self.print_task_queue.size > 0:
            self.print_task_queue.process_task()
    def cmd_G0(self, cmd):
        self.cmd_G1(cmd)
    def cmd_G1(self, cmd):
        while not self.check_if_heaters_ready():
            time.sleep(3)
        start_pos = self.toolhead.toolhead_pos
        end_pos = None
        if self.absolute_positioning:
            end_pos = [cmd.params.get('X', start_pos[0]), cmd.params.get('Y', start_pos[1]), cmd.params.get('Z', start_pos[2]), cmd.params.get('E', start_pos[3])]
            if not self.absolute_extrusion:
                end_pos[3] = cmd.params.get('E', 0) + start_pos[3]
        else:
            end_pos = [cmd.params.get('X', 0) + start_pos[0], cmd.params.get('Y', 0) + start_pos[1], cmd.params.get('Z', 0) + start_pos[2], cmd.params.get('E', 0) + start_pos[3]]
            if self.absolute_extrusion:
                end_pos[3] = cmd.params.get('E', start_pos[3])
        # print("from {} to {}".format(start_pos, end_pos))
        self.toolhead.speed = speed = cmd.params.get('F', self.toolhead.speed)
        new_move = NewMove(self.toolhead, start_pos, end_pos, speed)
        self.toolhead.toolhead_pos = end_pos
        self.new_move_queue.add_move(new_move)
        # new_move = Move(self.toolhead, start_pos, end_pos, speed)
        # self.toolhead.toolhead_pos = end_pos
        # self.move_queue.add_move(new_move)
    def cmd_G1_relative(self, cmd):
        start_pos = self.toolhead.toolhead_pos
        displacement = [cmd.params.get('X', 0), cmd.params.get('Y', 0), cmd.params.get('Z', 0), cmd.params.get('E', 0)]
        if self.absolute_positioning and displacement[3] == 0:
            for i in range(len(displacement)):
                if displacement[i] != 0:
                    displacement[i] = displacement[i] - start_pos[i]
        move = RelativeMove(self.toolhead, displacement)
        self.toolhead.process_unbuffered_move(move)
        self.toolhead.toolhead_pos = [start_pos[i] + displacement[i] for i in range(4)]
    def cmd_G20(self, cmd):
        pass
    def cmd_G21(self, cmd):
        self.toolhead.unit = "millimeters"
    def cmd_G28(self, cmd):
        for p in cmd.params:
            if p == 'W':
                for axis in ['X', 'Y', 'Z']:
                    self.toolhead.process_homing(axis)
            else:
                axis = p
                self.toolhead.process_homing(axis)
    def cmd_G80(self, cmd):
        print("Bed Leveling")
    def cmd_M82(self, cmd):
        self.absolute_extrusion = True
    def cmd_M83(self, cmd):
        self.absolute_extrusion = False
    def cmd_M84(self, cmd):
        self.cmd_motors_off(cmd)
        pass
    def cmd_G90(self, cmd):
        self.absolute_positioning = True
    def cmd_G91(self, cmd):
        self.absolute_positioning = False
    def cmd_G92(self, cmd):
        self.toolhead.toolhead_pos[0] = cmd.params.get('X', self.toolhead.toolhead_pos[0])
        self.toolhead.toolhead_pos[1] = cmd.params.get('Y', self.toolhead.toolhead_pos[1])
        self.toolhead.toolhead_pos[2] = cmd.params.get('Z', self.toolhead.toolhead_pos[2])
        self.toolhead.toolhead_pos[3] = cmd.params.get('E', self.toolhead.toolhead_pos[3])
    def cmd_M114(self, cmd):
        pass
    def cmd_M220(self, cmd):
        pass
    def cmd_M221(self, cmd):
        pass
    def cmd_M106(self, cmd):
        fan_power = cmd.params.get('S', 0)
        self.fan.set_fan_power(fan_power)
    def cmd_M107(self, cmd):
        self.fan.set_fan_power(0)
    def cmd_M104(self, cmd):
        target_temp = cmd.params.get('S', 0)
        # self.extruder.set_temperature(target_temp)
    def cmd_M109(self, cmd):
        target_temp = cmd.params.get('S', 0)
        # self.extruder.set_temperature_and_wait(target_temp)
    def cmd_M140(self, cmd):
        target_temp = cmd.params.get('S', 0)
        # self.heater_bed.set_temperature(target_temp)
    def cmd_M190(self, cmd):
        target_temp = cmd.params.get('S', 0)
        # self.heater_bed.set_temperature_and_wait(target_temp)
    def cmd_relative_move(self, displacement):
        move = RelativeMove(self.toolhead, displacement)
        self.toolhead.process_unbuffered_move(move)
        start_pos = self.toolhead.toolhead_pos
        self.toolhead.toolhead_pos = [start_pos[i] + displacement[i] for i in range(len(displacement))]
        print(self.toolhead.toolhead_pos)
    def cmd_absolute_move(self, destination):
        for i in range(len(destination)):
            if destination[i] == 9999: # 9999 means this axis shouldn't move, for example [100, 9999, 9999, 9999] only move X axis
                destination[i] = self.toolhead.toolhead_pos[i]
        move = AbsoluteMove(self.toolhead, destination)
        self.toolhead.process_unbuffered_move(move)
        self.toolhead.toolhead_pos = destination
        print(self.toolhead.toolhead_pos)
    def cmd_closed_loop(self, axis):
        if axis == 'A':
            for a in AXIS_LIST:
                cmd_closedloop = inst_go_to_closed_loop(a)
                package = Package(cmd_closedloop, 3, 'check_default_response')
                self.do_normal_serial_write(package)
                # self.add_to_serial_main_queue(package)
        else:
            cmd_closedloop = inst_go_to_closed_loop(axis)
            package = Package(cmd_closedloop, 3, 'check_default_response')
            self.do_normal_serial_write(package)
            # self.add_to_serial_main_queue(package)
    def cmd_system_reset(self, cmd):
        cmd_system_reset = inst_system_reset()
        package = Package(cmd_system_reset, 0, 'check_no_response')
        self.do_normal_serial_write(package)
        # self.add_to_serial_main_queue(package)
    def cmd_motors_off(self, cmd):
        cmd_disable_mosfet = inst_disable_MOSFETS(ALL_FLAG)
        package = Package(cmd_disable_mosfet, 0, 'check_no_response')
        self.do_normal_serial_write(package)
        # self.add_to_serial_main_queue(package)
    def cmd_emergency_stop(self, cmd):
        cmd_emergency_stop = inst_emergency_stop(ALL_FLAG)
        package = Package(cmd_emergency_stop, 0, 'check_no_response')
        self.do_normal_serial_write(package)
        # self.add_to_serial_main_queue(package)
    def cmd_comment(self, cmd):
        pass
    def macro_get_position(self, cmd):
        message = "X: {} Y: {} Z: {} E: {}".format(self.toolhead.toolhead_pos[0], self.toolhead.toolhead_pos[1], self.toolhead.toolhead_pos[2], self.toolhead.toolhead_pos[3])
        self.printer.add_to_message_queue(message)
    def macro_get_temperature(self, cmd):
        message = "Extruder: {}°C  Bed: {}°C".format(self.extruder.curr_temp, self.heater_bed.curr_temp)
        self.printer.add_to_message_queue(message)
    def macro_get_printer_state(self, cmd):
        pass
    def macro_get_task_queue(self, cmd):
        pass
    def macro_get_home_state(self, cmd):
        message = "X: {} Y: {} Z: {} E: {}".format(self.toolhead.home_state[0], self.toolhead.home_state[1], self.toolhead.home_state[2], self.toolhead.home_state[3])
        self.printer.add_to_message_queue(message)
    def macro_get_move_state(self, cmd):
        message = "X: {} Y: {} Z: {} E: {}".format(self.toolhead.move_state[0], self.toolhead.move_state[1], self.toolhead.move_state[2], self.toolhead.move_state[3])
        self.printer.add_to_message_queue(message)
    def do_normal_serial_write(self, package):
        self.serial_obj.write(package)
    def add_to_serial_main_queue(self, package):
        while 1:
            try:
                self.serial_obj.serial_main_queue.put(package)
                break
            except queue.Full:
                pass

DEFAULT_GCODE_FILE_DIRECTORY  = os.getcwd() + "/upload_files/"

class PrintState(Enum):
    CREATED = 0
    READY = 1
    PRINTING = 2
    SUSPENDED = 3
    COMPLETED = 4
    CANCELED = 5

class PrintTask():
    def __init__(self, name):
        self.name = name
        self.state = PrintState.CREATED
        self.start_time = time.time()
        self.finish_time = 0
        self.time_spent = 0
        self.time_left = 0
        self.minxyz = [0.0, 0.0, 0.0]
        self.maxxyz = [0.0, 0.0, 0.0]
        self.cmd_ptr = 0
        self.cmd_list = []
    def set_print_state(self, state):
        self.state = state
    def get_print_state(self):
        return self.state
    def get_next_command(self):
        if self.cmd_ptr < len(self.cmd_list) and self.state == PrintState.PRINTING:
            ptr = self.cmd_ptr
            self.cmd_ptr += 1
            return self.cmd_list[ptr]
        elif self.state == PrintState.SUSPENDED:
            return None
        elif self.state == PrintState.CANCELED:
            return None
        else:
            self.state = PrintState.COMPLETED
            self.finish_time = time.time()
            return None
    def calculate_time_spent(self):
        self.time_spent = time.time() - self.start_time
    def calculate_time_left(self):
        self.time_left = self.time_spent / self.cmd_ptr * (len(self.cmd_list) - self.cmd_ptr)
    def calculate_estimate_finish_time(self):
        pass
    def parse(self, gcode_parser):
        self.cmd_list = gcode_parser.parse_file(DEFAULT_GCODE_FILE_DIRECTORY + self.name)
        self.state = PrintState.READY
    def start_print(self):
        self.state = PrintState.PRINTING
        self.start_time = time.time()
    def resume_print(self):
        self.state = PrintState.PRINTING
    def suspend_print(self):
        self.state = PrintState.SUSPENDED
    def cancel_print(self):
        self.state = PrintState.CANCELED

class PrintTaskQueue():
    def __init__(self, printer, max_queue_size=5):
        self.printer = printer
        self.max_queue_size = max_queue_size
        self.size = 0
        self.queue = deque()
    def process_task(self):
        if self.size > 0:
            gcode_dispatcher = self.printer.get_object('gcode_dispatcher_obj')
            task_thread = threading.Thread(target=gcode_dispatcher.dispatch_print_task)
            task_thread.start()
        else:
            raise Exception("The print task queue is empty, no task to start")
    def add_task_to_front(self, task):
        if self.size < self.max_queue_size:
            self.queue.appendleft(task)
            self.size += 1
        else:
            print("The print queue is full")
    def add_task(self, task):
        if self.size < self.max_queue_size:
            self.queue.append(task)
            self.size += 1
        else:
            print("The print queue is full")
    def pop_task(self):
        pop_task = self.queue.popleft()
        self.size -= 1
    def delete_task(self, name):
        ptr = 0
        for task in self.queue:
            if task.name == name:
                break
            ptr += 1
        del self.queue[ptr]
        self.size -= 1
    def __str__(self):
        tasks = []
        for task in self.queue:
            tasks.append(task.name)
        return str(tasks)

if __name__ == "__main__":
    pass
