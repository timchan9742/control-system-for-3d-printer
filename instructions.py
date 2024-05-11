##instructions for the 3d printer
DISABLE_MOSFETS = 0
ENABLE_MOSFETS = 1
TRAPEZOID_MOVE = 2
SET_MAX_VELOCITY = 3
MOVE_WITH_FINISH_TIME = 4
SET_MAX_ACCELERATION = 5
START_CALIBRATION = 6
CAPTURE_HALL_SENSOR_DATA = 7
RESET_TIME = 8
GET_MOTOR_TIME = 9
TIME_SYNC = 10
GET_NUM_OF_ITEMS_IN_QUEUE = 11
EMERGENCY_STOP = 12
SET_ORIGIN = 13
HOMMING = 14
GET_MOTOR_POSITION = 15
GET_MOTOR_STATUS = 16
GO_TO_CLOSE_LOOP = 17
GET_UPDATE_FREQUENCY = 18
MOVE_WITH_ACCELERATION = 19
DETECT_DEVICES = 20
SET_DEVICE_ALIAS = 21
GET_PRODUCT_VERSION_AND_DETAILS = 22
MOVE_WITH_VELOCITY = 26
SYSTEM_RESET = 27
SET_MAX_CURRENT = 28
MULTI_MOVE = 29
SET_SAFETY_LIMITS = 30
PING_COMMAND = 31

SET_EXTRUDER_TEMPERATURE = 101
GET_EXTRUDER_TEMPERATURE = 102
SET_BED_TEMPERATURE = 103
GET_BED_TEMPERATURE = 104
SET_FAN_POWER = 105
GET_FAN_POWER = 106

SET_MOTOR_INDEX_COMMAND = 200
SET_PID_P_VALUE = 201
SET_PID_I_VALUE = 202
SET_PID_D_VALUE = 203
GET_PID_VALUE = 204

##command 0 - disable MOSFETS
def inst_disable_MOSFETS(flag, order='little'):
    command = bytearray([ord(flag), DISABLE_MOSFETS, 0])
    return command

##command 1 - enable MOSFETS
def inst_enable_MOSFETS(flag, order='little'):
    command = bytearray([ord(flag), ENABLE_MOSFETS, 0])
    return command

##command 2 - set position and move
def inst_set_position_and_move(flag, position, order='little'):
    command = bytearray([ord(flag), SET_POSITION_AND_MOVE, 4])
    command += position.to_bytes(4, byteorder=order, signed=True)
    return command

def inst_trapezoid_move(flag, displacement, time_steps, order='little'):
    command = bytearray([ord(flag), TRAPEZOID_MOVE, 8])
    command += displacement.to_bytes(4, byteorder=order, signed=True)
    command += time_steps.to_bytes(4, byteorder=order, signed=False)
    return command

##command 3 - set velocity
def inst_set_max_velocity(flag, max_vel, order='little'):
    command = bytearray([ord(flag), SET_MAX_VELOCITY, 4])
    command += int(max_vel).to_bytes(4, byteorder=order)
    return command

##command 4 - set position and finish time
def inst_move_with_finish_time(flag, position, time, order='little'):
    command = bytearray([ord(flag), MOVE_WITH_FINISH_TIME, 8])
    command += int(position).to_bytes(4, byteorder=order, signed=True)
    command += int(time).to_bytes(4, byteorder=order)
    return command

##command 5 - set acceleration
def inst_set_max_accleration(flag, max_accel, order='little'):
    command = bytearray([ord(flag), SET_MAX_ACCELERATION, 4])
    command += int(max_accel).to_bytes(4, byteorder=order)
    return command

##command 6 - start calibration
def inst_start_calibration(flag, order='little'):
    command = bytearray([ord(flag), START_CALIBRATION, 0])
    return command

##command 7 - capture hall sensor data
def capture_hall_sensor_data(order='little'):
    pass

##command 8 - reset all time
def inst_reset_time(flag, order='little'):
    command = bytearray([ord(flag), RESET_TIME, 0])
    return command

##command 9 - get current time
def inst_get_motor_time(flag, order='little'):
    command = bytearray([ord(flag), GET_MOTOR_TIME, 0])
    return command

##command 10 - time syncronization
def inst_time_sync(flag, master_time, order='little'):
    if flag != 255:
        command = bytearray([ord(flag), TIME_SYNC, 6])
        command += int(master_time).to_bytes(6, byteorder=order)
        return command
    else:
        command = bytearray([255, TIME_SYNC, 6])
        command += int(master_time).to_bytes(6, byteorder=order)
        return command

##command 11 - get number of items in queue
def inst_get_num_of_items_in_queue(flag, order='little'):
    command = bytearray([ord(flag), GET_NUM_OF_ITEMS_IN_QUEUE, 0])
    return command

##command 12 - send an emergency stop
def inst_emergency_stop(flag, order='little'):
    command = bytearray([ord(flag), EMERGENCY_STOP, 0])
    return command

##command 13 - set the current position as the origin 0
def inst_set_current_position_as_origin(flag, order='little'):
    command = bytearray([ord(flag), SET_ORIGIN, 0])
    return command

##command 14 - reset home position
def inst_do_homing(flag, max_homing_displacement, time_steps, order='little'):
    # DEFAULT_LENGTH = 8
    # flag_byte = bytes(flag, encoding='UTF-8')
    # command_byte = HOMMING.to_bytes(1, byteorder=order)
    # length_byte = DEFAULT_LENGTH.to_bytes(1, byteorder=order)
    # value_byte = max_homing_displacement.to_bytes(4, byteorder=order, signed=True)
    # time_byte = time_steps.to_bytes(4, byteorder=order)
    # return flag_byte + command_byte + length_byte + value_byte + time_byte
    command = bytearray([ord(flag), HOMMING, 8])
    command += max_homing_displacement.to_bytes(4, byteorder=order, signed=True)
    command += time_steps.to_bytes(4, byteorder=order)
    return command

