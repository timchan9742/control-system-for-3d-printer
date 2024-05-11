import math

FACTOR = 1
SPEED_FACTOR = 1

class RelativeMove():
    def __init__(self, toolhead, displacement):
        self.displacement = displacement
        self.speed = toolhead.speed / 60.0
        self.time = [abs(d) / self.speed for d in self.displacement]
        print(displacement)

class AbsoluteMove():
    def __init__(self, toolhead, destination):
        self.displacement = [destination[i] - toolhead.toolhead_pos[i] for i in len(destination)]
        self.speed = toolhead.speed / 60.0
        self.time = [abs(d) / self.speed for d in self.displacement]

class HomingMove():
    def __init__(self, toolhead, max_homing_distance=0):
        self.max_homing_distance = max_homing_distance
        self.time = 31250 * 60

class MoveQueue:
    def __init__(self, toolhead):
        self.queue = []
        self.toolhead = toolhead
        self.flush_count = 0
        self.LOOKAHEAD_TIME = 0.250
        self.time_left_to_flush = self.LOOKAHEAD_TIME
    def reset(self):
        del self.queue[:]
        self.time_left_to_flush = self.LOOKAHEAD_TIME
        self.flush_count = 0
    def set_flush_time(self, flush_time):
        self.time_left_to_flush = flush_time
    def flush(self):
        for m in self.queue:
            if True:
                start_v = m.start_v
                cruise_v = m.cruise_v
                end_v = m.end_v
                # print("start_v2: {} cruise_v2: {} end_v2: {}".format(start_v, cruise_v, end_v))
                m.set_junction(start_v, cruise_v, end_v)
        self.toolhead.process_moves_all(self.queue)
    def add_move(self, move):
        self.queue.append(move)
        self.flush_count += 1
        if len(self.queue) <= 1:
            return
        # move.cal_junction(self.queue[-2])
        self.time_left_to_flush -= move.min_move_t
        if self.time_left_to_flush <= 0:
            self.flush()
            self.reset()


