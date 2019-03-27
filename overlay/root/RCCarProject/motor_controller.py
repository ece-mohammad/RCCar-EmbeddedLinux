#!/usr/bin/env python2

import logging as log
import gpiolib as gpio

# ------------------------------- Motor State ----------------------------------

_UNINITIALIZED = 0
_STOPPED = 1
_RUNNING_CW = 2
_RUNNING_CCW = 3

# -------------------------- Rotation Directions -------------------------------

ROTATE_CW = "rcw"
ROTATE_CCW = "rccw"


# -------------------------------- Error codes ---------------------------------

SUCCESS = 0
_ERR_INVALID_PIN = 1
_ERR_USED_PIN = 2
_ERR_INVALID_CONFIG = 3
_ERR_INVALID_ARGS = 4
_ERR_ERROR = 5

# ----------------------- Logging/Debug configurations ------------------------

VERBOSE = "verbose"
QUIET = "quiet"
WARNINGS = "warnings"
ERRORS = "errors"

FILE = "file"
STDOUT = "stdout"

# ------------------------------- Motor Class ----------------------------------


class MotorControl(object):
    """
    Controls a DC motor
    Attributes:

    Methods:

    """

    def __init__(self, min_speed=0):

        self._pin_1 = None
        self._pin_2 = None
        self._direction = None
        self._speed = 0
        self._state = _UNINITIALIZED

        self._pwm_freq = 1
        self._min_speed = min_speed

        # TODO :: Add speed measurements
        # self._rpm = 0
        # self._abs_speed = 0

    # initialize motor pins
    def init_motor(self, pwm_pin, gnd_pin):

        err_code = SUCCESS

        # check pwm pin is available
        if gpio.GPIO_Pin.is_available(pwm_pin) and not gpio.GPIO_Pin.is_used(pwm_pin)[1]:

            # check if gnd pin is available
            if gpio.GPIO_Pin.is_available(gnd_pin) and not gpio.GPIO_Pin.is_used(gnd_pin)[1]:

                self._pin_1 = gpio.GPIO_Pin(pwm_pin, gpio.PWM)

                self._pin_2 = gpio.GPIO_Pin(gnd_pin, gpio.GPIO)
                self._pin_2.set_pin_direction(gpio.OUTPUT)

                self._state = _STOPPED

            # if gnd pin is not available
            else:

                log.critical("Failed to initialize motor pins!")
                log.debug("Motor pin {} is not available in the board or the pin is already in use!".format(gnd_pin))

        # if PWM pin is not available
        else:

            log.critical("Failed to initialize motor pins!")
            log.debug("Motor pin {} is not available in the board or the pin is already in use!".format(pwm_pin))

        return err_code

    # de-initialize pins
    def deinit_motor(self):
        """
        Release GPIO control over the pins
        :return: error code
        """

        err_code = SUCCESS

        if self._pin_1 and self._pin_2:

            if self._direction == ROTATE_CW:

                self._pin_1.pwm_stop()
                self._pin_1.deinit_pin()
                self._pin_2.deinit_pin()

            else:

                self._pin_2.pwm_stop()
                self._pin_2.deinit_pin()
                self._pin_1.deinit_pin()

            self._pin_1 = None
            self._pin_2 = None
            self._state = _UNINITIALIZED

        else:

            log.error("Trying to release motor pins before initialization.")
            err_code = _ERR_INVALID_CONFIG

        return err_code

    # rotate motor in a given direction with a given speed
    def rotate_motor(self, direction, speed=0):

        err_code = SUCCESS

        # check motor pins
        if self._state != _UNINITIALIZED:

            # check speed
            if speed < self._min_speed:

                log.error("Speed is lower than the minimum speed limit! The motor may fail to rotate!")
                log.debug("Given motor speed is {} while minimum required is {}".format(speed, self._min_speed))
                err_code = _ERR_INVALID_ARGS

            # check if motor is not running or running in different direction
            if self._direction != direction:

                # rotation direction clockwise (pin_1 -> PWM, pin_2 -> GND)
                if direction == ROTATE_CW:

                    self._pin_1.reconfigure_pin(gpio.PWM)
                    self._pin_2.reconfigure_pin(gpio.GPIO)

                    self._pin_1.pwm_generate(self._pwm_freq, speed)
                    self._pin_2.set_pin_value(gpio.LOW)

                    self._state = _RUNNING_CW
                    self._direction = ROTATE_CW

                # rotation direction counter clockwise (pin_1 -> GND, pin_2 -> PWM)
                elif direction == ROTATE_CCW:

                    self._pin_1.reconfigure_pin(gpio.GPIO)
                    self._pin_2.reconfigure_pin(gpio.PWM)

                    self._pin_1.set_pin_value(gpio.LOW)
                    self._pin_2.pwm_generate(self._pwm_freq, speed)

                    self._state = _RUNNING_CCW
                    self._direction = ROTATE_CCW

                # if direction is invalid
                else:

                    err_code = _ERR_INVALID_ARGS
                    log.error("Invalid rotation direction: {}!".format(direction))

            # if motor is running in the same direction
            else:

                self.update_speed(speed)

        # if pins are not configured yet
        else:

            log.critical("Trying to rotate motor before initializing its pins!")
            err_code = _ERR_INVALID_CONFIG

        return err_code

    # change motor speed
    def update_speed(self, speed):
        """
        Changes motor speed
        :param speed: new motor speed( PWM duty cycle %)
        :return: err_code
        """
        err_code = SUCCESS

        # check if motor is already running
        if self._state != _UNINITIALIZED:

            # check if speed > minimum speed
            if speed >= self._min_speed:

                self._speed = speed

                # check rotation direction
                if self._direction == ROTATE_CW:

                    self._pin_1.pwm_update(speed)

                else:

                    self._pin_2.pwm_update(speed)

            else:

                log.error("Motor speed is less than the minimum required to rotate the motor!")

        # if motor pins are not configured
        else:

            log.error("Trying to change motor speed while the motor is not configured!")

        return err_code

    # configure motor logging
    @classmethod
    def log_config(cls, stream, **kwargs):

        verbosity = kwargs.get("verbosity", QUIET)
        filename = kwargs.get("filename", ".motor_ctl_log")

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

            log.basicConfig(filename=filename, filemode='w', format="[MOTOR]::%(levelname)s::%(asctime)s::%(message)s",
                            datefmt="%d/%m/%Y %I:%M:%S", level=dlevel)

        else:

            log.basicConfig(format="[MOTOR]::%(levelname)s::%(asctime)s::%(message)s", datefmt="%d/%m/%Y %I:%M:%S",
                            level=dlevel)


if __name__ == '__main__':

    import time

    MotorControl.log_config(STDOUT, verbosity=QUIET)

    p0 = gpio.GPIO_Pin(5, gpio.PWM)
    m0 = MotorControl(20)
    m1 = MotorControl(20)

    p0.pwm_generate(1, 50)
    m0.init_motor(20, 21)
    m1.init_motor(12, 16)

    m0.rotate_motor(ROTATE_CW, speed=50)
    m1.rotate_motor(ROTATE_CW, speed=50)
    time.sleep(5)

    m0.rotate_motor(ROTATE_CW, speed=25)
    m1.rotate_motor(ROTATE_CW, speed=75)
    time.sleep(5)

    m0.rotate_motor(ROTATE_CCW, speed=50)
    m1.rotate_motor(ROTATE_CCW, speed=50)
    time.sleep(5)

    m0.rotate_motor(ROTATE_CCW, speed=25)
    m1.rotate_motor(ROTATE_CCW, speed=75)
    time.sleep(5)

    m0.deinit_motor()
    m1.deinit_motor()
    p0.pwm_stop()
    p0.deinit_pin()