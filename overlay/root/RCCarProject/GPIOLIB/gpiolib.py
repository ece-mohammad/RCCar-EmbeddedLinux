#!/usr/bin/env python2

# 
# Embedded Linux GPIO module utilizing sys/class/gpio
# This module is only a work around, use it only as a last resort.
# It's recommended to use other programs/modules like wiringPi,
# pigpio or RPI.gpio, and resort to this module only if you had
# problems getting the previous modules to run (you should
# ask for help though). Unlinke this module, the others
# have a community so finding ahelp shouldn't be too hard.
#
# version 1.4
#

import os
import time
import threading as thread
import logging as log

# ---------------- GPIO constants -----------------

LOW = 0
HIGH = 1

INPUT = "in"
OUTPUT = "out"

GPIO = "GPIO"
PWM = "PWM"

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

# ----------------------------- Available GPIO Pins ----------------------------
_AVAILABLE_GPIO = {
        2 : ["GPIO", "I2C_SDA"],
        3 : ["GPIO", "I2C_SCL"],
        4 : ["GPIO"],
        17: ["GPIO"],
        27: ["GPIO"],
        22: ["GPIO"],
        10: ["GPIO", "SPI0_MOSI"],
        9 : ["GPIO", "SPI0_MISO"],
        11: ["GPIO", "SPI0_CLK"],
        5 : ["GPIO"],
        6 : ["GPIO"],
        13: ["GPIO"],
        19: ["GPIO"],
        26: ["GPIO"],
        14: ["GPIO", "UART0_TXD0"],
        15: ["GPIO", "UART0_RXD0"],
        18: ["GPIO", "PCM_CLK"],
        23: ["GPIO"],
        24: ["GPIO"],
        25: ["GPIO"],
        8 : ["GPIO", "SPI0_CE0_N"],
        7 : ["GPIO", "SPI0_CE1_N"],
        12: ["GPIO"],
        16: ["GPIO"],
        20: ["GPIO"],
        21: ["GPIO"]
}

_GPIO_EXPORT_DIR = "/sys/class/gpio/export"
_GPIO_UNEXPORT_DIR = "/sys/class/gpio/unexport"
_GPIO_CLASS_DIR = "/sys/class/gpio"


