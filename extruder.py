from util import *
from instructions import *
from globalvars import *
from serialhdl import Package

TEMP_TOLERANCE = 2

class Extruder():
    def __init__(self, printer):
        self.printer = printer
        self.serial_obj = self.printer.get_object('serial_obj')
        self.curr_temp = 0
        self.set_temp = 0
        self.is_powered = False
        self.has_reached_extrusion_temp = False
        self.has_reached_set_temp = False
        self.min_temp = 0
        self.max_temp = 0
        self.min_extrude_temp = 0
        self.load_config()
    def load_config(self):
        try:
            config = self.printer.get_object('config_obj')
            extruder_config = config.get_config('extruder')
            self.min_temp = extruder_config.min_temp
            self.max_temp = extruder_config.max_temp
            self.min_extrude_temp = extruder_config.min_extrude_temp
        except:
            raise Exception("extruder_obj failed to load config")
    def exclusive_move(self, m):
        cmd_update_speed = inst_move_with_velocity(E_AXIS, 0, 1)
        cmd_accel = inst_move_with_acceleration(E_AXIS, int(m.axis_accel[3]) * self.RATIO, int(m.accel_t * self.mcu_freq))
        cmd_cruise = inst_move_with_acceleration(E_AXIS, 0, int(m.cruise_t * self.mcu_freq))
        cmd_decel = inst_move_with_acceleration(E_AXIS, int(m.axis_decel[3]) * self.RATIO, int(m.decel_t * self.mcu_freq))
        package_update_speed = Package(cmd_update_speed, 3, 'check_default_response')
        package_accel = Package(cmd_accel, 3, 'check_default_response')
        package_cruise = Package(cmd_cruise, 3, 'check_default_response')
        package_decel = Package(cmd_decel, 3, 'check_default_response')
        self.add_to_serial_main_queue(package_update_speed)
        self.add_to_serial_main_queue(package_accel)
        self.add_to_serial_main_queue(package_cruise)
        self.add_to_serial_main_queue(package_decel)
    def move(self, accel, time_steps):
        cmd_move = inst_move_with_acceleration(E_AXIS, accel, time_steps)
        package_move = Package(cmd_move, 3, 'check_default_response')
        self.add_to_serial_main_queue(package_move)
    def check_temperature(self, target_temp):
        if target_temp > self.max_temp:
            self.printer.add_to_message_queue('Temperature set exceeds max extrusion temperature {} >>>>>>'.format(self.max_temp))
            return False
        else:
            return True
    def set_temperature(self, target_temp):
        if self.check_temperature(target_temp):
            self.set_temp = target_temp
            if target_temp == 0:
                self.is_powered = False
            else:
                self.is_powered = True
                target_temp = temperature_to_analog_val(target_temp)
            cmd_set_extruder_temp = inst_set_extruder_temperature(TEMP_CONTROL_FLAG, int(target_temp))
            package = Package(cmd_set_extruder_temp, 3, 'check_default_response')
            self.do_normal_serial_write(package)
    def set_temperature_and_wait(self, target_temp):
        if self.check_temperature(target_temp):
            self.set_temp = target_temp
            if target_temp == 0:
                self.is_powered = False
            else:
                self.is_powered = True
                target_temp = temperature_to_analog_val(target_temp)
            cmd_set_extruder_temp = inst_set_extruder_temperature(TEMP_CONTROL_FLAG, int(target_temp))
            package = Package(cmd_set_extruder_temp, 3, 'check_default_response')
            self.do_normal_serial_write(package)
            self.has_reached_set_temp = False
    def update_temperature(self, val):
        self.curr_temp = analog_val_to_temperature(val)
        # print("extruder_temp: {}".format(self.curr_temp))
        if self.curr_temp >= self.set_temp:
            self.has_reached_set_temp = True
        if self.curr_temp >= self.min_extrude_temp:
            self.has_reached_extrusion_temp = True
    def do_normal_serial_write(self, package):
        self.serial_obj.write(package)
    def add_to_serial_main_queue(self, package):
        while 1:
            try:
                self.serial_obj.serial_main_queue.put(package)
                break
            except queue.Full:
                pass

class HeaterBed():
    def __init__(self, printer):
        self.printer = printer
        self.serial_obj = self.printer.get_object('serial_obj')
        self.curr_temp = 0
        self.set_temp = 0
        self.is_powered = False
        self.has_reached_set_temp = False
        self.min_temp = 0
        self.max_temp = 0
        self.load_config()
    def load_config(self):
        try:
            config = self.printer.get_object('config_obj')
            bed_config = config.get_config('heater_bed')
            self.min_temp = bed_config.min_temp
            self.max_temp = bed_config.max_temp
        except:
            raise Exception("heater_bed_obj failed to load config")
    def check_temperature(self, target_temp):
        if target_temp > self.max_temp:
            self.printer.add_to_message_queue('Temperature set exceeds max bed temperature {} >>>>>>'.format(self.max_temp))
            return False
        else:
            return True
    def set_temperature(self, target_temp):
        if self.check_temperature(target_temp):
            self.set_temp = target_temp
            if target_temp == 0:
                self.is_powered = False
            else:
                self.is_powered = True
                target_temp = temperature_to_analog_val(target_temp)
            cmd_set_bed_temp = inst_set_bed_temperature(TEMP_CONTROL_FLAG, int(target_temp))
            package = Package(cmd_set_bed_temp, 3, 'check_default_response')
            self.do_normal_serial_write(package)
    def set_temperature_and_wait(self, target_temp):
        if self.check_temperature(target_temp):
            self.set_temp = target_temp
            if target_temp == 0:
                self.is_powered = False
            else:
                self.is_powered = True
                target_temp = temperature_to_analog_val(target_temp)
            cmd_set_bed_temp = inst_set_bed_temperature(TEMP_CONTROL_FLAG, int(target_temp))
            package = Package(cmd_set_bed_temp, 3, 'check_default_response')
            self.do_normal_serial_write(package)
            self.has_reached_set_temp = False
    def update_temperature(self, val):
        self.curr_temp = analog_val_to_temperature(val)
        # print("bed_temp: {}".format(self.curr_temp))
        if self.curr_temp >= self.set_temp:
            self.has_reached_set_temp = True
    def do_normal_serial_write(self, package):
        self.serial_obj.write(package)
    def add_to_serial_main_queue(self, package):
        while 1:
            try:
                self.serial_obj.serial_main_queue.put(package)
                break
            except queue.Full:
                pass

class Fan():
    def __init__(self, printer):
        self.printer = printer
        self.serial_obj = self.printer.get_object('serial_obj')
        self.is_powered = False
        self.curr_power = 0
    def set_fan_power(self, power):
        if power == 0:
            self.is_powered = False
        else:
            self.is_powered = True
        self.curr_power = power
        return

if __name__ == '__main__':
    pass
