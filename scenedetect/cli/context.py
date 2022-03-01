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
""" ``scenedetect.cli.context`` Module

This module contains :py:class:`CliContext` which encapsulates the command-line options.
"""

from __future__ import print_function
import logging
import os
from typing import Optional, TextIO, Union

import click

from scenedetect.backends import AVAILABLE_BACKENDS
from scenedetect.cli.config import ConfigRegistry, ConfigLoadFailure, CHOICE_MAP
from scenedetect.frame_timecode import FrameTimecode, MAX_FPS_DELTA
import scenedetect.detectors
from scenedetect.platform import (check_opencv_ffmpeg_dll, get_and_create_path,
                                  get_cv2_imwrite_params, init_logger)
from scenedetect.scene_manager import SceneManager
from scenedetect.stats_manager import StatsManager, StatsFileCorrupt
from scenedetect.video_stream import VideoStream, VideoOpenFailure

logger = logging.getLogger('pyscenedetect')

USER_CONFIG = ConfigRegistry()


def parse_timecode(value: Union[str, int, FrameTimecode], frame_rate: float) -> FrameTimecode:
    """Parses a user input string into a FrameTimecode assuming the given framerate.

    If value is None, None will be returned instead of processing the value.

    Raises:
        click.BadParameter
     """
    if value is None:
        return None
    try:
        return FrameTimecode(timecode=value, fps=frame_rate)
    except (ValueError, TypeError):
        #pylint: disable=raise-missing-from
        raise click.BadParameter(
            'timecode must be in frames (1234), seconds (123.4s), or HH:MM:SS (00:02:03.400)')


def contains_sequence_or_url(video_path: str) -> bool:
    """Checks if the video path is a URL or image sequence."""
    return '%' in video_path or '://' in video_path


