
# Obtaining PySceneDetect

PySceneDetect is completely free software, and can be downloaded from the links below.  See the [license and copyright information](copyright.md) page for details.  If you have trouble running PySceneDetect, ensure that you have all the required dependencies listed in the [Installing Dependencies](#installing-dependencies) section below.


## Download

### PyPI (All Platforms, Requires `pip`)

Start by ensuring you have downloaded and installed all of the [system requirements](#installing-dependencies) (specifically the Python OpenCV `cv2` module).  Once this is done, you can get the latest version of [PySceneDetect on the Python Package Index](https://pypi.python.org/pypi/PySceneDetect) by running the following command:

```md
sudo pip install pyscenedetect
```

After installation, you can call PySceneDetect from any terminal/command prompt by typing `scenedetect` (try running `scenedetect --version` to verify that everything was installed correctly).  Alternatively, you can install PySceneDetect from the source archives below.


<h3>Source (All Platforms) &nbsp; <span class="wy-text-neutral"><span class="fa fa-windows"></span> &nbsp; <span class="fa fa-linux"></span> &nbsp; <span class="fa fa-apple"></span></span></h3>

<div class="important">
<h3 class="wy-text-neutral"><span class="fa fa-forward wy-text-info"></span> Latest Release: <b class="wy-text-neutral">v0.3.5</b></h3>
<h4 class="wy-text-neutral"><span class="fa fa-calendar wy-text-info"></span>&nbsp; Release Date:&nbsp; <b>August 2, 2016</b></h4>
<a href="https://github.com/Breakthrough/PySceneDetect/archive/v0.3.5.zip" class="btn btn-info" style="margin-bottom:8px;" role="button"><span class="fa fa-download"></span>&nbsp; <b>Download</b>&nbsp;&nbsp;.zip</a> &nbsp;&nbsp;&nbsp;&nbsp; <a href="https://github.com/Breakthrough/PySceneDetect/archive/v0.3.5.tar.gz" class="btn btn-info" style="margin-bottom:8px;" role="button"><span class="fa fa-download"></span>&nbsp; <b>Download</b>&nbsp;&nbsp;.tar.gz</a> &nbsp;&nbsp;&nbsp;&nbsp; <a href="#installation" class="btn btn-warning" style="margin-bottom:8px;" role="button"><span class="fa fa-gear"></span>&nbsp; <b>Installation</b></a> &nbsp;&nbsp;&nbsp;&nbsp; <a href="../examples/usage/" class="btn btn-danger" style="margin-bottom:8px;" role="button"><span class="fa fa-book"></span>&nbsp; <b>Getting Started</b></a>
</div>

Once you've downloaded the source archive, extract it to a location of your choice, and make sure you have the appropriate [system requirements](#installing-dependencies) installed before continuing.  PySceneDetect can be installed by running the following command in the location of the extracted files:

```md
sudo python setup.py install
```

After installation, you can call PySceneDetect from any terminal/command prompt by typing `scenedetect` (try running `scenedetect --version` to verify that everything was installed correctly).


------------------------------------------------


## Installation

Start by downloading the latest release of PySceneDetect and extracting it to a location of your choice.  Then, follow the instructions below under [Installing Dependencies](#installing-dependencies) to ensure you have all the system requirements.  Finally, run the commands in [Installing PySceneDetect](#installing-pyscenedetect) to install the program, allowing you to run the `scenedetect` command from any terminal/command prompt.


### Installing Dependencies

PySceneDetect requires [Python 2 or 3](https://www.python.org/) (tested on 2.7.X, untested but should work on 3.X) and the following libraries ([quick install guide](http://breakthrough.github.io/Installing-OpenCV/)):

 - [OpenCV](http://opencv.org/) (compatible with both 2.X or 3.X) and the Python module (`cv2`)
 - [Numpy](http://sourceforge.net/projects/numpy/) Python module (`numpy`)

You can [click here](http://breakthrough.github.io/Installing-OpenCV/) for a quick guide (OpenCV + Numpy on Windows & Linux) on installing the latest versions of OpenCV/Numpy on [Windows (using pre-built binaries)](http://breakthrough.github.io/Installing-OpenCV/#installing-on-windows-pre-built-binaries) and [Linux (compiling from source)](http://breakthrough.github.io/Installing-OpenCV/#installing-on-linux-compiling-from-source).  If the Python module that comes with OpenCV on Windows is incompatible with your system architecture or Python version, [see this page](http://www.lfd.uci.edu/~gohlke/pythonlibs/#opencv) to obtain a pre-compiled (unofficial) module.

Note that some Linux package managers still provide older, dated builds of OpenCV (pre-3.0).  PySceneDetect is compatible with both versions, but if you want to ensure you have the latest version, it's recommended that you [build and install OpenCV from source](http://breakthrough.github.io/Installing-OpenCV/#installing-on-linux-compiling-from-source) on Linux.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
To ensure you have all the requirements installed, open a `python` interpreter, and ensure you can run `import numpy` and `import cv2` without any errors.  Once this is done, you're ready to instalL PySceneDetect!


### Installing PySceneDetect

Go to the folder you extracted the PySceneDetect source code to, and run the following command (may require root):

```md
python setup.py install
```

Once finished, PySceneDetect will be installed, and you should be able to run the `scenedetect` command.  To verify that everything was installed properly, try calling the following command:

```md
scenedetect --version
```

To get familiar with PySceneDetect, try running `scenedetect --help`, or continue onwards to the [Getting Started: Basic Usage](examples/usage.md) section.  If you encounter any runtime errors while running PySceneDetect, ensure that you have all the required dependencies listed in the System Requirements section above (again, you should be able to `import numpy` and `import cv2`).  PySceneDetect is still beta software, so feel free to [report any bugs or share some feature requests/ideas](contributing.md) and help make PySceneDetect even better.

