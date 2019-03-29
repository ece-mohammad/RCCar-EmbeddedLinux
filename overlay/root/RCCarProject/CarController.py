#!/usr/bin/env python2

import custom_term
import rccar
import gpiolib as gpio
import time
import threading as thread
import logging as log

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
        self._speed = 0
        self._turn_rate = 0

        self._speed_step = 5
        self._turn_step = 5

        self._distance_to_object = None
        self._linear_speed = None
        self._rpm = 0  # TODO :: Add motor encoder

        self._ultrasonic_handler = None
        self._session = None

    def connect_car(self, lm_pin_1, lm_pin_2, lm_pwm_pin, rm_pin_1, rm_pin_2, rm_pwm_pin, us_trig_pin, us_echo_pin,
                    **kwargs):
        """
        Initialize car
        :param lm_pin_1 : Left motor pin 1
        :param lm_pin_2 : Left motor pin 2
        :param lm_pwm_pin : Left motor pwm pin
        :param rm_pin_1 : right motor pin 1
        :param rm_pin_2 : right motor pin 2
        :param rm_pwm_pin : right motor pwm pin
        :param us_trig_pin : ultrasonic trigger pin
        :param us_echo_pin : ultrasonic echo pin
        :param kwargs: Other parameters for car movement
                motor_min_speed : motor minimum required speed
                us_min_distance : ultrasonic minimum distance
                us_max_distance : ultrasonic maximum distance
        :return:
        """
        err_code = SUCCESS

        motor_min_speed = kwargs.get("motor_min_speed", 0)
        us_min_distance = kwargs.get("us_min_distance", 5)
        us_max_distance = kwargs.get("us_max_distance", 400)

        assert all(
                [
                        lm_pin_1, lm_pin_2, lm_pwm_pin,
                        rm_pin_1, rm_pin_2, rm_pwm_pin,
                        us_trig_pin, us_echo_pin
                ]
        )

        self._car = rccar.RCCar(
                lm_pin_1=lm_pin_1,
                lm_pin_2=lm_pin_2,
                lm_pwm_pin=lm_pwm_pin,
                rm_pin_1=rm_pin_1,
                rm_pin_2=rm_pin_2,
                rm_pwm_pin=rm_pwm_pin,
                motor_min_speed=motor_min_speed,
                us_trig_pin=us_trig_pin,
                us_echo_pin=us_echo_pin,
                us_min_distance=us_min_distance,
                us_max_distance=us_max_distance,

        )

        car_init = self._car.initialize()

        if car_init == rccar.SUCCESS:

            log.info("Car connected successfully.")
            self._session = True
            self.get_distance()

        else:

            log.critical("Failed to initialize car.")
            err_code = ERR_INVALID_CONFIGURATION

        return err_code

    def connect_controller(self):
        """
        Initializes teminal session
        :return: 0
        """
        self._controller = custom_term.CustomTerm()
        log.info("Connected to controller.")

        return 0

    def get_controller_input(self):
        """
        Gets input from controller
        :rtype: tuple
        :return: (input_type, input_message)
        """
        if self._controller:

            return self._controller.get_input()

        else:

            return None

    def process_control_signal(self, sig_type, signal):
        """
        Process input from controller
        :param sig_type: input type (1st element)
        :param signal: input message (2nd element)
        :return: 0
        """

        # if signal type is command
        if sig_type == custom_term.COMMAND:

            # if message is exit
            if signal == custom_term.EXIT_SESSION:

                self._controller.end_session()
                self._car.deinit()

                log.info("Received command signal: {}".format("exit"))
                log.debug("De-initializing controller and car!")

                sys.exit(0)

            # if message is speed up
            elif signal == custom_term.SPEED_UP:

                self._speed += self._speed_step

                if self._speed >= 100:
                    self._speed = 100

                self._car.change_car_params(speed=self._speed)

                log.info("Received command signal: {}".format("speed up"))
                log.debug("Increasing car speed to: {}".format(self._speed))

            # if message is speed down
            elif signal == custom_term.SPEED_DOWN:

                self._speed -= self._speed_step

                if self._speed <= 0:
                    self._speed = 0

                self._car.change_car_params(speed=self._speed)

                log.info("Received command signal: {}".format("speed down"))
                log.debug("Decreasing car speed to: {}".format(self._speed))

            # if message is tuen rate up
            elif signal == custom_term.TURN_RATE_UP:

                self._turn_rate += self._turn_step

                if self._turn_rate >= 100:
                    self._turn_rate = 100

                self._car.change_car_params(turn_rate=self._turn_rate)

                log.info("Received command signal: {}".format("turn rate up"))
                log.debug("Increasing car turn rate to: {}".format(self._turn_rate))

            # if message is turn rate down
            elif signal == custom_term.TURN_RATE_DOWN:

                self._turn_rate -= self._turn_step

                if self._turn_rate <= 0:
                    self._turn_rate = 0

                self._car.change_car_params(turn_rate=self._turn_rate)

                log.info("Received command signal: {}".format("turn rate down"))
                log.debug("Decreasing car turn rate to: {}".format(self._turn_rate))

            # if message is stop car
            elif signal == custom_term.STOP_CAR:

                self._car.move(direction=rccar.STOP, speed=50)

                log.info("Received command signal: {}".format("turn rate down"))
                log.debug("Decreasing car turn rate to: {}".format(self._turn_rate))

            else:

                log.error("Received an unknown command signal!")
                pass

        elif sig_type == custom_term.DIRECTION:

            if signal == custom_term.FORWARD:

                self._car.move(direction=rccar.FORWARD, speed=self._speed)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.BACKWARD:

                self._car.move(direction=rccar.BACKWARD, speed=self._speed)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.ROTATE_RIGHT:

                self._car.move(direction=rccar.ROTATE_RIGHT, speed=self._speed)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.ROTATE_LEFT:

                self._car.move(direction=rccar.ROTATE_LEFT, speed=self._speed)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.FORWARD_RIGHT:

                self._car.move(direction=rccar.FORWARD_RIGHT, speed=self._speed)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.FORWARD_LEFT:

                self._car.move(direction=rccar.FORWARD_LEFT, speed=self._speed)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.BACKWARD_RIGHT:

                self._car.move(direction=rccar.BACKWARD_RIGHT, speed=self._speed)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            elif signal == custom_term.BACKWARD_LEFT:

                self._car.move(direction=rccar.BACKWARD_LEFT, speed=self._speed)
                self._direction = signal

                log.info("Received direction signal: {}".format(signal))
                log.debug("Moving car in direction: {}".format(self._direction))

            else:

                log.error("Received an unknown data signal!")

        else:

            log.error("Can't process received signal!")
            log.debug("Invalid signal type!")

        self.update_controller_data()

        return 0

    def __update_car_data(self):
        """
        Gets distance to object from connected car
        :return: error code that indicates if the reading operation was successful
        """

        while self._session:

            # check if car is connected
            if self._car:

                self._distance_to_object = self._car.get_distance()

            else:

                self._distance_to_object = 0

            self.update_controller_data()
            time.sleep(0.1)

        return 0

    def get_distance(self):
        """

        :return:
        """
        self._ultrasonic_handler = thread.Thread(target=self.__update_car_data)
        self._ultrasonic_handler.setDaemon(True)
        self._ultrasonic_handler.setName("Ultrasonic_Handler")
        self._ultrasonic_handler.start()

        return 0

    def update_controller_data(self):
        """
        updates data in the controller
        :return: error code that indicates if the data was updated or not
        """
        err_code = SUCCESS

        # check controller
        if self._controller:

            self._controller.update_data(
                    direction=self._direction,
                    speed=self._speed,
                    turn_rate=self._turn_rate,
                    object_range=self._distance_to_object
            )

        # if controller was not initialized
        else:

            err_code = ERR_INVALID_CONFIGURATION
            log.error(

            )

        return err_code

    def deinit(self):
        """
        Disconnect car and controller
        :return: 0
        """
        self._session = None

        while self._ultrasonic_handler.is_alive():
            pass

        self._car.deinit()
        self._controller.end_session()

        return 0


