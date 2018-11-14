import numpy as np
import scipy.misc

from .pywm_widget import (
    PyWMWidget,
    PYWM_LAYER_BACK,
    PYWM_FORMATS
)


class PyWMBackgroundWidget(PyWMWidget):
    def __init__(self, wm, path):
        """
        transpose == 't': matrix transpose
        transpose == 'f': flip the image
        """
        super().__init__(wm)

        self.set_layer(PYWM_LAYER_BACK)
        im = scipy.misc.imread(path, flatten=False, mode='RGB')
        im_alpha = np.zeros(shape=(im.shape[0], im.shape[1], 4),
                            dtype=np.uint8)
        im_alpha[:, :, 0:3] = im
        im_alpha[:, :, 3] = 255

        self.width = im_alpha.shape[1]
        self.height = im_alpha.shape[0]

        im_alpha = im_alpha.reshape((self.width * self.height * 4), order='C')
        self.set_pixels(PYWM_FORMATS['ARGB8888'],
                        0,
                        self.width, self.height,
                        im_alpha.tobytes())

        self.set_box(0, 0, self.wm.width, self.wm.height)