##command 15 - get the current position
def inst_get_motor_position(flag, order='little'):
    command = bytearray([ord(flag), GET_MOTOR_POSITION, 0])
    return command

##command 16 - get the currect status
def inst_get_motor_status(flag, order='little'):
    command = bytearray([ord(flag), GET_MOTOR_STATUS, 0])
    return command

##command 17 - go to close loop mode
def inst_go_to_closed_loop(flag, order='little'):
    command = bytearray([ord(flag), GO_TO_CLOSE_LOOP, 0])
    return command

##command 18 - get the update frequency (reciprocal of the time step)
def inst_get_update_frequency(flag, order='little'):
    command = bytearray([ord(flag), GET_UPDATE_FREQUENCY, 0])
    return command

##command 19 - move with acceleration
def inst_move_with_acceleration(flag, accel, time_steps, order='little'):
    command = bytearray([ord(flag), MOVE_WITH_ACCELERATION, 8])
    command += accel.to_bytes(4, byteorder=order, signed=True)
    command += time_steps.to_bytes(4, byteorder=order)
    return command

##command 20 - detect devices
def inst_detect_devices(flag, order='little'):
    command = bytearray([ord(flag), DETECT_DEVICES, 0])
    return command

##command 21 - set device alias
def inst_set_device_alias(flag, unique_id, alias, order='little'):
    command = bytearray([255, SET_DEVICE_ALIAS, 9])
    command += unique_id.to_bytes(8, "little")
    command += alias.to_bytes(1, "little")
    return command

##command 22 - get product version and details
def inst_get_product_version_and_details(flag, order='little'):
    command = bytearray([ord(flag), GET_PRODUCT_VERSION_AND_DETAILS, 0])
    return command

def inst_move_with_velocity(flag, vel, time_steps, order='little'):
    command = bytearray([ord(flag), MOVE_WITH_VELOCITY, 8])
    command += vel.to_bytes(4, byteorder=order, signed=True)
    command += time_steps.to_bytes(4, byteorder=order)
    return command

def inst_system_reset():
    command = bytearray([255, SYSTEM_RESET, 0])
    return command

def inst_set_max_current(flag, max_current, max_regeneration_current, order='little'):
    command = bytearray([ord(flag), SET_MAX_CURRENT, 4])
    command += max_current.to_bytes(2, byteorder=order)
    command += max_regeneration_current.to_bytes(2, byteorder=order)
    return command

def inst_multi_move(flag, num_of_moves, move_type, value_list, time_list, order='little'):
    command = bytearray([ord(flag), MULTI_MOVE, 1 + 4 + num_of_moves * 8, num_of_moves])
    command += move_type.to_bytes(4, byteorder=order)
    for i in range(len(value_list)):
        command += value_list[i].to_bytes(4, byteorder=order, signed=True)
        command += time_list[i].to_bytes(4, byteorder=order)
    return command

def inst_set_safety_limits(flag, lower_limit, higher_limit):
    command = bytearray([ord(flag), SET_SAFETY_LIMITS, 8])
    command += lower_limit.to_bytes(4, byteorder=order, signed=True)
    command += higher_limit.to_bytes(4, byteorder=order, signed=True)
    return command

def inst_pin_pcb(flag, payload, order='little'):
    command = bytearray([ord(flag), PING_COMMAND, 10])
    command += payload
    return command

def inst_set_extruder_temperature(flag, temp, order='little'):
    command = bytearray([ord(flag), SET_EXTRUDER_TEMPERATURE, 2])
    command += temp.to_bytes(2, byteorder=order)
    return command

def inst_get_extruder_temperature(flag, order='little'):
    command = bytearray([ord(flag), GET_EXTRUDER_TEMPERATURE, 0])
    return command

def inst_set_bed_temperature(flag, temp, order='little'):
    command = bytearray([ord(flag), SET_BED_TEMPERATURE, 2])
    command += temp.to_bytes(2, byteorder=order)
    return command

def inst_get_bed_temperature(flag, order='little'):
    command = bytearray([ord(flag), GET_BED_TEMPERATURE, 0])
    return command

def inst_set_fan_power(flag, fan_power, order='little'):
    command = bytearray([ord(flag), SET_FAN_POWER, 1])
    command += fan_power.to_bytes(1, byteorder=order)
    return command

def inst_get_fan_power(flag):
    command = bytearray([ord(flag), GET_FAN_POWER, 0])
    return command

def inst_set_pid_p_value(flag, p_value, order='little'):
    command = bytearray([ord(flag), SET_PID_P_VALUE, 4])
    command += p_value.to_bytes(4, byteorder=order)
    return command

def inst_set_pid_i_value(flag, i_value, order='little'):
    command = bytearray([ord(flag), SET_PID_I_VALUE, 4])
    command += i_value.to_bytes(4, byteorder=order)
    return command

def inst_set_pid_d_value(flag, d_value, order='little'):
    command = bytearray([ord(flag), SET_PID_D_VALUE, 4])
    command += d_value.to_bytes(4, byteorder=order)
    return command

def inst_get_pid_value(flag):
    command = bytearray([ord(flag), GET_PID_VALUE, 0])
    return command
