from moves import *
from globalvars import *
from instructions import *
from serialhdl import Package
import math, time

multi_move_threshold = 6
move_type = 0
move_type_ptr = 0
value_list = [[] for i in range(len(AXIS_LIST))]
time_list = []
total_time = 0
count = 0

class ToolHead():
    def __init__(self, printer):
        self.printer = printer
        self.serial_obj = self.printer.get_object('serial_obj')
        self.microsteps_per_revolution = 360 * 256 * 7
        self.unit = "millimeters"
        self.junction_deviation = 0.0
        self.toolhead_pos = [0.0, 0.0, 0.0, 0.0] #the current position for processing moves since moves are buffered
        self.toolhead_actual_pos = [0.0, 0.0, 0.0, 0.0] #the actual position of the toolhead, updated when a move or moves have been sent and received
        self.move_state = [False, False, False, False]
        self.home_state = [False, False, False, False]
        self.speed = 600.0
        self.toolhead_curr_move_speed = 0
        self.load_config()
    def load_config(self):
        try:
            config = self.printer.get_object('config_obj')
            printer_config = config.get_config('printer')
            mcu_config = config.get_config('mcu')
            stepper_x_config = config.get_config('stepper_x')
            stepper_y_config = config.get_config('stepper_y')
            stepper_z_config = config.get_config('stepper_z')
            extruder_config = config.get_config('extruder')
            self.mcu_freq = mcu_config.mcu_update_frequency
            self.max_accel = printer_config.max_accel
            self.max_decel = printer_config.max_decel
            self.max_velocity = printer_config.max_velocity
            self.max_z_accel = printer_config.max_z_accel
            self.max_z_velocity = printer_config.max_z_velocity
            self.min_position = [stepper_x_config.min_position, stepper_y_config.min_position, stepper_z_config.min_position]
            self.max_position = [stepper_x_config.max_position, stepper_y_config.max_position, stepper_z_config.max_position]
            self.home_dir = [stepper_x_config.home_dir, stepper_y_config.home_dir, stepper_z_config.home_dir]
            self.home_speed = [stepper_x_config.home_speed, stepper_y_config.home_speed, stepper_z_config.home_speed]
            self.max_home_distance = [stepper_x_config.max_home_distance, stepper_y_config.max_home_distance, stepper_z_config.max_home_distance]
            self.max_home_time = [stepper_x_config.max_home_time, stepper_y_config.max_home_time, stepper_z_config.max_home_time]
            self.mm_per_revolution = [stepper_x_config.rotation_distance, stepper_y_config.rotation_distance, stepper_z_config.rotation_distance, extruder_config.rotation_distance]
            self.microsteps_per_mm = [(self.microsteps_per_revolution / x) for x in self.mm_per_revolution]
            self.ratio = [(x / self.mcu_freq) for x in self.microsteps_per_mm]
            self.square_corner_velocity = printer_config.square_corner_velocity
            self.cal_junction_deviation()
        except:
            raise Exception("toolhead_obj failed to load config")
    def set_max_acceleration(self, max_accel):
        self.max_accel = max_accel
    def set_max_deceleration(self, max_decel):
        self.max_decel = max_decel
    def convert_time(self, time): ##from second to micro_timestep
        return int(time * self.mcu_freq)
    def convert_velocity(self, vel, i):
        # return int(vel * self.ratio[i] * 2**20)
        return int(vel * self.microsteps_per_mm[i] / self.mcu_freq * 2**20)
    def convert_acceleration(self, accel, i):
        return int(accel * self.microsteps_per_mm[i] / (self.mcu_freq * self.mcu_freq) * 2**24)
    def convert_displacement(self, disp, i):
        return int(disp * self.microsteps_per_mm[i])
    def cal_junction_deviation(self):
        self.junction_deviation = self.square_corner_velocity * (math.sqrt(2.) - 1.) / self.max_accel
    def process_moves_all(self, moves):  ##process all buffered moves in the move queue
        global move_type
        global move_type_ptr
        global value_list
        global time_list
        global total_time
        global count
        global multi_move_threshold
        for m in moves:
            if False:
                pass
            else:
                for i in range(len(AXIS_LIST)):
                    j = ALL_AXIS_LIST.index(AXIS_LIST[i])
                    value_list[i].append(self.convert_velocity(m.axis_start_v[j], j))
                    if m.accel_t > 0:
                        value_list[i].append(self.convert_acceleration(m.axis_accel[j], j))
                    if m.cruise_t > 0:
                        value_list[i].append(0)
                    if m.decel_t > 0:
                        value_list[i].append(self.convert_acceleration(m.axis_decel[j], j))
                # print("start_v: {} accel: {}  decel: {}".format(m.axis_start_v, m.axis_accel, m.axis_decel))
                valid_move_count = 1
                time_list.append(1)
                if m.accel_t > 0:
                    time_list.append(int(m.accel_t * self.mcu_freq))
                    valid_move_count += 1
                if m.cruise_t > 0:
                    time_list.append(int(m.cruise_t * self.mcu_freq))
                    valid_move_count += 1
                if m.decel_t > 0:
                    time_list.append(int(m.decel_t * self.mcu_freq))
                    valid_move_count += 1
                move_type |= 1 << move_type_ptr
                move_type_ptr += valid_move_count

                # for i in range(len(AXIS_LIST)):
                #     j = ALL_AXIS_LIST.index(AXIS_LIST[i])
                #     value_list[i].append(self.convert_velocity(m.axis_start_v[j]))
                #     value_list[i].append(self.convert_acceleration(m.axis_accel[j]))
                #     value_list[i].append(0)
                #     value_list[i].append(self.convert_acceleration(m.axis_decel[j]))
                # time_list.append(2)
                # time_list.append(int(m.accel_t * self.mcu_freq))
                # time_list.append(int(m.cruise_t * self.mcu_freq))
                # time_list.append(int(m.decel_t * self.mcu_freq))
                # move_type |= 1 << move_type_ptr
                # move_type_ptr += 4

                if len(time_list) >= multi_move_threshold:
                    packages = [None] * len(AXIS_LIST)
                    for i in range(len(AXIS_LIST)):
                        cmd_multi_move = inst_multi_move(AXIS_LIST[i], len(time_list), move_type, value_list[i], time_list)
                        packages[i] = Package(cmd_multi_move, 3, 'check_default_response')
                        packages[i].num_of_moves = len(time_list)
                        # print("sum_time: {}".format(sum(time_list) / self.mcu_freq))
                    for i in range(len(AXIS_LIST)):
                        self.add_to_serial_main_queue(packages[i])
                    sum_time = sum(time_list) / self.mcu_freq
                    move_type = 0
                    move_type_ptr = 0
                    value_list = [[] for i in range(len(AXIS_LIST))]
                    time_list = []
    def process_move(self, move): ##process a single move
        move_type = 0
        value_list = [[] for i in range(len(AXIS_LIST))]
        time_list = []
        for i in range(len(AXIS_LIST)):
            value_list[i].append(self.convert_velocity(m.axis_start_v[i]))
            value_list[i].append(self.convert_acceleration(m.axis_accel[i]))
            value_list[i].append(0)
            value_list[i].append(self.convert_acceleration(m.axis_decel[i]))
        move_type |= 1 << 0
        time_list.append(1)
        time_list.append(int(m.accel_t * self.mcu_freq))
        time_list.append(int(m.cruise_t * self.mcu_freq))
        time_list.append(int(m.decel_t * self.mcu_freq))
        packages = [None] * len(AXIS_LIST)
        for i in range(len(AXIS_LIST)):
            cmd_multi_move = inst_multi_move(AXIS_LIST[i], 4, move_type, value_list[i], time_list)
            packages[i] = Package(cmd_multi_move, 3, 'check_default_response')
        for i in range(len(AXIS_LIST)):
            self.add_to_serial_main_queue(packages[i])
    def process_unbuffered_move(self, move): ##process a trapezoid move
        for idx, axis in enumerate(ALL_AXIS_LIST):
            j = ALL_AXIS_LIST.index(axis)
            displacement = self.convert_displacement(move.displacement[idx], j)
            time = self.convert_time(move.time[idx])
            if time > 0 and axis in AXIS_LIST:
                cmd_move = inst_trapezoid_move(axis, displacement, time)
                package = Package(cmd_move, 3, 'check_default_response')
                self.do_normal_serial_write(package)
    def process_homing(self, axis):
        j = ALL_AXIS_LIST.index(axis)
        max_home_distance = self.max_home_distance[j]
        max_home_distance = self.convert_displacement(max_home_distance, j)
        max_home_time = self.max_home_time[j]
        max_home_time = self.convert_time(max_home_time)
        if not self.home_dir[j]:
            max_home_distance = -max_home_distance
        cmd_homing = inst_do_homing(axis, max_home_distance, max_home_time);
        package_homing = Package(cmd_homing, 3, 'check_default_response')
        self.do_normal_serial_write(package_homing)
        idx = ['X', 'Y', 'Z'].index(axis)
        self.toolhead_pos[idx] = 0.0
        self.home_state[j] = True
    def do_normal_serial_write(self, package):
        self.serial_obj.write(package)
    def add_to_serial_main_queue(self, package):
        while 1:
            try:
                self.serial_obj.serial_main_queue.put(package)
                break
            except queue.Full:
                pass
