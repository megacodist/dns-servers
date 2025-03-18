#
# 
#

import time
import sys
import threading
from enum import Enum
from typing import List, Optional


class SpinnerStyle(Enum):
    """
    Enumeration of predefined spinner styles.
    """
    BRAILLE = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    BRAILLE_DOTS = ['⠋', '⠙', '⠚', '⠒', '⠂', '⠒', '⠲', '⠴', '⠤', '⠦',
                    '⠕', '⠗', '⠎', '⠞', '⠇', '⠗', '⠕', '⠧']
    DOTS = ['.   ', '..  ', '... ', '....']
    DOTS_REVERSE = ['....', ' ...', '  ..', '   .']
    LINE = ['-', '\\', '|', '/']
    ARC = ['◜', '◠', '◝', '◞', '◡', '◟']
    ARC2 = ['\uEE06', '\uEE07', '\uEE08', '\uEE09', '\uEE0A', '\uEE0B',]
    BLOCK = ['█', '▓', '▒', '░', '▒', '▓']
    CIRCLE = ['◐', '◓', '◑', '◒']
    GROW_VERTICAL = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆',
        '▅', '▄', '▃', '▂', ' ',]
    BOUNCING_BALL = ["(●    )", "( ●   )", "(  ●  )", "(   ● )",
        "(    ●)", "(   ● )", "(  ●  )", "( ●   )",]   


class Spinner:
    """
    A class for creating and managing a text-based spinner animation
    in the console.

    **Usage Procedure:**

    1.  **Initialization:**
        *   Create a `Spinner` object, optionally providing a
            `spinner` style (either a `SpinnerStyle` enum member or
            a list of single-character strings) and an initial
            `message`.
        *   Example: `spinner = Spinner(spinner=SpinnerStyle.DOTS,
            message="Loading")`

    2.  **Starting the Spinner:**
        *   Call the `start()` method to begin the spinner animation
            in a separate thread.
        *   You can provide an optional `message` to display when
            starting. If not provided, the initial message (if any)
            from the constructor will be used. If no message is
            provided in constructor and `start` method, no message
            will be printed.
        *   Example: `spinner.start("Processing")`

    3.  **Updating the Message (Optional):**
        *   You can change the displayed message at any time by
            setting the `message` property.
        *   Example: `spinner.message = "Almost done"`

    4.  **Stopping the Spinner:**
        *   Call the `stop()` method to halt the animation.
        *   You can provide an optional `message` to display upon
            stopping. If `None` is provided, the spinner line will
            be cleared without printing any message.
        *   Example: `spinner.stop("Finished!")` or `spinner.stop()`

    5.  **Changing the spinner style (Optional):**
        *   You can change the spinner style at any time by setting
            the `spinner` property.
        *   Example: `spinner.spinner = SpinnerStyle.LINE`

    **Important Notes:**

    *   The spinner runs in a separate thread, allowing your main
        program to continue executing.
    *   The `start()` and `stop()` methods handle thread management.
    *   The `message` property is thread-safe, allowing you to
        update it from different threads.
    *   The `spinner` property is also thread-safe.
    *   The `stop()` method clears the spinner line before printing
        the final message or clearing the line, preventing messy
        output.
    """

    _INTVL_SPIN = 0.25
    """The interval of time between spinner frames."""

    _THRD_NAME = "The spinner thread"
    """The name of the spinner thread."""

    def __init__(
            self,
            spinner: list[str] | SpinnerStyle = SpinnerStyle.BRAILLE,
            message: str = "",):
        """
        Initializes the Spinner.

        Args:
            spinner: A list of characters to use for the spinner
                animation, or a SpinnerStyle enum member to use a
                predefined spinner. Defaults to SpinnerStyle.BRAILLE.
            message: Initial message to display with the spinner.
        """
        self._spinner: List[str] = []  # Initialize as empty list
        self.spinner = spinner  # Use the setter to validate and set
        self._message: str = message
        self._running: bool = False
        self._spinnerThrd: Optional[threading.Thread] = None
        self._frameIdx: int = 0
        self._msgLock: threading.Lock = threading.Lock()
        """Lock to safely update message."""
        self._lastMsgLen: int = 0
        """The length of the last output to the terminal."""

    @property
    def message(self) -> str:
        """Gets the current message."""
        with self._msgLock:
            return self._message

    @message.setter
    def message(self, value: str) -> None:
        """Sets the current message."""
        with self._msgLock:
            self._message = value

    @property
    def spinner(self) -> List[str]:
        """Gets the current spinner characters."""
        return self._spinner

    @spinner.setter
    def spinner(self, value: list[str] | SpinnerStyle) -> None:
        """Sets the current spinner characters."""
        if isinstance(value, SpinnerStyle):
            self._spinner = value.value
        elif isinstance(value, list):
            if not all(
                    isinstance(char, str) and len(char) == 1
                    for char in value):
                raise ValueError("Custom spinner must be a list of "
                                 "single-character strings.")
            self._spinner = value
        else:
            raise TypeError("spinner must be a list of strings or a "
                            "SpinnerStyle enum member.")

    def start(self, message: str = "") -> None:
        """
        Starts the spinner animation in a separate thread.

        Args:
            message: Message to display when starting. Overrides
                initial message if provided. Defaults to "".
        """
        if self._running:
            # Already running, returning...
            return
        #
        self.message = message
        self._running = True
        self._spinnerThrd = threading.Thread(
            name=self._THRD_NAME,
            target=self._spin_loop,
            daemon=True,  # Allow main thread to exit
        )
        self._spinnerThrd.start()

    def stop(self, message: str | None = None) -> None:
        """
        Stops the spinner animation and displays a final message.

        Args:
            message: Final message to display after stopping.
                If None, nothing will be printed.
        """
        # If thread is not running, doing nothing...
        if not self._running:
            return
        # Waiting for spinner thread to exit...
        self._running = False
        if self._spinnerThrd and self._spinnerThrd.is_alive():
            self._spinnerThrd.join()
        # Printing the message...
        # Clear the previous output
        sys.stdout.write(f"\r{' ' * self._lastMsgLen}\r")
        if message is not None:
            sys.stdout.write(f"{message}\n")
            sys.stdout.flush()
        sys.stdout.flush()

    def _spin_loop(self) -> None:
        """
        The main loop for the spinner thread, animating the spinner.
        """
        while self._running:
            currMsg = self.message
            spinnerChar = self.spinner[
                self._frameIdx % len(self.spinner)
            ]
            output = f"\r{currMsg} {spinnerChar}"
            self._lastMsgLen = len(output)
            sys.stdout.write(output)
            sys.stdout.flush()
            self._frameIdx += 1
            time.sleep(self._INTVL_SPIN)