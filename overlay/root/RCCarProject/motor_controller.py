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
STOP = "stop"
BRAKE = "brake"

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

    def __init__(self, min_speed=0, pwm_freq=20):

        self._pin_1 = None
        self._pin_2 = None
        self._pwm_pin = None

        self._direction = None
        self._speed = 0

        self._state = _UNINITIALIZED

        self._pwm_freq = pwm_freq
        self._min_speed = min_speed

        # TODO :: Add speed measurements
        self._rpm = 0

    # initialize motor pins
    def init_motor(self, pin_1, pin_2, pwm_pin):

        err_code = SUCCESS

        # check pwm pin is available
        if gpio.GPIO_Pin.is_available(pwm_pin) and not gpio.GPIO_Pin.is_used(pwm_pin)[1]:

            # check if gnd pin is available
            if gpio.GPIO_Pin.is_available(pin_2) and not gpio.GPIO_Pin.is_used(pin_2)[1]:

                # check if Vcc pin is available
                if gpio.GPIO_Pin.is_available(pin_1) and not gpio.GPIO_Pin.is_used(pin_1)[1]:

                    # configure ground pin
                    self._pin_2 = gpio.GPIO_Pin(pin_2, gpio.GPIO)
                    self._pin_2.set_pin_direction(gpio.OUTPUT)
                    self._pin_2.set_pin_value(gpio.LOW)

                    # configure vcc pin
                    self._pin_1 = gpio.GPIO_Pin(pin_1, gpio.GPIO)
                    self._pin_1.set_pin_direction(gpio.OUTPUT)
                    self._pin_1.set_pin_value(gpio.LOW)

                    # configure pwm pin
                    self._pwm_pin = gpio.GPIO_Pin(pwm_pin, gpio.PWM)
                    self._pwm_pin.pwm_generate(self._pwm_freq, self._speed)

                    self._state = _STOPPED

                # if vcc pin si not available
                else:

                    log.critical("Failed to initialize motor pin 1 (default vcc)!")
                    log.debug(
                        "Motor pin {} is not available in the board or the pin is already in use!".format(pin_1))

            # if gnd pin is not available
            else:

                log.critical("Failed to initialize motor pin 2 (default ground)!")
                log.debug("Motor pin {} is not available in the board or the pin is already in use!".format(pin_2))

        # if PWM pin is not available
        else:

            log.critical("Failed to initialize motor pwm pin!")
            log.debug("Motor pin {} is not available in the board or the pin is already in use!".format(pwm_pin))

        return err_code

    # de-initialize pins
    def deinit_motor(self):
        """
        Release GPIO pins used by motor (pin-1, pin_2 and pwm_pin)
        :return: error code
        """

        err_code = SUCCESS

        if self._state != _UNINITIALIZED:

            self._pwm_pin.pwm_stop()
            self._pwm_pin.deinit_pin()
            self._pwm_pin = None

            self._pin_1.deinit_pin()
            self._pin_1 = None

            self._pin_2.deinit_pin()
            self._pin_2 = None

            log.info("Released motor pin.")

        else:

            log.error("Trying to release motor pins before initialization.")
            err_code = _ERR_INVALID_CONFIG

        return err_code

    # TODO :: Define number of pulses to rotate motor
    # rotate motor in a given direction with a given speed
    def rotate_motor(self, direction, speed=0):
        """
        Rotates motor in the given direction
        :param direction: Direction to rotate motor in (ROTATE_CW, ROTATE_CCW)
        :param speed: motor rotation speed % [0:100]
        :return: error code that indicates if the motor rotated successfully
        """
        err_code = SUCCESS

        # check motor pins
        if self._state != _UNINITIALIZED:

            # check speed limit
            if speed < self._min_speed:

                log.error("Speed is lower than the minimum speed limit! The motor may fail to rotate!")
                log.debug("Given motor speed is {} while minimum required is {}".format(speed, self._min_speed))
                err_code = _ERR_INVALID_ARGS

            # update speed changes
            if self._speed != speed:

                self._speed = speed
                self._pwm_pin.pwm_update(self._speed)

            # check if motor is not running or running in different direction
            if self._direction != direction:

                # rotation direction clockwise (pin_1 -> Vcc, pin_2 -> GND)
                if direction == ROTATE_CW:

                    self._pin_1.set_pin_value(gpio.HIGH)
                    self._pin_2.set_pin_value(gpio.LOW)

                    self._state = _RUNNING_CW
                    self._direction = ROTATE_CW

                # rotation direction counter clockwise (pin_1 -> GND, pin_2 -> Vcc)
                elif direction == ROTATE_CCW:

                    self._pin_1.set_pin_value(gpio.LOW)
                    self._pin_2.set_pin_value(gpio.HIGH)

                    self._state = _RUNNING_CCW
                    self._direction = ROTATE_CCW

                # stop motor rotation (pin_1 -> GND, pin_2 -> GND)
                elif direction == STOP:

                    self._pin_1.set_pin_value(gpio.LOW)
                    self._pin_2.set_pin_value(gpio.LOW)

                    self._state = _STOPPED
                    self._direction = STOP

                # brake motor (pin_1 -> Vcc, pin_2 -> Vcc)
                elif direction == BRAKE:

                    self._pin_1.set_pin_value(gpio.HIGH)
                    self._pin_2.set_pin_value(gpio.HIGH)

                    self._state = _STOPPED
                    self._direction = BRAKE

                # if direction is invalid
                else:

                    err_code = _ERR_INVALID_ARGS
                    log.error("Invalid rotation direction: {}!".format(direction))

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

            # check if speed >= minimum speed
            if speed >= self._min_speed:

                self._speed = speed
                self._pwm_pin.pwm_update(self._speed)

            else:

                log.error("Motor speed is less than the minimum required to rotate the motor!")

        # if motor pins are not configured
        else:

            log.error("Trying to change motor speed while the motor is not configured!")

        return err_code


if __name__ == '__main__':

    import time

    p0 = gpio.GPIO_Pin(5, gpio.PWM)
    p0.pwm_generate(1, 50)

    m0 = MotorControl(0)
    m1 = MotorControl(0)

    m0.init_motor(pin_1=16, pin_2=20, pwm_pin=21)
    m1.init_motor(pin_1=13, pin_2=19, pwm_pin=26)

    m0.rotate_motor(direction=ROTATE_CW, speed=50)
    m1.rotate_motor(direction=ROTATE_CW, speed=50)
    time.sleep(5)

    m0.rotate_motor(direction=ROTATE_CCW, speed=50)
    m1.rotate_motor(direction=ROTATE_CCW, speed=50)
    time.sleep(5)

    m0.rotate_motor(direction=STOP, speed=50)
    m1.rotate_motor(direction=STOP, speed=50)
    time.sleep(5)

    m0.rotate_motor(direction=BRAKE, speed=50)
    m1.rotate_motor(direction=BRAKE, speed=50)
    time.sleep(5)

    # TODO :: Apply this fix
    # A problem occurs here when m1 pwm thread needs some time to stop
    # so it lags behind m1
    # solution :

    m0.deinit_motor()
    m1.deinit_motor()
    p0.pwm_stop()
    p0.deinit_pin()