class Move:
    def __init__(self, toolhead, start_pos, end_pos, speed):
        self.toolhead = toolhead
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.max_accel = toolhead.max_accel
        self.max_decel = toolhead.max_decel
        self.max_velocity = toolhead.max_velocity
        self.max_z_velocity = toolhead.max_z_velocity
        self.max_e_velocity = 100
        self.speed = min(speed / 60.0, self.max_velocity) * SPEED_FACTOR
        self.is_extruder_only_move = False
        self.axis_d = [end_pos[i] - start_pos[i] for i in range(len(end_pos))]
        self.move_d = math.sqrt(sum([d * d for d in self.axis_d][:3]))
        if self.move_d <= 0.000000001:
            self.is_extruder_only_move = True
            self.move_d = self.axis_d = abs(self.axis_d[3])
            self.axis_accel = [0, 0, 0, self.max_accel]
            self.axis_decel = [0, 0, 0, self.axis_accel * (-1)]
            self.min_move_t = self.move_d / self.max_e_velocity
            self.start_v = 0
            self.cruise_v = min(self.max_e_velocity, math.sqrt(self.move_d * self.max_accel))
            self.end_v = 0
        else:
            self.inv_move_d = 1. / self.move_d
            self.normalized_axis_d = [d * self.inv_move_d for d in self.axis_d]
            self.axis_accel = [d * self.inv_move_d * self.max_accel for d in self.axis_d]
            self.axis_decel = [-d for d in self.axis_accel]
            self.min_move_t = self.move_d / self.speed
            self.start_v = 0
            self.cruise_v = min(self.speed, math.sqrt(self.move_d * self.max_accel))
            self.end_v = 0
    def cal_junction(self, prev_move):
        if self.is_extruder_only_move or prev_move.is_extruder_only_move:
            return
        curr_move_vector = self.normalized_axis_d
        prev_move_vector = prev_move.normalized_axis_d
        cos_theta = -(curr_move_vector[0] * prev_move_vector[0]
                    + curr_move_vector[1] * prev_move_vector[1]
                    + curr_move_vector[2] * prev_move_vector[2])
        if cos_theta > 0.999999:
            # prev_move.end_v = prev_move.cruise_v
            # prev_move.end_v = min(prev_move.cruise_v, self.cruise_v)
            # self.start_v = prev_move.end_v
            prev_move.end_v = self.start_v = 0
            return
        else:
            cos_theta = max(cos_theta, -0.999999)
            sin_half_theta = math.sqrt((1.0 - cos_theta) * 0.5)
            tan_half_theta = math.sqrt((1.0 - cos_theta) / (1.0 + cos_theta))
            radius = self.toolhead.junction_deviation * sin_half_theta / (1.0 - sin_half_theta)
            max_junction_v = math.sqrt(self.max_accel * radius)
            prev_centripetal_v = math.sqrt(0.5 * prev_move.move_d * tan_half_theta * prev_move.max_accel)
            curr_centripetal_v = math.sqrt(0.5 * self.move_d * tan_half_theta * self.max_accel)
            junction_v = min(max_junction_v, prev_move.cruise_v, self.cruise_v, prev_centripetal_v, curr_centripetal_v)
            prev_move.end_v = junction_v
            self.start_v = prev_move.end_v
            return

    def set_junction(self, start_v, cruise_v, end_v):
        if not self.is_extruder_only_move:
            self.axis_start_v = [start_v * ratio for ratio in self.normalized_axis_d]
            self.axis_cruise_v = [cruise_v * ratio for ratio in self.normalized_axis_d]
            self.axis_end_v = [end_v * ratio for ratio in self.normalized_axis_d]
        else:
            self.axis_start_v = [0.0, 0.0, 0.0, start_v]
            self.axis_cruise_v = [0.0, 0.0, 0.0, cruise_v]
            self.axis_end_v = [0.0, 0.0, 0.0, end_v]
        self.accel_d = (cruise_v * cruise_v - start_v * start_v) / (2 * self.max_accel)
        self.decel_d = (cruise_v * cruise_v - end_v * end_v) / (2 * self.max_decel)
        self.cruise_d = self.move_d - self.accel_d - self.decel_d
        self.accel_t = self.accel_d / ((start_v + cruise_v) * 0.5)
        self.decel_t = self.decel_d / ((end_v + cruise_v) * 0.5)
        self.cruise_t = self.cruise_d / cruise_v
        self.real_move_t = self.accel_t + self.cruise_t + self.decel_t
        # print('accel_d: {} accel_t: {} cruise_d: {} cruise_t: {} decel_d: {} decel_t: {}'.format(self.accel_d, self.accel_t, self.cruise_d, self.cruise_t, self.decel_d, self.decel_t))

    def __str__(self):
        return 'start_pos: {} end_pos: {} \n'.format(self.start_pos, self.end_pos) + 'start_v: {} cruise_v: {} end_v: {} accel_t: {} cruise_t: {} decel_t: {} min_move_t: {} real_move_t: {}'.format(self.start_v, self.cruise_v, self.end_v, self.accel_t, self.cruise_t, self.decel_t, self.min_move_t, self.real_move_t)

