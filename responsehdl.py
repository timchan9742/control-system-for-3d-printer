from termcolor import colored

##the ResponseHandler handles responses from the 3d printer
class ResponseHandler:
    def __init__(self, printer):
        self.printer = printer
    def check_no_response(self, resp):
        return True
    def check_default_response(self, resp):
        # print("checking DEFAULT response...")
        if len(resp) != 3:
             print(colored("Did not receive the 3-byte response", "red", attrs=["bold"]))
             return None
        if resp != b'R\x00\x00':
            print(colored("Wrong response", "red", attrs=["bold"]))
            return None
        print(colored("OK", "green", attrs=["bold"]))
        return True
    def check_get_num_of_items_in_queue(self, resp, axis):
        # print("checking GET_NUM_OF_ITEMS_IN_QUEUE-{} response...".format(axis))
        if len(resp) != 4:
            print("Did not receive the 4-byte response [get_num_of_items_in_queue {}]".format(axis))
            return None
        num = int.from_bytes(resp[3:], byteorder='little')
        return num
    def check_get_update_frequency_response(self, resp):
        # print("checking GET_UPDATE_FREQUENCY response...")
        if len(resp) != 7:
            print("Did not receive the 7-byte response [get_update_frequency]")
            return None
        frequency = int.from_bytes(resp[3:], byteorder='little')
        return frequency
    def check_detect_devices_response(self, resp):
        # print("checking DETECT_DEVICES response...")
        if len(resp) != 11:
            print("Did not receive the 11-byte response [detect_devices]")
            return None
        uniqueID = int.from_bytes(resp[3:], byteorder='little', signed=True)
        return uniqueID
    def check_get_motor_position_response(self, resp):
        # print("checking GET_MOTOR_POSITION response...")
        if len(resp) != 7:
            print(colored("Did not receive the 7-byte response [get_position]", "red", attrs=["bold"]))
            return None
        position = bytes_to_int(resp[3:])
        print(colored("current position: {}", "green", attrs=["bold"]).format(position))
        return position
    def check_get_motor_time_response(self, resp):
        # print("checking GET_MOTOR_TIME response...")
        if len(resp) != 9:
            print(colored("Did not receive the 9-byte response [get_time]", "red", attrs=["bold"]))
            return None
        time = int.from_bytes(resp[3:], byteorder='little')
        print(colored("current time: {}", "green", attrs=["bold"]).format(time))
        return time
    def check_time_sync_response(self, resp):
        # print("checking TIME_SYNC response...")
        if len(resp) != 9:
            print(colored("Did not receive the 9-byte response [time_sync]", "red", attrs=["bold"]))
            return None
        time_error = int.from_bytes(resp[3:7], byteorder='little', signed=True)
        RCC_ICSCR = int.from_bytes(resp[7:], byteorder='little', signed=False)
        print(colored("time_error: {}  RCC-ICSCR: {}", "green", attrs=["bold"]).format(time_error, RCC_ICSCR))
        return time_error, RCC_ICSCR
    def check_get_extruder_temp_response(self, resp):
        if len(resp) != 5:
            print("Did not receive the 5-byte response [get_extruder_temp]")
            return None
        temp = int.from_bytes(resp[3:], byteorder='little')
        self.printer.get_object('extruder_obj').update_temperature(temp)
        return temp
    def check_get_bed_temp_response(self, resp):
        if len(resp) != 5:
            print("Did not receive the 5-byte response [get_bed_temp]")
            return None
        temp = int.from_bytes(resp[3:], byteorder='little')
        return temp
