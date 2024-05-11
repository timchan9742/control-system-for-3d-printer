import logging
import time, os

class FileLogger():
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        data_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
        self.log_dir = os.getcwd() + '/logs/'
        self.log_file_path = os.getcwd() + '/logs/' + data_time + '.log'
        self.create_log_directory()
        self.remove_logs()
        fh = logging.FileHandler(self.log_file_path, mode='w')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
    def remove_logs(self):
        try:
            for f in os.listdir(self.log_dir):
                os.remove(self.log_dir + f)
        except:
            print("log directory doesn't exist")
    def create_log_directory(self):
        if os.path.exists(self.log_dir):
            pass
        else:
            os.mkdir(self.log_dir)
    def debug(self, msg):
        self.logger.debug(msg)
    def info(self, msg):
        self.logger.info(msg)
    def warning(self, msg):
        self.logger.warning(msg)
    def error(self, msg):
        self.logger.error(msg)
    def critical(self, msg):
        self.logger.critical(msg)
