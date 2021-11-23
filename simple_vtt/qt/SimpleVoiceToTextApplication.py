"""
SimpleVoiceToTextApplication.py

Backbone for this project's QT handling
"""

# Batteries included
import sys
import threading

# QT packages
from PySide2 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

# Audio processing
import numpy as np
import sounddevice as sd

class SimpleVoiceToTextApplication( QtWidgets.QApplication ):
    """
    Capture realtime audio and display it
    """

    def __init__( self, mic_fs=44100, memory_seconds=10 ):
        """
        Initialize a new SimpleVoiceToTextApplication.

        Parameters
        ----------
        mic_fs : int
            The sample rate to use with the microphone, in Hz. Defaults to 44.1 KHz
        memory_seconds : float
            The capture window width, in seconds. Defaults to 10 seconds.
        """
        super( SimpleVoiceToTextApplication, self ).__init__(sys.argv)

        # Grab params from keyword args
        self.mic_fs = mic_fs
        self.memory_seconds = memory_seconds

        # Create the main window
        self.main_window = MainWindow()

        # Create the sound sample buffer
        self.sample_semaphore = threading.Lock()
        self.sample_buffer = np.zeros(self.mic_fs * self.memory_seconds)

        # Open the sound device & start it
        # blocksize of 3000 is needed to prevent buffer underruns in ALSA on my machine
        self.mic = sd.InputStream(samplerate=self.mic_fs, blocksize=3000, callback=self._onSoundSamplesReceived)
        self.mic.start()

        # Start the redraw timer at 30 FPS
        self.redraw_timer = QtCore.QTimer()
        self.redraw_timer.timeout.connect( self._redraw )
        self.redraw_timer.start( int( 1000.0 / 30 ) )

    def _onSoundSamplesReceived( self, indata, frames, time, status ):
        """Callback for our sounddevice.Stream()

        The API for this function is defined by the sounddevice
        libraries, and documented here:
            https://python-sounddevice.readthedocs.io/en/0.4.3/api/streams.html#sounddevice.Stream

        This implementation just copies the newest samples into our
        sample buffer. A semaphore is employed to prevent the redraw
        timer from blitting a half-updated buffer.
        """

        # We don't need the frames parameter, but we'll check it anyway
        assert(indata.shape[0] == frames)

        # Lock the sample buffer semaphore (so that we don't draw a half-edited buffer)
        self.sample_semaphore.acquire()

        # Roll the buffer backward, pushing the samples-to-be-overwritten to the front
        # This is technically a lot of unneeded memory writes, but it keeps the buffer easy
        # to work with and I think it will cut it for now
        self.sample_buffer = np.roll(self.sample_buffer, len(indata))

        # Overwrite the oldest samples (now at the front of the buffer) with the newest ones
        self.sample_buffer[0: len(indata)] = indata[:,0]

        # Great, done.
        self.sample_semaphore.release()

    def _redraw( self):
        """Update the displayed waveform

        This function is called at a "reasonable rate" to update the
        displayed data. This rate is intentionally decoupled from the
        microphone read rate (determined by sample rate and block
        size), which is probably a fair bit faster than needed here.
        """

        # Secure the lock before accessing the sample buffer
        self.sample_semaphore.acquire()

        if self.main_window.plot_item is None:
            # Plot data item not yet created -- must be the first update
            # Create it
            self.main_window.plot_item = self.main_window.plot_widget.plot( self.sample_buffer )

        else:
            # already have plot data item, update its data
            self.main_window.plot_item.setData( self.sample_buffer )

        # Done! Release the lock
        self.sample_semaphore.release()

class MainWindow(QtWidgets.QMainWindow):
    """Main window for the Application

    This window will show our realtime audio waveform.
    """

    def __init__( self ):
        """
        Build and show self.
        """
        super(MainWindow, self).__init__()

        # Just set something sensible into the window header
        self.setWindowTitle("Simple Voice to Text")

        # Some QT overhead for QMainWindows
        # Basically this just means "we'll add all widgets in a single column"
        top_layout = QtWidgets.QVBoxLayout()
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(top_layout)
        self.setCentralWidget(central_widget)

        # Lets create our plot widget for realtime audio display
        # We'll also need to keep a handle on the actual displayed data, which is nothing right now
        self.plot_widget = pg.PlotWidget()
        top_layout.addWidget(self.plot_widget)
        self.plot_item = None

        # That's it -- we can display the ourselves now!
        self.show()