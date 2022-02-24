# -*- coding: utf-8 -*-
#
#         PySceneDetect: Python-Based Video Scene Detector
#   ---------------------------------------------------------------
#     [  Site: http://www.bcastell.com/projects/PySceneDetect/   ]
#     [  Github: https://github.com/Breakthrough/PySceneDetect/  ]
#     [  Documentation: http://pyscenedetect.readthedocs.org/    ]
#
# Copyright (C) 2014-2022 Brandon Castellano <http://www.bcastell.com>.
#
# PySceneDetect is licensed under the BSD 3-Clause License; see the included
# LICENSE file, or visit one of the above pages for details.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
""" ``scenedetect.video_stream`` Module

This module contains the :py:class:`VideoStream` class, which provides a library agnostic
interface for video input.  See :py:mod:`scenedetect.backends` for supported backends.

A :py:class:`VideoStream <scenedetect.video_stream.VideoStream>` is not used directly, but
by constructing a concrete implementation from :py:mod:`scenedetect.backends`.  For most
use cases, this can be done using the :py:func:`scenedetect.backends.open_video` function,
which will automatically use any available backend. Specific backends (e.g.
:py:class:`VideoStreamCv2 <scenedetect.backends.opencv.VideoStreamCv2>`) can also be
constructed directly. See the :py:mod:`scenedetect.backends` documentation for an example.

To actually implement the :py:class:`VideoStream <scenedetect.video_stream.VideoStream>`
interface, see :py:class:`VideoStreamCv2 <scenedetect.backends.opencv.VideoStreamCv2>` in
:py:mod:`scenedetect.backends.opencv` as a reference. To verify the implementation, run
the `VideoStream` test suite in `tests/test_video_stream.py` on the new backend.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Union

from numpy import ndarray

from scenedetect.platform import logger
from scenedetect.frame_timecode import FrameTimecode

##
## VideoStream Exceptions
##


class SeekError(Exception):
    """Either an unrecoverable error happened while attempting to seek, or the underlying
    stream is not seekable (additional information will be provided when possible)."""


class VideoOpenFailure(Exception):
    """Raised by a backend if opening a video fails."""


##
## VideoStream Constants & Helper Functions
##

# TODO: This value can and should be tuned for performance improvements as much as possible,
# until accuracy falls, on a large enough dataset. This has yet to be done, but the current
# value doesn't seem to have caused any issues at least.
DEFAULT_MIN_WIDTH: int = 260
"""The default minimum width a frame will be downscaled to when calculating a downscale factor."""


def compute_downscale_factor(frame_width: int, effective_width: int = DEFAULT_MIN_WIDTH) -> int:
    """Get the optimal default downscale factor based on a video's resolution (currently only
    the width in pixels is considered).

    The resulting effective width of the video will be between frame_width and 1.5 * frame_width
    pixels (e.g. if frame_width is 200, the range of effective widths will be between 200 and 300).

    Arguments:
        frame_width: Actual width of the video frame in pixels.
        effective_width: Desired minimum width in pixels.

    Returns:
        int: The defalt downscale factor to use to achieve at least the target effective_width.
    """
    assert not (frame_width < 1 or effective_width < 1)
    if frame_width < effective_width:
        return 1
    return frame_width // effective_width


##
## VideoStream Interface (Base Class)
##


class VideoStream(ABC):
    """ Interface which all video backends must implement. """

    #
    # Default Implementations
    #

    @property
    def base_timecode(self) -> FrameTimecode:
        """FrameTimecode object to use as a time base."""
        return FrameTimecode(timecode=0, fps=self.frame_rate)

    #
    # Abstract Static Methods
    #

    @staticmethod
    @abstractmethod
    def BACKEND_NAME() -> str:
        """Unique name used to identify this backend. Should be a static property in derived
        classes (`BACKEND_NAME = 'backend_identifier'`)."""
        return NotImplementedError

    #
    # Abstract Properties
    #

    @property
    @abstractmethod
    def path(self) -> Union[bytes, str]:
        """Video or device path."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> Union[bytes, str]:
        """Name of the video, without extension, or device."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_seekable(self) -> bool:
        """True if seek() is allowed, False otherwise."""
        raise NotImplementedError

    @property
    @abstractmethod
    def frame_rate(self) -> float:
        """Frame rate in frames/sec."""
        raise NotImplementedError

    @property
    @abstractmethod
    def duration(self) -> Optional[FrameTimecode]:
        """Duration of the stream as a FrameTimecode, or None if non terminating."""
        raise NotImplementedError

    @property
    @abstractmethod
    def frame_size(self) -> Tuple[int, int]:
        """Size of each video frame in pixels as a tuple of (width, height)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def aspect_ratio(self) -> float:
        """Display/pixel aspect ratio as a float (1.0 represents square pixels)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def position(self) -> FrameTimecode:
        """Current position within stream as FrameTimecode.

        This can be interpreted as presentation time stamp, thus frame 1 corresponds
        to the presentation time 0.  Returns 0 even if `frame_number` is 1."""
        raise NotImplementedError

    @property
    @abstractmethod
    def position_ms(self) -> float:
        """Current position within stream as a float of the presentation time in
        milliseconds. The first frame has a PTS of 0."""
        raise NotImplementedError

    @property
    @abstractmethod
    def frame_number(self) -> int:
        """Current position within stream as the frame number.

        Will return 0 until the first frame is `read`."""
        raise NotImplementedError

    #
    # Abstract Methods
    #

    @abstractmethod
    def read(self, decode: bool = True, advance: bool = True) -> Union[ndarray, bool]:
        """ Return next frame (or current if advance = False), or False if end of video.

        Arguments:
            decode: Decode and return the frame.
            advance: Seek to the next frame. If False, will remain on the current frame.

        Returns:
            If decode = True, returns either the decoded frame, or False if end of video.
            If decode = False, a boolean indicating if the next frame was advanced to or not is
            returned.
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """ Close and re-open the VideoStream (equivalent to seeking back to beginning). """
        raise NotImplementedError

    @abstractmethod
    def seek(self, target: Union[FrameTimecode, float, int]) -> None:
        """Seek to the given timecode. If given as a frame number, represents the current seek
        pointer (e.g. if seeking to 0, the next frame decoded will be the first frame of the video).

        For 1-based indices (first frame is frame #1), the target frame number needs to be converted
        to 0-based by subtracting one. For example, if we want to seek to the first frame, we call
        seek(0) followed by read(). If we want to seek to the 5th frame, we call seek(4) followed
        by read(), at which point frame_number will be 5.

        May not be supported on all backend types or inputs (e.g. cameras).

        Arguments:
            target: Target position in video stream to seek to.
                If float, interpreted as time in seconds.
                If int, interpreted as frame number.
        Raises:
            SeekError: An error occurs while seeking, or seeking is not supported.
            ValueError: `target` is not a valid value (i.e. it is negative).
        """
        raise NotImplementedError