# -------------------------------- GPIO pin class ------------------------------
class GPIO_Pin(object):

    # GPIO Pin attributes
    def __init__(self, pin_number, mode):

        self._pin_number = pin_number
        self._gpio_pin_class_dir = os.path.join(_GPIO_CLASS_DIR, "gpio" + str(pin_number))
        self._gpio_pin_direction_dir = os.path.join(self._gpio_pin_class_dir, "direction")
        self._gpio_pin_value_dir = os.path.join(self._gpio_pin_class_dir, "value")

        self._direction = OUTPUT
        self._last_state = 0
        self._mode = mode
        self._init_gpio_pin()

        self._pwm_duty = 0
        self._frequency = 0
        self._pwm_on = False
        self._pwm_handler = None
        self.__t_up = 0
        self.__t_dwn = 0

    # Add pin instance to /sys/class/gpio
    def _init_gpio_pin(self):

        # error code
        err_code = SUCCESS

        # check if pin is available
        if self.is_available(self._pin_number):

            _, used = self.is_used(self._pin_number)

            # if pin is not used before
            if not used:

                # export pin
                if os.system("echo \"{}\" > {}".format(self._pin_number, _GPIO_EXPORT_DIR)):

                    log.error("Failed to inistantiate pin {}.".format(self._pin_number))
                    err_code = ERR_ERROR

                else:

                    log.info("Pin {} inistance created!".format(self._pin_number))

                    # if this pin is used as a PWM pin, set it as output
                    if self._mode == PWM:
                        self.set_pin_direction(OUTPUT)
                        log.info("Pin {} configured for PWM".format(self._pin_number))

            # if pin was used before
            else:

                log.error("Failed to initialize pin {}".format(self._pin_number))
                log.debug("Failed to inistantiate pin {}. An instance already exists!".format(self._pin_number))
                err_code = ERR_INVALID_CONFIGURATION

        # if pin isn't available
        else:
            log.error("Failed to initialize pin {}".format(self._pin_number))
            log.critical("Pin {} isn't availabe for this board!".format(self._pin_number))
            err_code = ERR_INVALID_PIN_NUMBER

        return err_code

    # reconfigure pin
    def reconfigure_pin(self, mode):
        """
        Reconfigures pin
        :param mode: Mode for the pin PWM or GPIO
        :return: error code
        """

        err_code = SUCCESS

        # if current mode is PWM and PWM is running
        if self._mode == PWM and self._pwm_on:

            # stop PWM
            self.pwm_stop()
            self._pwm_on = False

        # if current mode is GPIO input
        elif self._mode == GPIO and self._direction == INPUT:

            # set mode to output
            self.set_pin_direction(OUTPUT)

        else:

            pass

        # if new mode is PWM
        if mode == PWM:

            # if current mode is GPIO
            if self._mode == GPIO:
                self._mode = PWM

            log.info("Changed pin {} mode {}".format(self._pin_number, mode))

            # set pin value low
            self.set_pin_value(LOW)

        # if new mode is GPIO
        elif mode == GPIO:

            # if current mode is PWM
            if self._mode == PWM:
                self._mode = GPIO

            log.info("Changed pin {} mode {}".format(self._pin_number, mode))

            # set pin value low
            self.set_pin_value(LOW)

        else:

            err_code = ERR_INVALID_ARGUMENT
            log.debug("Invalid mode configuration {} for pin {}".format(mode, self._pin_number))
            log.error("Failed to change pin {} mode to {}".format(self._pin_number, mode))

        return err_code

    # Remove pin instance from /sys/class/gpio
    def deinit_pin(self):

        # error code
        err_code = SUCCESS

        # if current gpio pin is already configured
        if self.is_used(self._pin_number):

            # check if pin was output/high
            if self._direction == OUTPUT and self._last_state == HIGH:
                self.set_pin_value(LOW)

            # unexport pin
            if os.system("echo {} > {}".format(str(self._pin_number), _GPIO_UNEXPORT_DIR)):

                log.error("Failed to deconfigure pin {}".format(self._pin_number))
                err_code = ERR_ERROR

            # if unexport failed
            else:

                log.info("Deconfigured pin {}".format(self._pin_number))

        # if current gpio pin is not used
        else:

            log.warning("Failed to deconfigure pin {}".format(self._pin_number))
            log.debug("GPIO Pin is not in use!")
            err_code = ERR_INVALID_CONFIGURATION

        return err_code

    # Set pin direction
    def set_pin_direction(self, direction):

        err_code = SUCCESS

        # check if pin is initialized
        if self.is_used(self._pin_number):

            # check if direction is valid
            if direction in (INPUT, OUTPUT):

                # if pin mode is GPIO
                if self._mode == GPIO:

                    # set pin direction
                    if os.system("echo \"{}\" > {}".format(direction, self._gpio_pin_direction_dir)):

                        log.error("Failed to set pin {} direction to {}".format(self._pin_number, direction))
                        log.debug("Failed to set pin {} direction!".format(self._pin_number))
                        err_code = ERR_ERROR

                    else:

                        log.info("Pin {} direction set to: {}".format(self._pin_number, direction))
                        self._direction = direction

                # if pin is used for PWM
                elif self._mode == PWM:

                    if os.system("echo \"{}\" > {}".format(OUTPUT, self._gpio_pin_direction_dir)):

                        log.error("Failed to set pin {} direction to {}".format(self._pin_number, OUTPUT))
                        log.debug("Failed to set pin {} direction!".format(self._pin_number))
                        err_code = ERR_ERROR

                    else:

                        log.info("Pin {} direction set to: {}".format(self._pin_number, OUTPUT))
                        self._direction = direction

                # if mode is invalid
                else:

                    log.error("Invalid mode {} for pin {}".format(self._mode, self._pin_number))

            # if pin direction is invalid
            else:

                log.error("Failed to set pin {} direction to {}".format(self._pin_number, direction))
                log.debug("Invalid direction ({}) for pin {}".format(direction, self._pin_number))
                err_code = ERR_INVALID_ARGUMENT

        # if pin was not initialized before
        else:

            log.error("Failed to set pin {} direction to {}".format(self._pin_number, direction))
            log.debug("No instance for pin {} in /sys/class/gpio!".format(self._pin_number))
            err_code = ERR_INVALID_CONFIGURATION

        return err_code

    # set pin value
    def set_pin_value(self, value):

        err_code = SUCCESS

        # check if pin is initialized
        if self.is_used(self._pin_number):

            # check if direction is valid
            if value in (HIGH, LOW):

                # set pin direction
                if os.system("echo \"{}\" > {}".format(value, self._gpio_pin_value_dir)):

                    log.error("Couldn't set pin {} value to {}!".format(self._pin_number, value))
                    log.debug("Failed to set pin {} value!".format(self._pin_number))
                    err_code = ERR_ERROR

                else:

                    log.debug("Pin {} value set to: {}".format(self._pin_number, value))
                    self._last_state = value

            # if pin direction is invalid
            else:

                log.error("Couldn't set pin {} value to {}!".format(self._pin_number, value))
                log.debug("Invalid value ({}) for pin {}".format(value, self._pin_number))
                err_code = ERR_INVALID_ARGUMENT

        # if pin was not initialized before
        else:

            log.error("Couldn't set pin {} value to {}!".format(self._pin_number, value))
            log.debug("No instance for pin {} in /sys/class/gpio!".format(self._pin_number))
            err_code = ERR_INVALID_CONFIGURATION

        return err_code

    # get pin value
    def get_pin_value(self):

        err_code = SUCCESS
        pin_state = LOW

        # check if pin is initialized
        if self.is_used(self._pin_number):

            # check pin direction
            if self._direction == OUTPUT:

                pin_state = self._last_state

            else:

                pin_state = int(open(self._gpio_pin_value_dir, "r").read().strip())
                self._last_state = pin_state

        # if pin was not initialized before
        else:

            log.error("Couldn't read pin {}".format(self._pin_number))
            log.debug("No instance for pin {} in /sys/class/gpio!".format(self._pin_number))
            err_code = ERR_INVALID_CONFIGURATION

        return err_code, pin_state

    # generate PWM signal on the pin
    def pwm_generate(self, frequency, duty_cycle, pulses=0):

        err_code = SUCCESS

        # check if pin mode is PWM
        if self._mode == PWM:

            # check if frequency and duty cycle are valid numbers
            if (frequency > 0) and (0 <= duty_cycle <= 100):

                self._frequency = frequency
                self._pwm_duty = duty_cycle

                # PWM time calculations
                t_total = 1.0 / frequency
                self.__t_up = duty_cycle * t_total / 100
                self.__t_dwn = t_total - self.__t_up

                # PWM thread
                self._pwm_on = True
                self._pwm_handler = thread.Thread(target=self.__gen_pwm__, args=(pulses,))
                self._pwm_handler.setDaemon(True)
                self._pwm_handler.setName("Pin{}_PWM_Thread".format(self._pin_number))
                self._pwm_handler.start()

                log.debug(
                        "Satrted PWM on pin: {} with frequency: {} and duty cycle: {}".format(self._pin_number,
                                                                                              frequency,
                                                                                              duty_cycle))

            # if duty cycle or frequency values are invalid
            else:

                log.critical("Failed to generate PWM for pin {}".format(self._pin_number))
                log.debug("Invalid frequency {} or duty cycle {} values for pin {}".format(frequency, duty_cycle,
                                                                                           self._pin_number))
                err_code = ERR_INVALID_ARGUMENT

        # if pin mode in not PWM
        else:

            log.critical("Failed to generate PWM for pin {}".format(self._pin_number))
            log.debug("Pin {} is not configured for PWM signals.".format(self._pin_number))
            err_code = ERR_INVALID_CONFIGURATION

        return err_code

    # updates PWM duty cycle
    def pwm_update(self, duty_cycle):
        """
        Updates PWM duty cycle
        :param duty_cycle:
        :return:
        """
        total_time = 1.0 / self._frequency
        self.__t_up = duty_cycle * total_time / 100
        self.__t_dwn = total_time - self.__t_up
        pass

    # stop PWM signal
    def pwm_stop(self):

        err_code = SUCCESS

        # check if pin mode is PWM
        if self._mode == PWM:

            # If PWM flag is True (set)
            if self._pwm_on:

                # clear PWM flag False (reset)
                self._pwm_on = False

            else:

                log.error("Invalid operation: Trying to stop a PWM signal on pin {} while it's not running.".format(
                        self._pin_number))
                err_code = ERR_PWM_NOT_RUNNING

        # else if pin mode is not PWM
        else:

            log.error("Invalid operation: Trying to stop a pwm signal on pin {} while it's not in PWM mode.".format(
                    self._pin_number))
            err_code = ERR_INVALID_CONFIGURATION

        return err_code

    # private method for PWM generation
    def __gen_pwm__(self, pulses):

        # number of PWM pulses is defined
        if pulses:

            n = pulses

            while n:

                # if up_time > 0
                if self.__t_up >= 0:

                    self.set_pin_value(HIGH)
                    time.sleep(self.__t_up)
                    self.set_pin_value(LOW)
                    time.sleep(self.__t_dwn)

                # if up_time == 0
                else:

                    log.error("PWM T_on {} is not larger than 0!".format(self.__t_up))
                    self.set_pin_value(LOW)

                n -= 1

        # if number of PWM pulses is 0 
        else:

            # while pwm_on flag is True (set)
            while self._pwm_on:

                # if up_time > 0
                if self.__t_up >= 0:

                    self.set_pin_value(HIGH)
                    time.sleep(self.__t_up)
                    self.set_pin_value(LOW)
                    time.sleep(self.__t_dwn)

                # if up_time == 0
                else:

                    log.error("PWM T_on {} is not larger than 0!".format(self.__t_up))
                    self.set_pin_value(LOW)

        return 0

    # check if pin is available in the board
    @staticmethod
    def is_available(pin_number):

        return bool(_AVAILABLE_GPIO.get(pin_number, None))

    # deconfigure (unexport) given pin
    @staticmethod
    def pin_deconfig(pin_number):
        """
        De-configures given pin
        :param pin_number:
        :return: error code that indicates if the pin was de-configured or not = ERR
        """

        err_code = SUCCESS

        # check if pin is valid
        if pin_number in _AVAILABLE_GPIO.get(pin_number, None):

            # if pin was unexported
            if os.system("echo {} > {}".format(pin_number, _GPIO_UNEXPORT_DIR)) == 0:

                log.debug("Pin {} was de-configured successfully.".format(pin_number))

            # if pin was not unexported
            else:

                log.error("Failed to de-configure pin {}".format(pin_number))
                err_code = ERR_ERROR

        # if pin is not valid
        else:

            log.error("Failed to de-configure pin {}".format(pin_number))
            log.debug("Pin {} is not a valid GPIO pin number!".format(pin_number))
            err_code = ERR_INVALID_PIN_NUMBER

        return err_code

    # check if pin is used (was exported before)
    @staticmethod
    def is_used(pin_number):
        """
        Checks if the given GPIO Pin is already used (configured)
        :param pin_number:
        :return: (err_code, Boolean)
        error code indicates if the function was run successfully or not
        Boolean: True if the pin is used, else False
        """

        err_code = SUCCESS
        used = False

        # check if pin_number number is valid
        if _AVAILABLE_GPIO.get(pin_number, None):

            # check if pin is used
            used = os.path.exists(os.path.join(_GPIO_CLASS_DIR, "gpio" + str(pin_number)))

        # if pin is invalid
        else:

            log.error("Pin {} isn't used as it's not available in the board!".format(pin_number))
            err_code = ERR_INVALID_PIN_NUMBER

        return (err_code, used)

    # --------------------------- configure logging ----------------------------
    @classmethod
    def log_config(cls, stream, **kwargs):
        verbosity = kwargs.get("verbosity", QUIET)
        filename = kwargs.get("filename", ".gpiolog")

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

            log.basicConfig(filename=filename, filemode='w', format="[GPIO]::%(levelname)s::%(asctime)s::%(message)s",
                            datefmt="%d/%m/%Y %I:%M:%S", level=dlevel)

        else:

            log.basicConfig(format="[GPIO]::%(levelname)s::%(asctime)s::%(message)s", datefmt="%d/%m/%Y %I:%M:%S",
                            level=dlevel)


