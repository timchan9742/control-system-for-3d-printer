from util import *
from gcode import GcodeParser

class MCUConfig():
    def __init__(self):
        self.attr_list = ['port', 'baudrate', 'mcu_update_frequency']
        self.port = ''
        self.baudrate = 230400
        self.mcu_update_frequency = 31250
    def check_type(self, attr, value):
        if attr == 'port':
            setattr(self, attr, value)
        elif attr in ['baudrate', 'mcu_update_frequency']:
            if get_int(value):
                setattr(self, attr, int(value))
            else:
                raise Exception('type match error: attribute {} and value {} does not match'.format(attr, value))
    def __str__(self):
        pass

class PrinterConfig():
    def __init__(self):
        self.attr_list = ['max_accel', 'max_decel', 'max_z_accel', 'max_velocity', 'max_z_velocity', 'square_corner_velocity']
        self.max_accel = 2500
        self.max_decel = 2500
        self.max_z_accel = 1500
        self.max_velocity = 100
        self.max_z_velocity = 50
        self.square_corner_velocity = 5
    def check_type(self, attr, value):
        if attr in ['max_accel', 'max_decel', 'max_z_accel', 'max_velocity', 'max_z_velocity', 'square_corner_velocity']:
            if get_int(value) or get_float(value):
                setattr(self, attr, float(value))
            else:
                raise Exception('type match error: attribute {} and value {} does not match'.format(attr, value))
    def __str__(self):
        pass

class ExtruderConfig():
    def __init__(self):
        self.attr_list = ['min_temp', 'max_temp', 'min_extrude_temp', 'nozzle_diameter', 'filament_diameter', 'rotation_distance']
        self.min_temp = 0
        self.max_temp = 270
        self.min_extrude_temp = 170
        self.rotation_distance = 10
    def check_type(self, attr, value):
        if attr in ['min_temp', 'max_temp', 'min_extrude_temp']:
            if get_int(value) or get_float(value):
                setattr(self, attr, int(value))
            else:
                raise Exception('type match error: attribute {} and value {} does not match'.format(attr, value))
        elif attr in ['nozzle_diameter', 'filament_diameter', 'rotation_distance']:
            if get_float(value):
                setattr(self, attr, float(value))
            else:
                raise Exception('type match error: attribute {} and value {} does not match'.format(attr, value))
    def __str__(self):
            pass

class HeaterBedConfig():
    def __init__(self):
        self.attr_list = ['min_temp', 'max_temp']
        self.min_temp = 0
        self.max_temp = 100
    def check_type(self, attr, value):
        if attr in ['min_temp', 'max_temp']:
            if get_int(value) or get_float(value):
                setattr(self, attr, int(value))
            else:
                raise Exception('type match error: attribute {} and value {} does not match'.format(attr, value))
    def __str__(self):
        pass

class StepperConfig():
    def __init__(self):
        self.attr_list = ['microsteps', 'min_position', 'max_position', 'home_speed', 'home_dir', 'max_home_distance', 'max_home_time', 'rotation_distance']
        self.microsteps = None
        self.min_position = 0
        self.max_position = 0
        self.home_speed = 10
        self.home_dir = False
        self.max_home_distance = 0
        self.max_home_time = 0
        self.rotation_distance = 10
    def check_type(self, attr, value):
        if attr in ['microsteps', 'min_position', 'max_position', 'home_speed', 'max_home_distance', 'max_home_time']:
            if get_int(value) or get_float(value):
                setattr(self, attr, int(value))
            else:
                raise Exception('type match error: attribute {} and value {} does not match'.format(attr, value))
        elif attr in ['rotation_distance']:
            if get_float(value):
                setattr(self, attr, float(value))
            else:
                raise Exception('type match error: attribute {} and value {} does not match'.format(attr, value))
        elif attr in ['home_dir']:
            if value == 'true':
                setattr(self, attr, True)
            elif value == 'false':
                setattr(self, attr, False)
            else:
                raise Exception('type match error: attribute {} and value {} does not match'.format(attr, value))
    def __str__(self):
        pass

class FirmwareRetractionConfig():
    def __init__(self):
        self.attr_list = ['retract_length', 'retract_speed']
        self.retract_length = 0.0
        self.retract_speed = 10
    def check_type(self, attr, value):
        if attr in ['retract_length', 'retract_speed']:
            if get_int(value) or get_float(value):
                setattr(self, attr, value)
            else:
                raise Exception('type match error: attribute {} and value {} does not match'.format(attr, value))
    def __str__(self):
        pass

class GcodeMacroConfig():
    def __init__(self):
        self.attr_list = ['gcode']
        self.gcode_macros = {}
    def update_macro(self, name, gcode):
        self.gcode_macros[name] = gcode
    def check_type(self, attr, value):
        pass
    def __str__(self):
        pass

class GcodeMacro:
    def __init__(self, name):
        self.name = name
        self.gcode = []
    def __str__(self):
        str = ''
        str += self.name + '\n'
        for g in self.gcode:
            str += g
            str += '\n'
        return str

