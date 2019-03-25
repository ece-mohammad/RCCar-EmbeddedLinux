#!/usr/bin/env python2

import time
import threading as thread

def thread_handler(num):

    # while True:
    print("Thread {} Echo: {} Time: {}".format(thread.current_thread(), num, time.ctime(time.time())))
    time.sleep(1)

def main():

    thread_list = list()

    for i in range(10):

        # th = thread.Thread(target=thread_handler, name="thread"+str(i), args=(i,))
        th = thread.Thread(target=thread_handler, args=(i,))
        th.setDaemon(True)
        th.setName("Thread<{}>".format(i))
        thread_list.append(th)
    
    for i in thread_list:
        print("Starting thread: {} at: {}".format(i.getName(), time.ctime(time.time())))
        i.start()

if __name__ == '__main__':

    main()