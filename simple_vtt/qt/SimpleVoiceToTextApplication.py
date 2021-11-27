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

# audio IO
import sounddevice as sd

from simple_vtt.VoiceModel import *

DEFAULT_SAMPLE_RATE = 8000

def getapp():
    """Convenience method to retrieve the QApplication singleton
    """
    return SimpleVoiceToTextApplication.instance()

class SimpleVoiceToTextApplication( QtWidgets.QApplication ):
    """
    Capture realtime audio and display it
    """

    def __init__( self, mic_fs=DEFAULT_SAMPLE_RATE ):
        """
        Initialize a new SimpleVoiceToTextApplication.

        Parameters
        ----------
        mic_fs : int
            The sample rate to use with the microphone, in Hz. Defaults to 44.1 KHz
        """
        super( SimpleVoiceToTextApplication, self ).__init__(sys.argv)

        # Grab params from keyword args
        self.mic_fs = mic_fs

        # Create the voice model & a semaphore to protect it
        self.voice_model = VoiceModel()
        self.voice_model_semaphore = threading.Lock()

        # Create the main window
        self.main_window = MainWindow()

        # Open the sound device & start it
        # blocksize parameter needs to be sufficiently high to avoid ALSA underrun conditions
        # Mono audio for now
        self.mic = sd.InputStream(samplerate=self.mic_fs,
                                  blocksize=int( mic_fs/31),
                                  channels=1,
                                  callback=self._onSoundSamplesReceived)
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

        # Update the voice model
        self.voice_model_semaphore.acquire()
        self.voice_model.process_audio_clip( indata, self.mic_fs, contiguous=True )
        self.voice_model_semaphore.release()

    def _redraw(self):
        """Update the displayed waveform

        This function is called at a "reasonable rate" to update the
        displayed data. This rate is intentionally decoupled from the
        microphone read rate (determined by sample rate and block
        size), which is probably a fair bit faster than needed here.
        """

        # Safely grab a copy of the current buffer
        self.voice_model_semaphore.acquire()
        self.main_window.redraw()
        self.voice_model_semaphore.release()

class MainWindow(QtWidgets.QMainWindow):
    """Main window for the Application

    This window will show our realtime audio waveform.
    """

    def __init__(self):
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
        self.plot_widget.setLabel( "left", "Air Pressure on Microphone Membrane" )
        self.plot_widget.setLabel( "bottom", "Time (seconds)" )
        top_layout.addWidget(self.plot_widget)
        self.plot_item = None

        # Add the STFT plot
        self.stft_plot = pg.PlotWidget()
        self.stft_plot.setLabel( "bottom", "Time (seconds)" )
        self.stft_plot.setLabel( "left", "Frequency (Hz)" )
        self.stft_item = None
        top_layout.addWidget(self.stft_plot)

        # That's it -- we can display the ourselves now!
        self.show()

    def redraw(self):
        """Update all widgets with new data

        Recalculate all features and update all plots with new data.
        """

        # Time-domain sample
        audio_clip = getapp().voice_model.audio_buffer
        x = np.linspace(0, len(audio_clip)/getapp().mic_fs, len(audio_clip))
        if self.plot_item is None:
            # Plot data item not yet created -- must be the first update
            # Create it
            self.plot_item = self.plot_widget.plot(x, audio_clip)

        else:
            # already have plot data item, update its data
            self.plot_item.setData( x, audio_clip )

        # STFT
        freqs, times, img = getapp().voice_model.stft()
        img = np.absolute( img ).T
        if self.stft_item is None:
            self.stft_item = pg.ImageItem( img )
            self.stft_item.setColorMap(pg.colormap.getFromMatplotlib('rainbow'))
            self.stft_item.setLevels((0, 0.01))
            self.stft_item.scale( times[-1] / img.shape[0], freqs[-1] / img.shape[1])
            self.stft_plot.addItem( self.stft_item )
        else:
            self.stft_item.setImage(img, autoLevels=False)
