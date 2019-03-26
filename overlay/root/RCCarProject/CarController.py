#!/usr/bin/env python2

import custom_term
import rccar
import logging as log
import time
import gpiolib as gpio

# ---------------- Logging/Debug configurations ---------------

VERBOSE = "verbose"
QUIET = "quiet"
WARNINGS = "warnings"
ERRORS = "errors"
CRITICAL = "critical"

FILE = "file"
STDOUT = "stdout"

# ---------------------------------- Error codes -------------------------------

SUCCESS = 0
ERR_INVALID_PIN_NUMBER = 1
ERR_INVALID_ARGUMENT = 2
ERR_INVALID_CONFIGURATION = 3
ERR_PWM_NOT_RUNNING = 4
ERR_ERROR = 5

# -------------------------------- States --------------------------------------

UNINITIALIZED = 0
READY = 1
RUNNING = 2
STOPPED = 3

# ----------------------------- Directions -------------------------------------

FORWARD = 0
BACKWARD = 1
ROTATE_RIGHT = 2
ROTATE_LEFT = 3
TURN_RIGHT = 4
TURN_LEFT = 5


# ------------------------ Car controller class --------------------------------
class CarController(object):

    def __init__(self):

        self._controller = None
        self._car = None
        self._last_key = None

        self._direction = None
        self._linear_speed = None
        self._distance_to_object = None

        self._turn_rate = 0
        self._speed = 0
        self._rpm = 0   # TODO :: Add motor encoder

        self._speed_step = 1
        self._turn_step = 1

    def connect_car(self, **kwargs):

        err_code = SUCCESS

        lm_pin_1 = kwargs.get("left_motor_pin_1", None)
        lm_pin_2 = kwargs.get("left_motor_pin_2", None)
        rm_pin_1 = kwargs.get("right_motor_pin_1", None)
        rm_pin_2 = kwargs.get("right_motor_pin_2", None)
        us_t_pin = kwargs.get("ultrasonic_trig_pin", None)
        us_e_pin = kwargs.get("ultrasonic_echo_pin", None)

        self._car = rccar.RCCar(
                left_motor_pin_1=lm_pin_1,
                left_motor_pin_2=lm_pin_2,
                right_motor_pin_1=rm_pin_1,
                right_motor_pin_2=rm_pin_2,
                ultrasonic_trig_pin=us_t_pin,
                ultrasonic_echo_pin=us_e_pin
        )

        car_init = self._car.initialize()

        if car_init == rccar.SUCCESS:

            log.info("Car connected successfully.")

        else:

            log.critical("Failed to initialize car.")
            err_code = ERR_INVALID_CONFIGURATION

        return err_code

    def connect_controller(self):

        self._controller = custom_term.CustomTerm()
        log.info("Connected to controller.")

    def get_controller_input(self):

        return self._controller.get_input()

    def process_control_signal(self, sig_type, signal):

        if sig_type == custom_term.COMMAND:

            if signal == custom_term.EXIT_SESSION:

                self._car.deinit()
                self._controller.end_session()

                log.info("Received command signal: {}".format("exit"))
                log.debug("De-initializing controller and car!")

                sys.exit(0)

            elif signal == custom_term.SPEED_UP:

                self._speed += self._speed_step

                if self._speed > 100:
                    self._speed = 100

                self._car.change_motor_params(speed=self._speed)

                log.info("Received command signal: {}".format("speed up"))
                log.debug("Increasing car speed to: {}".format(self._speed))

            elif signal == custom_term.SPEED_DOWN:

                self._speed -= self._speed_step

                if self._speed < 0:
                    self._speed = 0

                self._car.change_motor_params(speed=self._speed)

                log.info("Received command signal: {}".format("speed down"))
                log.debug("Decreasing car speed to: {}".format(self._speed))

            elif signal == custom_term.TURN_RATE_UP:

                self._turn_rate += self._turn_step

                if self._turn_rate > 100:
                    self._turn_rate = 100

                self._car.change_motor_params(turn_rate=self._turn_rate)

                log.info("Received command signal: {}".format("turn rate up"))
                log.debug("Increasing car turn rate to: {}".format(self._turn_rate))

            elif signal == custom_term.TURN_RATE_DOWN:

                self._turn_rate += self._turn_step

                if self._turn_rate < 0:
                    self._turn_rate = 0

                self._car.change_motor_params(turn_rate=self._turn_rate)

                log.info("Received command signal: {}".format("turn rate down"))
                log.debug("Decreasing car turn rate to: {}".format(self._turn_rate))

            else:

                log.error("Received an unknown command signal!")
                pass

        elif sig_type == custom_term.DIRECTION:

            if signal == custom_term.FORWARD:

                self._car.move(rccar.FORWARD)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.BACKWARD:

                self._car.move(rccar.BACKWARD)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.ROTATE_RIGHT:

                self._car.move(rccar.ROTATE_RIGHT)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.ROTATE_LEFT:

                self._car.move(rccar.ROTATE_LEFT)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.TURN_RIGHT:

                self._car.move(rccar.TURN_RIGHT)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.TURN_LEFT:

                self._car.move(rccar.TURN_LEFT)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            else:

                log.error("Received an unknown data signal!")

        else:

            log.error("Can't ptrocess received signal!")
            log.debug("Invalid signal type!")
            pass

        self.update_controller_data()

    def update_distance_to_object(self):

        self._distance_to_object = self._car.get_distance()
        self.update_controller_data()

    def update_controller_data(self):

        self._controller.update_data(direction=self._direction, speed=self._speed, turn_rate=self._turn_rate, object_range=self._distance_to_object)

    def deinit(self):

        self._car.deinit()
        self._controller.end_session()
        self._on_going_session = False

    # --------------------------- configure logging ----------------------------
    @classmethod
    def log_config(cls, stream, **kwargs):

        verbosity = kwargs.get("verbosity", CRITICAL)
        filename = kwargs.get("filename", ".car_ctl_log")

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

            log.basicConfig(filename=filename, filemode='w', format="[Controller]::%(levelname)s::%(asctime)s::%(message)s",
                            datefmt="%d/%m/%Y %I:%M:%S", level=dlevel)

        else:

            log.basicConfig(format="[Controller]::%(levelname)s::%(asctime)s::%(message)s", datefmt="%d/%m/%Y %I:%M:%S",
                            level=dlevel)


if __name__ == '__main__':

    import time
    import sys

    lmp1 = 21
    lmp2 = 20
    rmp1 = 16
    rmp2 = 12
    ustp = 26
    usep = 19
    hbp = 5

    max_count = 10

    heartbeat = gpio.GPIO_Pin(hbp, gpio.PWM)

    CarController.log_config(stream=FILE, verbosity=CRITICAL)

    rc = CarController()

    rc.connect_car(
            left_motor_pin_1=lmp1,
            left_motor_pin_2=lmp2,
            right_motor_pin_1=rmp1,
            right_motor_pin_2=rmp2,
            ultrasonic_trig_pin=ustp,
            ultrasonic_echo_pin=usep
    )

    heartbeat.pwm_generate(1, 50)
    rc.connect_controller()

    count = 0

    while True:

        sig_type, sig = rc.get_controller_input()
        rc.process_control_signal(sig_type, sig)
        rc.update_distance_to_object()
        time.sleep(0.1)

    rc.deinit()
    heartbeat.pwm_stop()
    heartbeat.deinit_pin()
    sys.exit(0)