class NewMoveQueue:
    def __init__(self, toolhead):
        self.test_queue = []
        self.queue = []
        self.toolhead = toolhead
        self.flush_count = 0
        self.LOOKAHEAD_TIME = 0.250
        self.time_left_to_flush = self.LOOKAHEAD_TIME
    def reset(self):
        del self.queue[:]
        self.time_left_to_flush = self.LOOKAHEAD_TIME
        self.flush_count = 0
    def set_flush_time(self, flush_time):
        self.time_left_to_flush = flush_time
    def flush(self, move):
        start_v = math.sqrt(move.max_start_v2)
        cruise_v = math.sqrt(move.max_cruise_v2)
        end_v = math.sqrt(move.max_end_v2)
        move.set_junction(start_v, cruise_v, end_v)
        self.toolhead.process_move(move)
    def flush_all(self):
        end_v2 = 0
        for i in range(self.flush_count - 1, -1, -1):
            # ----------------------------------------------
            # suppose x = accel_delta_v2, y = decel_delta_v2 then we have
            # 1. start_v2 + x - y = end_v2
            # 2. x + y = delta_v2 if we suppose that this move only has acceleration stage and deceleration stage
            # => start_v2 + 2x = end_v2 + delta_v2
            # => x = (end_v2 + delta_v2 - start_v2 ) / 2
            # ----------------------------------------------
            m = self.queue[i]
            if m.is_extruder_only_move == False:
                accel_delta_v2 = (m.delta_v2 + end_v2 - m.max_start_v2) * 0.5
                if accel_delta_v2 < 0: ##only deceleration in this move
                    m.max_start_v2 = end_v2 + m.delta_v2
                    m.max_cruise_v2 = m.max_start_v2
                    m.max_end_v2 = end_v2
                    end_v2 = m.max_start_v2
                else:
                    if m.max_start_v2 + accel_delta_v2 <= m.max_cruise_v2:
                        m.max_cruise_v2 = m.max_start_v2 + accel_delta_v2
                        m.max_end_v2 = end_v2
                        end_v2 = m.max_start_v2
                    else:
                        m.max_cruise_v2 = m.max_cruise_v2
                        m.max_end_v2 = end_v2
                        end_v2 = m.max_start_v2
            else:
                accel_delta_v2 = (m.delta_v2 + 0 - m.max_start_v2) * 0.5
                m.max_cruise_v2 = m.max_start_v2 + accel_delta_v2
                m.max_end_v2 = 0
        for m in self.queue:
            m.set_junction_v2(m.max_start_v2, m.max_cruise_v2, m.max_end_v2)
            # start_v = math.sqrt(m.max_start_v2)
            # cruise_v = math.sqrt(m.max_cruise_v2)
            # end_v = math.sqrt(m.max_end_v2)
            # print("move_d: {}".format(m.move_d))
            # print("start_v: {:.1f} cruise_v: {:.1f} end_v: {:.1f}".format(start_v, cruise_v, end_v))
            # m.set_junction(start_v, cruise_v, end_v)
            # print("accel_t: {:.4f} cruise_t: {:.4f} decel_t: {:.4f}".format(m.accel_t, m.cruise_t, m.decel_t))
        self.toolhead.process_moves_all(self.queue)
    def add_move(self, move):
        if move.move_d > 0:
            self.queue.append(move)
            self.flush_count += 1
            if len(self.queue) <= 1:
                return
            move.cal_junction(self.queue[-2])
            self.time_left_to_flush -= move.min_move_t
            if self.time_left_to_flush <= 0:
                self.flush_all()
                self.reset()

