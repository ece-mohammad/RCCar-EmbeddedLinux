#!/usr/bin/env python2

import time


def micro_sleep(micro_sec):

    start_time = time.time()

    while time.time() - start_time < micro_sec * (1e-6):
        pass

    # time.sleep(micro_sec*1e-6)

    return 0


if __name__ == '__main__':

    def overhead(t):

        st = time.time()
        micro_sleep(t)
        e = time.time()
        time_slept = 1e6*(e - st)
        # print("Sleeping for {} micro seconds, actual time: {}, overhead: {}".format(t, time_slept, time_slept-t))
        return time_slept, time_slept-t

    trials = dict()

    for run in range(1000):

        for t in range(1, 100):

            oh = overhead(t)
            v = trials.get(t, None)

            if v:

                trials[t][0] += oh[0]
                trials[t][1] += oh[1]

            else:

                trials[t] = list(oh)

    for k in trials.keys():
        print("Micro sleep for {}, actual sleep time: {}, overhead: {}".format(k, trials[k][0]/1000.0, trials[k][1]/1000.0))