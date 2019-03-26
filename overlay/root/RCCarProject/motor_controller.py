#!/usr/bin/env python2

import logging as log
import gpiolib as gpio

# ------------------------------- Motor State ----------------------------------

_STOPPED = 0
_RUNNING_CW = 1
_RUNNING_CCW = 2

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

    def __init__(self, min_speed=30):
        self._pin_1 = None
        self._pin_2 = None
        self._direction = None
        self._speed = 0
        self._state = _STOPPED
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

        else:

            log.debug("Trying to release pin_2 before initialization.")
            err_code = _ERR_INVALID_CONFIG

        return err_code

    # rotate motor in a given direction with a given speed
    def rotate_motor(self, direction, speed=40):

        err_code = SUCCESS

        # check motor pins
        if self._pin_1 and self._pin_2:

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

                    self._pin_1.pwm_generate(20, speed)
                    self._pin_2.set_pin_value(gpio.LOW)

                # rotation direction counter clockwise (pin_1 -> GND, pin_2 -> PWM)
                elif direction == ROTATE_CCW:

                    self._pin_1.reconfigure_pin(gpio.GPIO)
                    self._pin_2.reconfigure_pin(gpio.PWM)

                    self._pin_1.set_pin_value(gpio.LOW)
                    self._pin_2.pwm_generate(20, speed)

                # if direction is invalid
                else:

                    err_code = _ERR_INVALID_ARGS
                    log.error("Invalid rotation direction: {}!".format(direction))

            # if motor is running in the same direction
            else:

                self._update_speed(speed)

        # if pins are not configured yet
        else:

            log.critical("Trying to rotate motor before initializing its pins!")
            err_code = _ERR_INVALID_CONFIG

        return err_code

    # change motor speed
    def _update_speed(self, speed):
        """
        Changes motor speed
        :param speed: new motor speed( PWM duty cycle %)
        :return: err_code
        """
        err_code = SUCCESS

        # check if motor pins are configured
        if self._pin_1 and self._pin_2:

            # check if motor is running
            if self._state != _STOPPED:

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

            else:

                log.error("Motor is not rotating, changing its speed won't have any affect!")

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
    gpio.GPIO_Pin.log_config(STDOUT, verbosity=VERBOSE)

    p0 = gpio.GPIO_Pin(5, gpio.PWM)
    m0 = MotorControl(20)
    m1 = MotorControl(20)

    p0.pwm_generate(1, 50)
    m0.init_motor(20, 21)
    m1.init_motor(12, 16)

    m0.rotate_motor(ROTATE_CW)
    m1.rotate_motor(ROTATE_CCW)
    time.sleep(10)
    m0.rotate_motor(ROTATE_CCW)
    m1.rotate_motor(ROTATE_CW)
    time.sleep(10)

    m0.deinit_motor()
    m1.deinit_motor()
    p0.pwm_stop()
    p0.deinit_pin()