class CliContext:
    """Context of the command-line interface passed between the various sub-commands.

    After processing the main program options in `parse_options`, the CLI will set the options
    passed for each sub-command.  After preparing the commands, their actions are executed by
    passing this object to :py:func:`scenedetect.cli.controller.run_scenedetect`.
    """

    def __init__(self):
        self.config = USER_CONFIG
        self.options_processed: bool = False # True when CLI option parsing is complete.
        self.process_input_flag: bool = True # If False, skips video processing.

        self.video_stream: VideoStream = None
        self.base_timecode: FrameTimecode = None
        self.scene_manager: SceneManager = None
        self.stats_manager: StatsManager = None

        # Main `scenedetect` Options
        self.output_directory: str = None        # -o/--output
        self.quiet_mode: bool = None             # -q/--quiet or -v/--verbosity quiet
        self.stats_file_path: str = None         # -s/--stats
        self.drop_short_scenes: bool = None      # --drop-short-scenes
        self.min_scene_len: FrameTimecode = None # -m/--min-scene-len
        self.frame_skip: int = None              # -fs/--frame-skip

        # `time` Command Options
        self.time: bool = False
        self.start_time: FrameTimecode = None # time -s/--start
        self.end_time: FrameTimecode = None   # time -e/--end
        self.duration: FrameTimecode = None   # time -d/--duration

        # `save-images` Command Options
        self.save_images: bool = False
        self.image_extension: str = None   # save-images -j/--jpeg, -w/--webp, -p/--png
        self.image_directory: str = None   # save-images -o/--output
        self.image_param: int = None       # save-images -q/--quality if -j/-w,
                                           #   otherwise -c/--compression if -p
        self.image_name_format: str = None # save-images -f/--name-format
        self.num_images: int = None        # save-images -n/--num-images
        self.frame_margin: int = 1         # save-images -m/--frame-margin
        self.scale: float = None           # save-images -s/--scale
        self.height: int = None            # save-images -h/--height
        self.width: int = None             # save-images -w/--width

        # `split-video` Command Options
        self.split_video: bool = False
        self.split_mkvmerge: bool = None   # split-video -m/--mkvmerge
        self.split_args: str = None        # split-video -a/--override-args, -c/--copy
        self.split_directory: str = None   # split-video -o/--output
        self.split_name_format: str = None # split-video -f/--filename
        self.split_quiet: bool = None      # split-video -q/--quiet

        # `list-scenes` Command Options
        self.list_scenes: bool = False
        self.print_scene_list: bool = None      # list-scenes -q/--quiet
        self.scene_list_directory: str = None   # list-scenes -o/--output
        self.scene_list_name_format: str = None # list-scenes -f/--filename
        self.scene_list_output: bool = None     # list-scenes -n/--no-output
        self.skip_cuts: bool = None             # list-scenes -s/--skip-cuts

        # `export-html` Command Options
        self.export_html: bool = False
        self.html_name_format: str = None     # export-html -f/--filename
        self.html_include_images: bool = None # export-html --no-images
        self.image_width: int = None          # export-html -w/--image-width
        self.image_height: int = None         # export-html -h/--image-height

        # Internal variables
        self._check_input_open_failed = False # Used to avoid excessive log messages

    def _initialize(self, config: Optional[str], quiet: Optional[bool], verbosity: Optional[str],
                    logfile: Optional[TextIO]):
        """Setup logging and load application configuration file."""
        self.quiet_mode = bool(quiet)
        curr_verbosity = logging.INFO
        # Convert verbosity into it's log level enum, and override quiet mode if set.
        if verbosity is not None:
            assert verbosity in CHOICE_MAP['global']['verbosity']
            if verbosity.lower() == 'none':
                self.quiet_mode = True
                verbosity = 'info'
            else:
                # Override quiet mode if verbosity is set.
                self.quiet_mode = False
            curr_verbosity = getattr(logging, verbosity.upper())
        else:
            verbosity_str = USER_CONFIG.get_value('global', 'verbosity')
            assert verbosity_str in CHOICE_MAP['global']['verbosity']
            if verbosity_str.lower() == 'none':
                self.quiet_mode = True
            else:
                curr_verbosity = getattr(logging, verbosity_str.upper())
                # Override quiet mode if verbosity is set.
                if not USER_CONFIG.is_default('global', 'verbosity'):
                    self.quiet_mode = False

        init_logger(log_level=curr_verbosity, show_stdout=not self.quiet_mode, log_file=logfile)

        if not self.quiet_mode:
            for (log_level, log_str) in USER_CONFIG.get_init_log():
                logger.log(log_level, log_str)

        if config:
            try:
                new_config = ConfigRegistry(config)
                self.config = new_config
            except ConfigLoadFailure as ex:
                logger.error('PySceneDetect %s', scenedetect.__version__)
                for (log_level, log_str) in ex.init_log:
                    logger.log(log_level, log_str)
                logger.error("Failed to load config file!\n")
                raise click.BadParameter(
                    'Failed to read config file, see log for details.',
                    param_hint='-c/--config') from ex

            # Re-initialize logger with the correct verbosity.
            if verbosity is None and not self.config.is_default('global', 'verbosity'):
                verbosity_str = self.config.get_value('global', 'verbosity')
                assert verbosity_str in CHOICE_MAP['global']['verbosity']
                curr_verbosity = getattr(logging, verbosity_str.upper())
                self.quiet_mode = False
                init_logger(
                    log_level=curr_verbosity, show_stdout=not self.quiet_mode, log_file=logfile)


    def parse_options(self, input_path: str, output: Optional[str], framerate: float,
                      stats_file: Optional[str], downscale: Optional[int], frame_skip: int,
                      min_scene_len: str, drop_short_scenes: bool, backend: str, quiet: bool,
                      logfile: Optional[str], config: Optional[str], stats: Optional[str],
                      verbosity: Optional[str]):
        """ Parse Options: Parses all global options/arguments passed to the main
        scenedetect command, before other sub-commands (e.g. this function processes
        the [options] when calling scenedetect [options] [commands [command options]].

        This method calls the _init_video_stream(), _open_stats_file(), and
        check_input_open() methods, which may raise a click.BadParameter exception.

        Raises:
            click.BadParameter
        """

        # TODO(v1.0): Make the stats value optional (e.g. allow -s only), and allow use of
        # $VIDEO_NAME macro in the name.  Default to $VIDEO_NAME.csv.

        try:
            self._initialize(config, quiet, verbosity, logfile)
        finally:
            # Make sure we always print the version number even on any kind of init failure.
            logger.info('PySceneDetect %s', scenedetect.__version__)
            for (log_level, log_str) in self.config.get_init_log():
                logger.log(log_level, log_str)

        logger.debug("Current configuration:\n%s", str(self.config.config_dict))
        logger.debug('Parsing program options.')

        # TODO(#247): Need to set verbosity default to None and allow the case where quiet-mode=True
        # in the config, but -v debug is specified.
        self.output_directory = output

        if stats is not None and frame_skip != 0:
            self.options_processed = False
            error_strs = [
                'Unable to detect scenes with stats file if frame skip is not 1.',
                '  Either remove the -fs/--frame-skip option, or the -s/--stats file.\n'
            ]
            logger.error('\n'.join(error_strs))
            raise click.BadParameter(
                '\n  Combining the -s/--stats and -fs/--frame-skip options is not supported.',
                param_hint='frame skip + stats file')

        if self.output_directory is not None:
            logger.info('Output directory set:\n  %s', self.output_directory)

        # Have to load the input video to obtain a time base before parsing timecodes.
        if input_path is None:
            return
        self._init_video_stream(input_path=input_path, framerate=framerate, backend=backend)

        self.min_scene_len = parse_timecode(min_scene_len, self.video_stream.frame_rate)
        self.drop_short_scenes = drop_short_scenes
        self.frame_skip = frame_skip

        # Open StatsManager if --stats is specified.
        if stats_file:
            self._open_stats_file(file_path=stats_file)

        logger.debug('Initializing SceneManager.')
        self.scene_manager = SceneManager(self.stats_manager)
        if downscale is None:
            self.scene_manager.auto_downscale = True
        else:
            try:
                self.scene_manager.auto_downscale = False
                self.scene_manager.downscale = downscale
            except ValueError as ex:
                logger.debug(str(ex))
                raise click.BadParameter(str(ex), param_hint='downscale factor')
        self.options_processed = True

    def check_input_open(self):
        # type: () -> None
        """Ensure self.video_stream was initialized (i.e. -i/--input was specified),
        otherwise raises an exception.

        Raises:
            click.BadParameter if self.video_stream was not initialized.
        """
        if self.video_stream is None:
            if not self._check_input_open_failed:
                logger.error('Error: No input video was specified.')
            self._check_input_open_failed = True
            raise click.BadParameter('Input video not set.', param_hint='-i/--input')

    def add_detector(self, detector):
        """ Add Detector: Adds a detection algorithm to the CliContext's SceneManager. """
        self.check_input_open()
        options_processed_orig = self.options_processed
        self.options_processed = False
        try:
            self.scene_manager.add_detector(detector)
        except scenedetect.stats_manager.FrameMetricRegistered:
            raise click.BadParameter(
                message='Cannot specify detection algorithm twice.', param_hint=detector.cli_name)
        self.options_processed = options_processed_orig

    def _init_video_stream(self, input_path: str, framerate: Optional[float], backend: str):
        self.base_timecode = None
        try:
            if not backend in AVAILABLE_BACKENDS:
                raise click.BadParameter(
                    'Specified backend is not available on this system!', param_hint='-b/--backend')
            logger.debug('Using backend: %s / %s', backend, AVAILABLE_BACKENDS[backend].__name__)
            self.video_stream = AVAILABLE_BACKENDS[backend](input_path, framerate)
            self.base_timecode = self.video_stream.base_timecode
        except VideoOpenFailure as ex:
            dll_okay, dll_name = check_opencv_ffmpeg_dll()
            if dll_okay:
                logger.error('Backend failed to open video: %s', str(ex))
            else:
                logger.error(
                    'Error: OpenCV dependency %s not found.'
                    ' Ensure that you installed the Python OpenCV module, and that the'
                    ' %s file can be found to enable video support.', dll_name, dll_name)
                # Add additional output message in red.
                click.echo(
                    click.style(
                        '\nOpenCV dependency missing, video input/decoding not available.\n',
                        fg='red'))
            raise click.BadParameter('Failed to open video!', param_hint='-i/--input')
        except IOError as ex:
            raise click.BadParameter('Input error:\n\n\t%s\n' % str(ex), param_hint='-i/--input')

        if self.video_stream.frame_rate < MAX_FPS_DELTA:
            raise click.BadParameter(
                'Failed to obtain framerate for input video. Manually specify framerate with the'
                ' -f/--framerate option, or try re-encoding the file.',
                param_hint='-i/--input')

    def _open_stats_file(self, file_path: str):
        """Initializes this object's StatsManager, loading any existing stats from disk.
        If the file does not already exist, all directories leading up to it's eventual location
        will be created here."""
        self.stats_file_path = get_and_create_path(file_path, self.output_directory)
        self.stats_manager = StatsManager()

        logger.info('Loading frame metrics from stats file: %s',
                    os.path.basename(self.stats_file_path))
        try:
            self.stats_manager.load_from_csv(self.stats_file_path)
        except StatsFileCorrupt:
            error_info = (
                'Could not load frame metrics from stats file - file is either corrupt,'
                ' or not a valid PySceneDetect stats file. If the file exists, ensure that'
                ' it is a valid stats file CSV, otherwise delete it and run PySceneDetect'
                ' again to re-generate the stats file.')
            error_strs = ['Could not load stats file.', 'Failed to parse stats file:', error_info]
            logger.error('\n'.join(error_strs))
            # pylint: disable=raise-missing-from
            raise click.BadParameter(
                '\n  Could not load given stats file, see above output for details.',
                param_hint='input stats file')

    def save_images_command(self, num_images: int, output: Optional[str], name_format: str,
                            jpeg: bool, webp: bool, quality: int, png: bool, compression: int,
                            frame_margin: int, scale: float, height: int, width: int):
        """ Save Images Command: Parses all options/arguments passed to the save-images command,
        or with respect to the CLI, this function processes [save-images options] when calling:
        scenedetect [global options] save-images [save-images options] [other commands...].

        Raises:
            click.BadParameter
        """
        self.check_input_open()
        options_processed_orig = self.options_processed
        self.options_processed = False

        if contains_sequence_or_url(self.video_stream.path):
            error_str = '\nThe save-images command is incompatible with image sequences/URLs.'
            logger.error(error_str)
            raise click.BadParameter(error_str, param_hint='save-images')

        num_flags = sum([1 if flag else 0 for flag in [jpeg, webp, png]])
        if num_flags <= 1:

            # Ensure the format exists (default is JPEG).
            extension = 'jpg'
            if png:
                extension = 'png'
            elif webp:
                extension = 'webp'
            valid_params = get_cv2_imwrite_params()
            if not extension in valid_params or valid_params[extension] is None:
                error_strs = [
                    'Image encoder type %s not supported.' % extension.upper(),
                    'The specified encoder type could not be found in the current OpenCV module.',
                    'To enable this output format, please update the installed version of OpenCV.',
                    'If you build OpenCV, ensure the the proper dependencies are enabled. '
                ]
                logger.debug('\n'.join(error_strs))
                raise click.BadParameter('\n'.join(error_strs), param_hint='save-images')

            self.save_images = True
            self.image_directory = output
            self.image_extension = extension
            self.image_param = compression if png else quality
            self.image_name_format = name_format
            self.num_images = num_images
            self.frame_margin = frame_margin
            self.scale = scale
            self.height = height
            self.width = width

            image_type = 'JPEG' if self.image_extension == 'jpg' else self.image_extension.upper()
            image_param_type = ''
            if self.image_param:
                image_param_type = 'Compression' if image_type == 'PNG' else 'Quality'
                image_param_type = ' [%s: %d]' % (image_param_type, self.image_param)
            logger.info('Image output format set: %s%s', image_type, image_param_type)
            if self.image_directory is not None:
                logger.info('Image output directory set:\n  %s',
                            os.path.abspath(self.image_directory))
            self.options_processed = options_processed_orig
        else:
            logger.error('Multiple image type flags set for save-images command.')
            raise click.BadParameter(
                'Only one image type (JPG/PNG/WEBP) can be specified.', param_hint='save-images')
