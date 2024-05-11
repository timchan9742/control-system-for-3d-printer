import asyncio
import websockets
import json
import os
import random
from gcode import GcodeParser, GCodeCommand
from dispatcher import PrintTask, PrintState


##the WebServer handles requests from the web interface
class WebServer:
    def __init__(self, printer):
        self.printer = printer
        self.webhandler = WebHandler(self.printer)
    async def handler(self, websocket, path):
        while 1:
            package = await websocket.recv()
            data = json.loads(package)
            ##for debug purpose
            # print("receive: {}".format(data))
            resp = self.handle_request_from_web_client(data)
            if resp:
                await websocket.send(resp)
    def handle_request_from_web_client(self, data):
        try:
            command_in_lower_case = data['type'].lower()
            fn = getattr(self.webhandler, "handle_" + command_in_lower_case)
            resp = fn(data)
            return resp
        except:
            return None
    def start_server(self):
        print("Starting server...")
        start_server = websockets.serve(self.handler, "0.0.0.0", 8000)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server)
        loop.run_forever()

class WebHandler():
    def __init__(self, printer):
        self.printer = printer
        self.upload_path = None
        self.toolhead_obj = self.printer.get_object('toolhead_obj')
        self.dispatcher_obj = self.printer.get_object('gcode_dispatcher_obj')
        self.print_task_queue = self.printer.get_object('print_queue_obj')
    def write_file(self, data):
        try:
            with open(self.upload_path, "a") as f:
                f.write(data['payload'])
        except:
            raise Exception("Open file error")
    def handle_get_printer_info(self, data):

        message_queue_obj = self.printer.get_object('message_queue_obj')
        print_queue = self.printer.get_object('print_queue_obj')
        extruder_temp = self.printer.get_object('extruder_obj').curr_temp
        extruder_set_temp = self.printer.get_object('extruder_obj').set_temp
        bed_temp = self.printer.get_object('heater_bed_obj').curr_temp
        bed_set_temp = self.printer.get_object('heater_bed_obj').set_temp
        fan_power = self.printer.get_object('fan_obj').curr_power
        # if run on a raspberry pi
        # from gpiozero import CPUTemperature
        # cpu = CPUTemperature()
        # pi_temp = cpu.temperature

        message = message_queue_obj.get_message()
        position = self.toolhead_obj.toolhead_pos
        max_accel = self.toolhead_obj.max_accel
        max_decel = self.toolhead_obj.max_decel
        move_speed = self.toolhead_obj.toolhead_curr_move_speed
        move_state = [False, False, False, False]
        home_state = [False, False, False, False]
        ongoing_task = self.dispatcher_obj.ongoing_task
        is_printing = self.printer.is_printing
        task_list = []

        if print_queue.queue:
            for task in print_queue.queue:
                if task.state == PrintState.PRINTING:
                    task.calculate_time_spent()
                    task.calculate_time_left()
                dict = {'name': task.name, 'state': task.state.value, 'start_time': task.start_time,
                       'finish_time': task.finish_time, 'time_spent': task.time_spent, 'time_left': task.time_left}
                task_list.append(dict)
        else:
            pass

        ##these are some random parameters for testing
        extruder_temp = random.randint(226, 230)
        extruder_set_temp = random.randint(226, 230)
        bed_temp = random.randint(78, 80)
        bed_set_temp = random.randint(78, 80)
        pi_temp = random.randint(49, 50)
        position = [random.randint(0, 250), random.randint(0, 250), random.randint(2, 2), 0]

        resp = {"action": "UPDATE_PRINTER_INFO",
               "payload": {
                   "isPrinting": is_printing,
                   "extruder": {
                   "temp": extruder_temp,
                   "setTemp": extruder_set_temp,
                   "isPowered": False
                   },
                   "bed": {
                   "temp": bed_temp,
                   "setTemp": bed_set_temp,
                   "isPowered": False
                   },
                   "pi": {
                   "temp": pi_temp
                   },
                   "fan": {
                   "power": fan_power,
                   "isPowered": False
                   },
                   "toolhead": {
                   "position": position,
                   "maxAccel": max_accel,
                   "maxDecel": max_decel,
                   "moveSpeed": move_speed,
                   "moveState": move_state,
                   "homeState": home_state
                   },
                   "taskQueue": task_list,
                   "message": message
                }
               }
        resp = json.dumps(resp)
        return resp
    def handle_gcode_macro(self, data):
        gcode_command = GCodeCommand(data['payload'])
        gcode_command.cmd = data['payload']
        self.add_to_dispatcher_request_queue(gcode_command)
        return None
    def handle_gcode_command(self, data):
        lines = data['payload'].split('\n') ##this could contain more than one Gcode commands
        gcode_parser = GcodeParser(self.printer)
        try:
            for l in lines:
                gcode_command = gcode_parser.parse_line(l, -1)
                self.add_to_dispatcher_request_queue(gcode_command)
        except:
            pass
        del gcode_parser
        return None
    def handle_gcode_file_request(self, data):
        file_list = []
        for file in os.listdir(os.getcwd() + UPLOAD_PATH):
            if file == ".DS_Store":
                continue
            file_list.append(file)
        resp = {"action": "UPDATE_FILE_LIST", "gcodeFileList": file_list}
        resp = json.dumps(resp)
        return resp
    def handle_set_extruder_temperature(self, data):
        target_temp = int(data['payload'])
        self.printer.get_object('extruder_obj').set_temperature(target_temp)
        return None
    def handle_set_bed_temperature(self, data):
        target_temp = int(data['payload'])
        self.printer.get_object('heater_bed_obj').set_temperature(target_temp)
        return None
    def handle_heaters_off(self, data):
        self.printer.get_object('extruder_obj').set_temperature(0)
        self.printer.get_object('heater_bed_obj').set_temperature(0)
        return None
    def handle_get_temperature_all(self, data):
        extruder_temp = int(self.printer.get_object('extruder_obj').curr_temp)
        bed_temp = int(self.printer.get_object('heater_bed_obj').curr_temp)
        pi_temp = 0
        # if run on a raspberry pi
        # from gpiozero import CPUTemperature
        # cpu = CPUTemperature()
        # pi_temp = cpu.temperature
        resp = {"action": "UPDATE_TEMPERATURE", "temperature": {
          "extruder": extruder_temp,
          "bed": bed_temp,
          "pi": pi_temp
        }}
        resp = json.dumps(resp)
        return resp
    def handle_get_position_all(self, data):
        position = self.toolhead_obj.toolhead_pos
        resp = {"action": "UPDATE_POSITION", "position": {
          "x": position[0],
          "y": position[1],
          "z": position[2],
          "e": position[3]
        }}
        resp = json.dumps(resp)
        return resp
    def handle_set_max_acceleration(self, data):
        self.toolhead_obj.max_accel = int(data['payload'])
        return None
    def handle_set_max_deceleration(self, data):
        self.toolhead_obj.max_decel = int(data['payload'])
        return None
    def handle_relative_move(self, data):
        if not self.printer.is_printing:
            self.dispatcher_obj.cmd_relative_move(data['payload'])
        return None
    def handle_absolute_move(self, data):
        if not self.printer.is_printing:
            self.dispatcher_obj.cmd_absolute_move(data['payload'])
        return None
    def handle_add_print(self, data):
        filename = data['payload']
        print_task = PrintTask(filename)
        self.print_task_queue.add_task(print_task)
        return None
    def handle_start_print(self, data):
        filename = data['payload']
        print_task = PrintTask(filename)
        self.print_task_queue.add_task(print_task)
        self.print_task_queue.process_task()
        return None
    def handle_resume_print(self, data):
        self.print_task_queue.queue[0].resume_print()
        self.printer.is_printing = True
        return None
    def handle_pause_print(self, data):
        self.print_task_queue.queue[0].suspend_print()
        self.printer.is_printing = False
        return None
    def handle_cancel_print(self, data):
        self.print_task_queue.queue[0].cancel_print()
        self.printer.is_printing = False
        return None
    def handle_closedloop(self, data):
        self.dispatcher_obj.cmd_closed_loop(data['payload'])
        return None
    def handle_motors_off(self, data):
        self.dispatcher_obj.cmd_motors_off(None)
        return None
    def handle_emergency_stop(self, data):
        self.dispatcher_obj.cmd_emergency_stop(None)
        return None
    def handle_system_reset(self, data):
        self.dispatcher_obj.cmd_system_reset(None)
        return None
    def handle_program_restart(self, data):
        self.printer.program_restart()
        return None
    def add_to_dispatcher_request_queue(self, event):
        try:
            self.dispatcher_obj.request_queue.put(event)
        except queue.Full:
            pass
