import re

class GcodeParser():
    def __init__(self, printer):
        self.printer = printer
        self.command_list = []
    def parse_macro(self, macro_content):
        macro_command_list = []
        for line in macro_content:
            line = line.strip()
            macro_command_list.append(self.parse_line(line, -1))
        return macro_command_list
    def parse_line(self, line, idx):
        re_parse_coord = r'(?P<coords>[XYZE])([-]?[0-9]+(?:\.[0-9]+)?)'
        re_parse_params = r'(?P<params>[FSTWXYZ])([0-9]*)'
        re_parse_command = r'[GM][0-9]+'
        re_parse_comment = r'^[#*;].*'
        gcode_command = GCodeCommand(line)
        gcode_command.cmd = "comment"
        res_get_comment = re.findall(re_parse_comment, line)
        if not res_get_comment:
            res_get_command = re.findall(re_parse_command, line)
            res_get_coordinates = re.findall(re_parse_coord, line)
            res_get_parameters = re.findall(re_parse_params, line)
            if line in self.printer.request_macros:
                gcode_command.cmd = line
            else:
                if res_get_command:
                    gcode_command.cmd = res_get_command[0]
                    if gcode_command.cmd in ['G0', 'G1'] and res_get_coordinates:
                        for r in res_get_coordinates:
                            gcode_command.params[r[0]] = float(r[1])
                    elif res_get_parameters:
                        for r in res_get_parameters:
                            try:
                                gcode_command.params[r[0]] = float(r[1])
                            except:
                                gcode_command.params[r[0]] = -1
                else:
                    self.printer.add_to_message_queue("Error occurred when parsing line {}: {} >>>>>>".format(idx + 1, line))
                    raise Exception("Error occurred when parsing line {}: {} >>>>>>".format(idx + 1, line))
        else:
            re_parse_description = r'(MINX|MINY|MINZ|MAXX|MAXY|MAXZ|LAYER|LAYER_COUNT|TIME):([-]?[0-9]+(?:\.[0-9]+)?)'
            res_get_description = re.findall(re_parse_description, res_get_comment[0])
        return gcode_command
    def parse_file(self, filename):
        print("----------------------------------------------------")
        print("-----------------start parsing file-----------------")
        print("----------------------------------------------------")
        self.command_list = command_list = []
        with open(filename, 'r') as f:
            file = f.readlines()
            for i, line in enumerate(file):
                line = line.strip()
                if line in self.printer.gcode_macros:
                    try:
                        macro_command_list = self.parse_macro(self.printer.gcode_macros[line])
                        for c in macro_command_list:
                            command_list.append(c)
                    except:
                        self.printer.add_to_message_queue("Error occurred when parsing macro {}".format(line))
                        raise Exception("Error occurred when parsing macro {}".format(line))
                else:
                    command_list.append(self.parse_line(line, i))
        self.command_list = command_list
        del command_list
        return self.command_list

class GCodeCommand:
    def __init__(self, gcode):
        self.cmd = ''
        self.params = {}
        self.gcode = gcode
    def get_command(self):
        return self.cmd
    def get_command_params(self):
        return self.params
    def get_command_line(self):
        return self.gcode
    def __str__(self):
        return self.gcode
        # res = self.cmd
        # for k in self.params:
        #     res += ' '
        #     res += k
        #     res += str(self.params[k])
        # return res

if __name__ == "__main__":
    pass