class ConfigLoader():
    def __init__(self, printer):
        self.printer = printer
        self.necessary_section_list = ['printer', 'extruder', 'heater_bed', 'mcu', 'firmware_retraction'] ##configs that must be provided
        self.section_list = ['printer', 'extruder', 'heater_bed', 'mcu', 'stepper_x', 'stepper_y', 'stepper_z', 'safe_z_home', 'firmware_retraction', 'gcode_macro'] ##all possible configs
        self.registered_configs = {} ##dict to store all the registered configs(mapping: name -> obj)
        self.path = 'configs/config.cfg'
        self.read_config_file()
    def read_config_file(self):
        import re
        re_parse_comment = re.compile(r'^[#;].*$')
        re_parse_section = re.compile(r'\[([^]]+)\]')
        re_parse_attr = re.compile(r'(?P<attr>.+):')
        re_parse_value = re.compile(r':[\s]*(?P<value>.+)[\s]*')
        gcode_parser = GcodeParser(self.printer)
        with open(self.path, 'r') as f:
            file = f.read()
            lines = file.split('\n')
            curr_section = None
            curr_macro = None
            macro_has_attr = False
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                if re.findall(re_parse_comment, line):
                    continue
                pos = line.find('#')
                if pos > 0:
                    line = line[:pos]
                section = re.findall(re_parse_section, line)
                if section:
                    section = section[0]
                    if re.match(r'gcode_macro', section):
                        tmp = section.split(" ")
                        section = tmp[0]
                        macro = tmp[1]
                        if section not in self.section_list:
                            raise Exception('{} is not a valid section >>>>>>'.format(section))
                        curr_section = section
                        curr_macro = GcodeMacro(macro)
                        macro_has_attr = False
                        if 'gcode_macro' not in self.registered_configs:
                            self.register_config('gcode_macro')
                        continue
                    else:
                        if section not in self.section_list:
                            raise Exception('{} is not a valid section >>>>>>'.format(section))
                        curr_section = section
                        self.register_config(section)
                        continue
                if curr_section == 'gcode_macro':
                    attr = re.findall(re_parse_attr, line)
                    if attr:
                        if attr[0] not in self.registered_configs['gcode_macro'].attr_list:
                            raise Exception('{} section does not have attribute {} >>>>>>'.format(curr_section, attr[0]))
                        macro_has_attr = True
                    else:
                        if macro_has_attr == False:
                            raise Exception('gcode attribute is not specified in [{} {}]'.format(curr_section, curr_macro))
                        if gcode_parser.parse_line(line, -1):
                            curr_macro.gcode.append(line)
                            self.registered_configs['gcode_macro'].update_macro(curr_macro.name, curr_macro.gcode)
                else:
                    attr = re.findall(re_parse_attr, line)
                    value = re.findall(re_parse_value, line)
                    if attr and value:
                        if curr_section is None:
                            raise Exception('{} is not defined inside any section >>>>>>'.format(attr[0]))
                        if attr[0] not in self.registered_configs[curr_section].attr_list:
                            raise Exception('{} section does not have attribute {} >>>>>>'.format(curr_section, attr[0]))
                        self.registered_configs[curr_section].check_type(attr[0], value[0])
                        continue
                    raise Exception('error occurred when parsing line {}: {} >>>>>>'.format(i + 1, line))

                # if section:
                #     if section[0] not in self.section_list:
                #         raise Exception('{} is not a valid section >>>>>>'.format(section[0]))
                #     curr_section = section[0]
                #     self.register_config(section[0])
                #     continue
                # attr = re.findall(re_parse_attr, line)
                # value = re.findall(re_parse_value, line)
                # if attr and value:
                #     if curr_section is None:
                #         raise Exception('{} is not defined inside any section >>>>>>'.format(attr[0]))
                #     if attr[0] not in self.registered_configs[curr_section].attr_list:
                #         raise Exception('{} section does not have attribute {} >>>>>>'.format(curr_section, attr[0]))
                #     self.registered_configs[curr_section].check_type(attr[0], value[0])
                #     continue
                # raise Exception('error occurred when parsing line {}: {} >>>>>>'.format(i + 1, line))
            # for s in self.necessary_section_list:
            #     if s not in self.registered_configs:
            #         raise Exception('section {} must be specified but missing >>>>>>'.format(s))
        # print(self.registered_configs['gcode_macro'].macros)
        # print("successfully load config file")
        del gcode_parser
        f.close()
    def get_config(self, name):
        if name in self.registered_configs:
            return self.registered_configs[name]
        raise Exception('config {} is not registered >>>>>>'.format(name))
    def register_config(self, name):
        if name == 'printer':
            self.registered_configs[name] = PrinterConfig()
        elif name == 'extruder':
            self.registered_configs[name] = ExtruderConfig()
        elif name == 'heater_bed':
            self.registered_configs[name] = HeaterBedConfig()
        elif name == 'mcu':
            self.registered_configs[name] = MCUConfig()
        elif name == 'stepper_x' or name == 'stepper_y' or name == 'stepper_z':
            self.registered_configs[name] = StepperConfig()
        elif name == 'firmware_retraction':
            self.registered_configs[name] = FirmwareRetractionConfig()
        elif name == 'gcode_macro':
            self.registered_configs[name] = GcodeMacroConfig()
    def show_all_configs(self):
        for key, value in self.registered_configs.items():
            print("[{}]".format(key))
            print(value.__dict__)