if __name__ == "__main__":

    # # test 1 (pin 21)
    # tp = GPIO_Pin(21, GPIO)
    # tp.set_pin_direction(OUTPUT)

    # i = 0
    # while i < 10:
    #     tp.set_pin_value(HIGH)
    #     time.sleep(0.5)
    #     tp.set_pin_value(LOW)
    #     time.sleep(0.5)
    #     i += 1

    # tp.deinit_pin()

    # Test 2, threading on 4 pins
    # def sw_pwm(pin, t):

    #     tp = GPIO_Pin(pin, GPIO)
    #     tp.set_pin_direction(OUTPUT)

    #     while True:

    #         tp.set_pin_value(HIGH)
    #         time.sleep(t)
    #         tp.set_pin_value(LOW)
    #         time.sleep(t)

    #     return True

    # thread_list = list()

    # with ThreadPoolExecutor(max_workers=5) as tpe:

    #     c = 1
    #     for p in [12, 16, 20, 21]:

    #         tpe.submit(sw_pwm, p, c)
    #         c += 1

    # Test 3 : PWM on 4 pins w/ low freq (0.5, 1H)Hz
    p0 = GPIO_Pin(26, PWM)
    p1 = GPIO_Pin(12, PWM)
    p2 = GPIO_Pin(16, PWM)
    p3 = GPIO_Pin(20, PWM)
    p4 = GPIO_Pin(21, PWM)

    p0.pwm_generate(1, 30, 0)
    p1.pwm_generate(1, 50, 0)
    p2.pwm_generate(1, 50, 0)
    p3.pwm_generate(1, 50, 0)
    p4.pwm_generate(1, 50, 0)

    time.sleep(10)

    p1.pwm_update(20)
    p2.pwm_update(40)
    p3.pwm_update(60)
    p4.pwm_update(80)

    time.sleep(10)

    p0.pwm_stop()
    p1.pwm_stop()
    p2.pwm_stop()
    p3.pwm_stop()
    p4.pwm_stop()

    while thread.active_count() > 1:
        time.sleep(0.1)

    p0.deinit_pin()
    p1.deinit_pin()
    p2.deinit_pin()
    p3.deinit_pin()
    p4.deinit_pin()
