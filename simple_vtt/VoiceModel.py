"""
VoiceModel.py

Classes for extracting properties from a speaker in an audio clip.
"""

import numpy as np
import scipy.signal as sps

AUDIO_PROCESSING_WINDOW_SECONDS = 3
AUDIO_PROCESSING_SAMPLE_HZ      = 8000

class VoiceModel:
    """Analyze voice in an audio clip, in real-time.

    This class performs realtime analytics on an individual voice
    given a mono audio input.

    Properties
    ----------
    inspect : VoiceModelInspectionData
        Contains various fields for debugging and visualizing the
        model's behavior.
    """

    def __init__(self):
        """Initialize a VoicModel

        Initialize a new VoiceModel

        Parameters
        ----------
        """
        self.audio_buffer = np.zeros(AUDIO_PROCESSING_SAMPLE_HZ * AUDIO_PROCESSING_WINDOW_SECONDS)

    def process_audio_clip( self, samples, fs, contiguous=False ):
        """Fit to some additional audio.

        Feed in an additional sound clip to analyze.

        Parameters
        ----------
        samples : np.array( real )
            The raw audio samples
        fs : float
            The sample rate, in Hz
        contiguous : bool
            Whether the beginning of this sample is directly
            connected to the end of the last provided sample.
            Typically True for realtime processing and False
            otherwise.
        """
        if fs != AUDIO_PROCESSING_SAMPLE_HZ:
            raise NotImplementedError( "Sorry -- for now, need to supply data in correct frequency." )
        if contiguous is False:
            raise NotImplementedError( "Sorry -- only contiguous data for now." )

        # Roll the buffer backward, pushing the samples-to-be-overwritten to the front
        # This is technically a lot of unneeded memory writes, but it keeps the buffer easy
        # to work with and I think it will cut it for now
        self.audio_buffer = np.roll(self.audio_buffer, len(samples))

        # Overwrite the oldest samples (now at the front of the buffer) with the newest ones
        self.audio_buffer[0: len(samples)] = samples[:,0]

    def stft( self ):
        """Calculate and return the short-time Fourier transform of the processing window

        This function calculates and returns the STFT of the audio
        processing window (the last AUDIO_PROCESSING_WINDOW_SECONDS of
        received audio).

        The return format matches Scipy's stft() implementation.
        """
        return sps.stft(self.audio_buffer, fs=AUDIO_PROCESSING_SAMPLE_HZ, nperseg=AUDIO_PROCESSING_SAMPLE_HZ/20)
