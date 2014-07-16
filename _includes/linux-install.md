### 1. Install Prerequisites

Trep requires that the following dependencies are installed:

* Python - [http://www.python.org/](http://www.python.org/) (>=2.6) (including development header files)
* Numpy - [http://www.scipy.org/](http://www.scipy.org/) (>=1.4.1) (including development header files)
* Scipy - [http://www.scipy.org/](http://www.scipy.org/)

You also need a C compiler installed and configured properly to compile Python extensions.

To install the basic prerequisites, run the following command:
<pre>sudo aptitude install python python-dev python-numpy python-scipy</pre>


The following packages are optional. Trep should work fine without them, but they are required to use any of the visualization tools:

* PyOpenGL - [http://pyopengl.sourceforge.net/](http://pyopengl.sourceforge.net/)
* PyQt4 - [http://www.riverbankcomputing.co.uk/software/pyqt/intro](http://www.riverbankcomputing.co.uk/software/pyqt/intro)
* Python Imaging Library - [http://www.pythonware.com/products/pil/](http://www.pythonware.com/products/pil/)
* matplotlib - [http://matplotlib.sourceforge.net/](http://matplotlib.sourceforge.net/)

To install the all prerequisites including visualizations, run the following command:
<pre>
sudo aptitude install python python-dev python-opengl python-numpy python-scipy python-imaging \
     python-qt4 python-qt4-gl python-matplotlib freeglut3-dev
</pre>


### 2. Installing from source

Checkout the latest version of trep from Github using the following
<pre>git clone https://github.com/MurpheyLab/trep.git</pre>
Build trep with the following commands
<pre>
cd trep
python setup.py build
</pre>
After the compilation finishes, install trep with
<pre>sudo python setup.py install</pre>