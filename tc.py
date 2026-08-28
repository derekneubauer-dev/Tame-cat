#!/path/to/python3

import argparse
import time
from os import listdir, SEEK_END
from os.path import join, isfile, exists, splitext


LOG_FILE_PATH = ".dev.log"
PROJECT_DIR_PATH = "."


def main():

    parser = argparse.ArgumentParser(prog="Development Utilities")
    parser.add_argument("action")
    args = parser.parse_args()
    action = args.action

    if not exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "x"):
            pass
    
    if action == "start":
        print("Starting...")
        if Session.in_session():
            raise InSessionError
        else: 
            Session.clock_in()

    elif action == "stop":
        print("Stopping...")
        if not Session.in_session():
            raise OutOfSessionError
        else:
            Session.clock_out()


    elif action == "report":
        print("Reporting...")
        progress = Progress(LOG_FILE_PATH)
        progress.report()

    elif action == "status":
        Session.in_session()
        
    else:
        raise ValueError('Use argument "start", "stop", "status", or "report"')


class InSessionError(Exception):
    def __init__(self, message="Can't Start Session: Already In Progress"):
        self.message = message
        super().__init__(self.message)

class OutOfSessionError(Exception):
    def __init__(self, message="Can't End Session: No Session in Progress"):
        self.message = message
        super().__init__(self.message)


class SessionManager:

    def __init__(self, file_name):
        self.file_name = file_name
        self.list_sessions = []
        self.load_sessions()
    
    def load_sessions(self):
        lines = []
        length: int = 0
        in_progress = True
        start_timestamp = 0
        stop_timestamp = 0
        duration = 0

        with open(self.file_name, 'r') as f:
            lines = f.readlines()
            length = len(lines)
            for i in range(0, length, 2):
                start_timestamp = float(lines[i].strip())
                if length % 2 == 0:
                    in_progress = False
                    stop_timestamp = float(lines[i+1].strip())
            
                self.list_sessions.append(Session(in_progress, start_timestamp, stop_timestamp))
        
        print(self.list_sessions)
        

    
    def get_sessions(self):
        return self.list_sessions


class Session:

    def __init__(self, in_progress = False, clock_in_unix_time: float = 0, clock_out_unix_time: float =0):
        self.session_in_progress = False
        self.clock_in_timestamp = clock_in_unix_time
        self.clock_out_timestamp = clock_out_unix_time
        self.secs_duration = self.calculate_duration()
        self.str_duration = self.format_duration()


    def calculate_duration(self):
        return self.clock_out_timestamp - self.clock_in_timestamp
    
    def format_duration(self):
        return get_hours_min_sec(self.secs_duration)

    def get_clock_in_timestamp(self):
        return self.clock_in_timestamp
    
    def get_clock_out_timestamp(self):
        return self.clock_out_timestamp

    @staticmethod 
    def clock_in():
        with open(LOG_FILE_PATH, 'a') as f :
            now = time.time()
            f.write(f"{now}\n")
    

    @staticmethod
    def clock_out():
        with open(LOG_FILE_PATH, "r+") as f:
            now = time.time()
            dev_log = f.readlines()
            #print(dev_log)
            starts = dev_log[0::2]
            #stops = dev_log[1::2]
            #print(f"{starts=}\n {stops=}")
            #print(f"{starts=}")
            duration =  now - float(starts[-1].split("-")[1])
            #print(f"{duration=}")
            f.write(f"{now}\n")
            print(f"{get_hours_min_sec(duration)=}")


    @staticmethod
    def in_session():
        with(open(LOG_FILE_PATH, 'r')) as f:
            line_count = count_lines(f)
            if line_count % 2 == 0:
                print("Out of Session")
                return False 
            else:
                print("In Session") 
            return True




class Progress:
    
    def __init__(self, log_file = LOG_FILE_PATH):
        self.log_file = log_file
        self.project_file_names, self.number_of_lines, self.bytes_in_project = self.project_stats() 
        self.sessions: list[Session] = SessionManager(self.log_file).get_sessions()
        self.project_start_date = self.get_start_date()

        
    def project_stats(self):
        files = [file for file in listdir(PROJECT_DIR_PATH) if isfile(join(PROJECT_DIR_PATH, file))]
        lines_per_file = []
        bytes_per_file = []

        for file in files:
            with open(join(PROJECT_DIR_PATH, file), 'r') as file_pointer:

                lines = count_lines(file_pointer)
                bytes = count_bytes(file_pointer)              
                lines_per_file.append(lines) 
                bytes_per_file.append(bytes)


        stats = (files, lines_per_file, bytes_per_file)
        print(list(zip(stats)))
        return  stats 

    def total_bytes(self):
        total_bytes = sum(self.bytes_in_project)
        if total_bytes / 1024 > 1024:
            return f"{total_bytes/1048576}M"
        else:

            return f"{total_bytes/1024:.2f}K "

    def total_lines(self):
         return sum(self.number_of_lines)


    def total_time(self):
        durations = []
        for session in self.sessions:
            durations.append(session.calculate_duration())
        
        self.total_time = sum(durations)
        return self.total_time


    def get_start_date(self):
        return time.strftime("%b %d %Y %H:%M", time.localtime(self.sessions[0].get_clock_in_timestamp()))


    
    def __str__(self):
        return f"""
            Project Started: {self.project_start_date}\n
            Time Spent On Project: {get_hours_min_sec(self.total_time())}\n
            Project Size Lines Of Code: {self.total_lines()}\n
            Project Size Bytes: {self.total_bytes()}
            """

    def report(self):

        print(self.__str__())

def get_hours_min_sec(secs):
    hours = secs//3600
    secs = secs - hours*3600
    minutes =   secs//60
    secs = secs - minutes*60
    seconds = secs

    hours_min_sec_string = f"{int(hours)}H {int(minutes)}M {seconds:.2f}S"

    return hours_min_sec_string


def count_lines(file):
    line_count = 0
    for line in file:
        line_count += 1

    return line_count

def count_bytes(file):
    bytes = 0
    file.seek(0, SEEK_END)
    num_bytes = file.tell()
    return num_bytes
    

if __name__ == "__main__":
    
    main()