class NewMove:
    def __init__(self, toolhead, start_pos, end_pos, speed):
        self.toolhead = toolhead
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.max_accel = toolhead.max_accel
        self.max_decel = toolhead.max_decel
        self.max_velocity = toolhead.max_velocity
        self.max_z_velocity = toolhead.max_z_velocity
        self.max_e_velocity = 100
        self.speed = min(speed / 60.0, self.max_velocity) * SPEED_FACTOR
        # self.speed = 200
        self.smooth_factor = 0.80 #if this factor is set to 1 then there will be no cruise stage in the move
        self.is_extruder_only_move = False
        self.axis_d = [end_pos[i] - start_pos[i] for i in range(len(end_pos))]
        self.move_d = math.sqrt(sum([d * d for d in self.axis_d][:3]))
        if self.move_d <= 0.000000001:
            self.is_extruder_only_move = True
            # self.move_d = self.axis_d = self.axis_d[3]
            self.normalized_axis_d = [0, 0, 0, 1]
            self.axis_accel = [0, 0, 0, self.max_accel]
            self.axis_decel = [0, 0, 0, self.axis_accel * (-1)]
            self.min_move_t = self.move_d / self.max_e_velocity
            self.max_start_v2 = 0
            self.max_cruise_v2 = self.max_e_velocity **2
            self.delta_v2 = 2 * self.max_accel * self.move_d * self.smooth_factor
            self.max_end_v2 = 0
        else:
            self.inv_move_d = 1. / self.move_d
            self.normalized_axis_d = [d * self.inv_move_d for d in self.axis_d]
            self.axis_accel = [d * self.inv_move_d * self.max_accel for d in self.axis_d]
            self.axis_decel = [-d for d in self.axis_accel]
            self.min_move_t = self.move_d / self.speed
            self.max_start_v2 = 0
            self.max_cruise_v2 = self.speed **2
            self.delta_v2 = 2 * self.max_accel * self.move_d * self.smooth_factor
            self.max_end_v2 = 0
    def cal_junction(self, prev_move):
        if self.is_extruder_only_move or prev_move.is_extruder_only_move:
            return
        curr_move_vector = self.normalized_axis_d
        prev_move_vector = prev_move.normalized_axis_d
        cos_theta = -(curr_move_vector[0] * prev_move_vector[0]
                    + curr_move_vector[1] * prev_move_vector[1]
                    + curr_move_vector[2] * prev_move_vector[2])
        if cos_theta > 0.999999:
            # prev_move.end_v = self.start_v = 0
            return
        else:
            cos_theta = max(cos_theta, -0.999999)
            sin_half_theta = math.sqrt((1.0 - cos_theta) * 0.5)
            tan_half_theta = math.sqrt((1.0 - cos_theta) / (1.0 + cos_theta))
            radius = self.toolhead.junction_deviation * sin_half_theta / (1.0 - sin_half_theta)
            prev_centripetal_v2 = 0.5 * prev_move.move_d * tan_half_theta * prev_move.max_accel
            curr_centripetal_v2 = 0.5 * self.move_d * tan_half_theta * self.max_accel
            self.max_start_v2 = min(self.max_accel * radius, prev_move.max_accel * radius, prev_move.max_cruise_v2, self.max_cruise_v2,
            prev_centripetal_v2, curr_centripetal_v2, prev_move.max_start_v2 + prev_move.delta_v2)
            return
    def set_junction(self, start_v, cruise_v, end_v):
        self.start_v = start_v
        self.cruise_v = cruise_v
        self.end_v = end_v
        if not self.is_extruder_only_move:
            self.axis_start_v = [start_v * ratio for ratio in self.normalized_axis_d]
            self.axis_cruise_v = [cruise_v * ratio for ratio in self.normalized_axis_d]
            self.axis_end_v = [end_v * ratio for ratio in self.normalized_axis_d]
            self.toolhead.toolhead_curr_move_speed = self.cruise_v
        else:
            self.axis_start_v = [0.0, 0.0, 0.0, start_v]
            self.axis_cruise_v = [0.0, 0.0, 0.0, cruise_v]
            self.axis_end_v = [0.0, 0.0, 0.0, end_v]
            self.toolhead.toolhead_curr_move_speed = 0
        self.accel_d = (cruise_v * cruise_v - start_v * start_v) / (2 * self.max_accel)
        self.decel_d = (cruise_v * cruise_v - end_v * end_v) / (2 * self.max_decel)
        self.cruise_d = self.move_d - self.accel_d - self.decel_d
        self.accel_t = self.accel_d / ((start_v + cruise_v) * 0.5)
        self.decel_t = self.decel_d / ((end_v + cruise_v) * 0.5)
        self.cruise_t = self.cruise_d / cruise_v
        self.real_move_t = self.accel_t + self.cruise_t + self.decel_t
        # print('accel_d: {} accel_t: {} cruise_d: {} cruise_t: {} decel_d: {} decel_t: {}'.format(self.accel_d, self.accel_t, self.cruise_d, self.cruise_t, self.decel_d, self.decel_t))

    def set_junction_v2(self, start_v2, cruise_v2, end_v2):
        self.start_v = start_v = math.sqrt(start_v2)
        self.cruise_v = cruise_v = math.sqrt(cruise_v2)
        self.end_v = end_v = math.sqrt(end_v2)
        if not self.is_extruder_only_move:
            self.axis_start_v = [start_v * ratio for ratio in self.normalized_axis_d]
            self.axis_cruise_v = [cruise_v * ratio for ratio in self.normalized_axis_d]
            self.axis_end_v = [end_v * ratio for ratio in self.normalized_axis_d]
            self.toolhead.toolhead_curr_move_speed = self.cruise_v
        else:
            self.axis_start_v = [0.0, 0.0, 0.0, start_v]
            self.axis_cruise_v = [0.0, 0.0, 0.0, cruise_v]
            self.axis_end_v = [0.0, 0.0, 0.0, end_v]
            self.toolhead.toolhead_curr_move_speed = 0
        self.accel_d = (cruise_v2 - start_v2) / (2 * self.max_accel)
        self.decel_d = (cruise_v2 - end_v2) / (2 * self.max_decel)
        self.cruise_d = self.move_d - self.accel_d - self.decel_d
        self.accel_t = self.accel_d / ((start_v + cruise_v) * 0.5)
        self.decel_t = self.decel_d / ((end_v + cruise_v) * 0.5)
        self.cruise_t = self.cruise_d / cruise_v
        self.real_move_t = self.accel_t + self.cruise_t + self.decel_t

    def __str__(self):
        return 'start_pos: {} end_pos: {} \n'.format(self.start_pos, self.end_pos) + 'start_v: {} cruise_v: {} end_v: {} accel_t: {} cruise_t: {} decel_t: {} min_move_t: {} real_move_t: {}'.format(self.start_v, self.cruise_v, self.end_v, self.accel_t, self.cruise_t, self.decel_t, self.min_move_t, self.real_move_t)
