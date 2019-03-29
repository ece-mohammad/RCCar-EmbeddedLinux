#!/usr/bin/env python2

import logging as log

import motor_controller as motor
import ultrasonic

# ---------------- Logging/Debug configurations ---------------

VERBOSE = "verbose"
QUIET = "quiet"
WARNINGS = "warnings"
ERRORS = "errors"

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
FORWARD_RIGHT = 4
FORWARD_LEFT = 5
BACKWARD_RIGHT = 6
BACKWARD_LEFT = 7
STOP = 8

# ------------------------------ RC Car Controller -----------------------------


class RCCar(object):

    def __init__(self, lm_pin_1, lm_pin_2, lm_pwm_pin, rm_pin_1, rm_pin_2, rm_pwm_pin, us_trig_pin, us_echo_pin,
                 turn_rate=50, **kwargs):

        self.right_motor = None
        self.left_motor = None
        self.ultrasonic = None

        self._left_motor_pin_1 = lm_pin_1
        self._left_motor_pin_2 = lm_pin_2
        self._left_motor_pwm_pin = lm_pwm_pin

        self._right_motor_pin_1 = rm_pin_1
        self._right_motor_pin_2 = rm_pin_2
        self._right_motor_pwm_pin = rm_pwm_pin

        self._ultrasonic_trig_pin = us_trig_pin
        self._ultrasonic_echo_pin = us_echo_pin

        self._ultrasonic_min_distance = kwargs.get("us_min_distance", 5)
        self._ultrasonic_max_distance = kwargs.get("us_max_distance", 300)

        self._motor_min_speed = kwargs.get("motor_min_speed", 0)

        assert all(
                [
                        self._left_motor_pin_1,
                        self._left_motor_pin_2,
                        self._left_motor_pwm_pin,
                        self._right_motor_pin_1,
                        self._right_motor_pin_2,
                        self._right_motor_pwm_pin,
                        self._ultrasonic_trig_pin,
                        self._ultrasonic_echo_pin
                ]
        )

        self._car_turn_rate = turn_rate
        self._car_speed = 0
        self._car_direction = None

        self._distance_to_object = 0

        self._state = UNINITIALIZED

    # initialize car components
    def initialize(self):
        """
        Initialize car components (left motor, right motor, ultrasonic)
        :return: error code that indicates if the car components were initialized successfully
        """
        err_code = SUCCESS

        # create instances of car modules 9left motor, right motor, ultrasonic)
        self.right_motor = motor.MotorControl(min_speed=self._motor_min_speed)
        self.left_motor = motor.MotorControl(min_speed=self._motor_min_speed)
        self.ultrasonic = ultrasonic.UltrasonicSensor(min_distance=self._ultrasonic_min_distance,
                                                      max_distance=self._ultrasonic_max_distance, sound_speed=34000)

        # initialize car modules
        left_motor = self.right_motor.init_motor(
                pin_1=self._right_motor_pin_1,
                pin_2=self._right_motor_pin_2,
                pwm_pin=self._right_motor_pwm_pin
        )

        right_motor = self.left_motor.init_motor(
                pin_1=self._left_motor_pin_1,
                pin_2=self._left_motor_pin_2,
                pwm_pin=self._left_motor_pwm_pin
        )

        ranger = self.ultrasonic.init_ultrasonic(
                trig_pin=self._ultrasonic_trig_pin,
                echo_pin=self._ultrasonic_echo_pin
        )

        # if initializing left motor was successful
        if left_motor != motor.SUCCESS:

            err_code = ERR_ERROR
            log.critical("Left motor failed to initialize!")

        # if initializing right motor was successful
        elif right_motor != motor.SUCCESS:

            err_code = ERR_ERROR
            log.critical("Right motor failed to initialize!")

        # if initializing ultrasonic was successful
        elif ranger != ultrasonic.SUCCESS:

            err_code = ERR_ERROR
            log.critical("Ultrasonic failed to initialize!")

        else:

            self._state = READY
            log.debug("Car modules initialized successfully!")

        return err_code

    # de-initialize car modules
    def deinit(self):
        """
        De-initialize car components (left motor, right motor, ultrasonic)
        :return: error code that indicates if car modules were de-initialized successfully
        """
        err_code = SUCCESS

        # check if car is initialized
        if self._state != UNINITIALIZED:

            # deinit car modules
            self.right_motor.deinit_motor()
            self.left_motor.deinit_motor()
            self.ultrasonic.deinit_ultrasonic()

            # reset car attributes
            self.right_motor = None
            self.left_motor = None
            self.ultrasonic = None

            self._left_motor_pin_1 = None
            self._left_motor_pin_2 = None
            self._right_motor_pin_1 = None
            self._right_motor_pin_2 = None

            self._ultrasonic_trig_pin = None
            self._ultrasonic_echo_pin = None
            self._ultrasonic_min_distance = None
            self._ultrasonic_max_distance = None

            self._motor_min_speed = 0
            self._motor_pwm_freq = 20
            self._car_turn_rate = 0
            self._car_speed = 0
            self._car_direction = None

            self._distance_to_object = 0

            self._state = UNINITIALIZED

        else:

            err_code = ERR_ERROR
            log.error("Failed to deinit car modules! Car modules are already uninitialized!")

        return err_code

    # move the car in a given direction
    def move(self, direction, speed):
        """
        Move car with the given speed in the given direction
        :param direction: direction to move car in
        :param speed: speed to move car with % [0:100]
        :return: error code that indicates if the car moved successfully
        """
        err_code = SUCCESS

        # check if car is initialized
        if self._state == UNINITIALIZED:

            log.error("Trying to move car before initialization!")
            err_code = ERR_ERROR

        else:

            if 0 <= speed <= 100:

                self._car_speed = speed

            else:

                self._car_speed = 0
                log.error("Car speed {} can't be a negative number!".format(speed))

            self._state = RUNNING
            self._car_direction = direction

            # direction == stop
            if direction == STOP:

                # stop both motors
                self.right_motor.rotate_motor(direction=motor.BRAKE, speed=self._car_speed)
                self.left_motor.rotate_motor(direction=motor.BRAKE, speed=self._car_speed)
                log.debug("Car braked!")

            # direction == forward
            elif direction == FORWARD:

                # rotate both motors in the same direction (clockwise direction)
                self.right_motor.rotate_motor(direction=motor.ROTATE_CW, speed=self._car_speed)
                self.left_motor.rotate_motor(direction=motor.ROTATE_CW, speed=self._car_speed)
                log.debug("Moving car in forward direction!")

            # direction == backward
            elif direction == BACKWARD:

                # rotate both motors in the same direction (counter clockwise direction)
                self.right_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=self._car_speed)
                self.left_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=self._car_speed)
                self._state = RUNNING
                log.debug("Moving car in backwards direction!")

            # direction == rotate right
            elif direction == ROTATE_RIGHT:

                # rotate both motors in the same direction (counter clockwise direction)
                self.right_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=self._car_speed)
                self.left_motor.rotate_motor(direction=motor.ROTATE_CW, speed=self._car_speed)
                self._state = RUNNING
                log.debug("Rotating car to the right!")

            # direction == rotate left
            elif direction == ROTATE_LEFT:

                self.right_motor.rotate_motor(direction=motor.ROTATE_CW, speed=self._car_speed)
                self.left_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=self._car_speed)
                self._state = RUNNING
                log.debug("Rotating car to the left!")

            # direction == forward right
            elif direction == FORWARD_RIGHT:

                self.right_motor.rotate_motor(direction=motor.ROTATE_CW,
                                              speed=(round(self._car_speed * self._car_turn_rate/100.0, 2))
                                              )
                self.left_motor.rotate_motor(direction=motor.ROTATE_CW, speed=self._car_speed)
                self._state = RUNNING
                log.debug("Turning car to the right!")

            elif direction == FORWARD_LEFT:

                self.right_motor.rotate_motor(direction=motor.ROTATE_CW, speed=self._car_speed)
                self.left_motor.rotate_motor(direction=motor.ROTATE_CW,
                                             speed=(round(self._car_speed * self._car_turn_rate/100.0, 2))
                                             )
                self._state = RUNNING
                log.debug("Turning car to the left!")

            elif direction == BACKWARD_RIGHT:

                self.right_motor.rotate_motor(direction=motor.ROTATE_CCW,
                                              speed=(round(self._car_speed * self._car_turn_rate/100.0, 2))
                                              )
                self.left_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=self._car_speed)
                self._state = RUNNING
                log.debug("Turning car to the right!")

            elif direction == BACKWARD_LEFT:

                self.right_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=self._car_speed)
                self.left_motor.rotate_motor(direction=motor.ROTATE_CCW,
                                             speed=(round(self._car_speed * self._car_turn_rate/100.0, 2))
                                             )
                self._state = RUNNING
                log.debug("Turning car to the left!")

            else:

                log.error("Failed to move car in direction: {}".format(direction))
                log.debug("Invalid direction: {}".format(direction))
                err_code = ERR_INVALID_ARGUMENT

        return err_code

    # change motor parameters
    def change_car_params(self, speed=None, turn_rate=None):
        """
        Change car movement parameters (speed, turn rate)
        :param speed: Speed at which the car is moving
        :param turn_rate: Turn rate, how fast the car turns
        :return: error code that indicates if the car parameters were updated
        """
        err_code = SUCCESS

        # check speed
        if speed is not None:
            self._car_speed = speed
            log.debug("Changed motor speed to: {}!".format(speed))

        # check turn rate
        if turn_rate is not None:
            self._car_turn_rate = turn_rate
            log.debug("Changed turn rate to: {}!".format(speed))

        # update motors
        if (self._state != STOPPED and self._state != UNINITIALIZED) and self._car_direction is not None:
            self.move(self._car_direction, self._car_speed)

        return err_code

    # get car's speed
    def get_speed(self):
        """
        Get current car speed
        :return: (int) car speed
        """
        return self._car_speed

    # gets distance ahead of the car
    def get_distance(self):
        """
        Returns the distance to the object in front of the car
        :return: (int) distance
        """
        self._distance_to_object = self.ultrasonic.get_distance()
        return self._distance_to_object


if __name__ == '__main__':

    import time

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

    rc = RCCar(
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

    rc.initialize()

    rc.change_car_params(speed=50, turn_rate=25)

    count = 0
    max_count = 20

    while count < max_count:

        count += 1
        time.sleep(1)

        if count < max_count / 2:

            rc.move(FORWARD, 50)

        else:

            rc.move(BACKWARD, 50)

        print("speed: {}, distance: {}".format(rc.get_speed(), rc.get_distance()))

    rc.move(FORWARD, 0)
    time.sleep(5)

    rc.move(BACKWARD, 0)
    time.sleep(5)

    rc.move(STOP, 50)
    time.sleep(5)

    rc.move(FORWARD_RIGHT, 50)
    time.sleep(5)

    rc.move(FORWARD_LEFT, 50)
    time.sleep(5)

    rc.move(BACKWARD_RIGHT, 50)
    time.sleep(5)

    rc.move(BACKWARD_LEFT, 50)
    time.sleep(5)

    rc.deinit()
