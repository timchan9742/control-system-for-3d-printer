from printer import *
from web_app import run_web_app
from multiprocessing import Process

def main():
    process_web_app = Process(target=run_web_app)
    process_web_app.start()
    ##run the printer control system on the main thread
    printer = Printer()
    printer.run()

if __name__ == '__main__':
    main()
