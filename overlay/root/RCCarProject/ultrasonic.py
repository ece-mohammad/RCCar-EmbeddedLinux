#!/usr/bin/env python2

import time
import logging as log
import gpiolib as gpio

# -------------------------------- Error codes ---------------------------------

SUCCESS = 0
_ERR_INVALID_PIN = 1
_ERR_USED_PIN = 2
_ERR_INVALID_CONFIG = 3
_ERR_INVALID_ARGS = 4
_ERR_ERROR = 5

# ----------------------- Logging/Debug configurations -------------------------

VERBOSE = "verbose"
QUIET = "quiet"
WARNINGS = "warnings"
ERRORS = "errors"

FILE = "file"
STDOUT = "stdout"


# ------------------------------- Ultrasonic -----------------------------------

class UltrasonicSensor(object):

    def __init__(self, min_distance=4, max_distance=300, sound_speed=34000):
        self._trig_pin = None
        self._echo_pin = None
        self._distance = 0
        self._min_distance = min_distance
        self._max_distance = max_distance
        self._sound_speed = sound_speed
        self._max_time = float(self._max_distance) / self._sound_speed
        self._min_time = float(self._min_distance) / self._sound_speed

    # initialize ultrasonic sensor GPIO pins
    def init_ultrasonic(self, trig_pin=None, echo_pin=None):
        """
        Initializes ultrasonic pins
        :return: error code that indicates if the pins were initialized
        """

        err_code = SUCCESS

        # check if trigger pin is available
        if gpio.GPIO_Pin.is_available(trig_pin) and not gpio.GPIO_Pin.is_used(trig_pin)[1] and trig_pin:

            if gpio.GPIO_Pin.is_available(echo_pin) and not gpio.GPIO_Pin.is_used(echo_pin)[1] and echo_pin:

                self._trig_pin = gpio.GPIO_Pin(trig_pin, gpio.GPIO)
                self._echo_pin = gpio.GPIO_Pin(echo_pin, gpio.GPIO)

                self._trig_pin.set_pin_direction(gpio.OUTPUT)
                self._echo_pin.set_pin_direction(gpio.INPUT)

                self._trig_pin.set_pin_value(gpio.LOW)

            else:

                log.error("Failed to configure Echo pin: {} for ultrasonic sensor!".format(echo_pin))
                log.debug("The pin {} is either used before or is unavailable for this board!".format(echo_pin))
                err_code = _ERR_INVALID_PIN

        # trigger pin is not available or is already used
        else:

            log.error("Failed to configure Trigger pin: {} for ultrasonic sensor!".format(trig_pin))
            log.debug("The pin {} is either used before or is unavailable for this board!".format(trig_pin))
            err_code = _ERR_INVALID_PIN

        return err_code

    # de configure ultrasonic GPIO pins
    def de_init(self):
        """
        Deconfigure GPIO pins associated with trigger/echo pins of the
        ultrasonic module
        :return: 0
        """
        if self._trig_pin and self._echo_pin:

            gpio.GPIO_Pin.deinit_pin(self._trig_pin)
            gpio.GPIO_Pin.deinit_pin(self._echo_pin)

            self._trig_pin = None
            self._echo_pin = None

        return 0

    # measures distance to the first object in front of the ultrasonic sensor
    def get_distance(self):
        """
        :returns the distance to the first object in front of the sensor
        :return: int
        """

        # check if pins have been initialized
        if self._trig_pin and self._echo_pin:

            # set trigger pin low
            self._trig_pin.set_pin_value(gpio.LOW)
            self.micro_sleep(2000)

            # send trigger pulse (HIGH for 10 microseconds)
            self._trig_pin.set_pin_value(gpio.HIGH)
            self.micro_sleep(10)
            self._trig_pin.set_pin_value(gpio.LOW)

            start = time.time()
            # wait for echo
            while self._echo_pin.get_pin_value()[1] == gpio.LOW and (time.time() - start) < self._max_time:
                pass

            if (time.time() - start) > (self._max_time + 3e5):

                log.error("Echo signal delayed too long, either an object is too close or too far from the sensor!")
                distance = -1

            else:

                rise = time.time()
                while self._echo_pin.get_pin_value()[1] == gpio.HIGH:
                    pass

                fall = time.time()
                delta = rise - fall

                if delta <= (self._min_time + 2e5):

                    log.debug("Object is too close to the sensor!")

                elif delta >= (self._max_time + 2e5):

                    log.debug("Object is too far from the sensor!")

                else:

                    pass

                distance = (fall - rise) * self._sound_speed / 2

        # if pins were not initialized
        else:

            log.critical("Trying to echo without initializing pins!")
            distance = -1

        return distance

    # microsecond sleep
    @staticmethod
    def micro_sleep(micro_sec):

        start_time = time.time()

        while time.time() - start_time < micro_sec * (1e-6):
            pass

        return 0

    # configure ultrasonic logging
    @classmethod
    def log_config(cls, stream, **kwargs):
        verbosity = kwargs.get("verbosity", QUIET)
        filename = kwargs.get("filename", ".ultrasonic_log")

        # logger for debugging
        if verbosity == VERBOSE:

            dlevel = log.DEBUG

        elif verbosity == QUIET:

            dlevel = log.INFO

        elif verbosity == WARNINGS:

            dlevel = log.WARNING

        elif verbosity == ERRORS:

            dlevel = log.ERROR

        else:

            dlevel = log.INFO

        if stream == FILE:

            log.basicConfig(filename=filename, filemode='w',
                            format="[ULTRASONIC]::%(levelname)s::%(asctime)s::%(message)s",
                            datefmt="%d/%m/%Y %I:%M:%S", level=dlevel)

        else:

            log.basicConfig(format="[ULTRASONIC]::%(levelname)s::%(asctime)s::%(message)s", datefmt="%d/%m/%Y %I:%M:%S",
                            level=dlevel)


if __name__ == '__main__':

    import math

    p0 = gpio.GPIO_Pin(5, gpio.PWM)
    p0.pwm_generate(1, 50)

    us = UltrasonicSensor(max_distance=400)
    us.init_ultrasonic(trig_pin=26, echo_pin=19)

    normalize = lambda x: round(x, 2)

    count = 0
    while count < 20:

        res = normalize(us.get_distance())
        print("Distance: {} cm".format(res))

        time.sleep(.5)
        count += 1

    us.de_init()
    p0.deinit_pin()