if __name__ == '__main__':

    import time
    import sys

    # HearBeat Pin
    HEART_BEAT_PIN = 12

    # Right Motor Pins
    RIGHT_MOTOR_PIN_1 = 13
    RIGHT_MOTOR_PIN_2 = 19
    RIGHT_MOTOR_PWM_PIN = 26

    # Left Motor Pin
    LEFT_MOTOR_PIN_1 = 16
    LEFT_MOTOR_PIN_2 = 20
    LEFT_MOTOR_PWM_PIN = 21

    # Ultrasonic Pins
    US_TRGI_PIN = 6
    US_ECHO_PIN = 5

    US_MIN_DISTANCE = 5
    US_MAX_DISTANCE = 350

    MOTORS_MIN_SPEED = 0

    max_count = 10

    heartbeat = gpio.GPIO_Pin(HEART_BEAT_PIN, gpio.PWM)
    heartbeat.pwm_generate(1, 50)

    # CarController.log_config(stream=FILE, verbosity=CRITICAL)

    rc = CarController()

    rc.connect_controller()

    rc.connect_car(
            lm_pin_1=LEFT_MOTOR_PIN_1,
            lm_pin_2=LEFT_MOTOR_PIN_2,
            lm_pwm_pin=LEFT_MOTOR_PWM_PIN,
            rm_pin_1=RIGHT_MOTOR_PIN_1,
            rm_pin_2=RIGHT_MOTOR_PIN_2,
            rm_pwm_pin=RIGHT_MOTOR_PWM_PIN,
            us_trig_pin=US_TRGI_PIN,
            us_echo_pin=US_ECHO_PIN,
            us_min_distance=US_MIN_DISTANCE,
            us_max_distance=US_MAX_DISTANCE,
            motor_min_speed=MOTORS_MIN_SPEED
    )

    count = 0

    while True:

        s_type, sig = rc.get_controller_input()

        if s_type == custom_term.COMMAND and sig == custom_term.EXIT_SESSION:

            break

        else:

            rc.process_control_signal(s_type, sig)
            time.sleep(0.05)

    rc.deinit()
    heartbeat.pwm_stop()
    heartbeat.deinit_pin()
