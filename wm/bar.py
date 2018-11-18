from pywm import PyWMCairoWidget, PYWM_LAYER_FRONT
import cairo


class TopBar(PyWMCairoWidget):
    def __init__(self, wm):
        super().__init__(wm, wm.width, 20)
        self.text = "Top"
        self.set_layer(PYWM_LAYER_FRONT)

        self.render()
        self.update(self.wm.state)

    def update(self, wm_state):
        dy = wm_state.top_bar_dy * self.height
        self.set_box(0, dy - self.height, self.width, self.height)

    def set_text(self, text):
        self.text = text
        self.render()

    def _render(self, surface):
        ctx = cairo.Context(surface)

        ctx.set_source_rgba(.0, .0, .0, .7)
        ctx.rectangle(0, 0, self.width, self.height)
        ctx.fill()

        ctx.select_font_face('Source Code Pro for Powerline')
        ctx.set_font_size(12)
        ctx.move_to(10, .5 * self.height + 6)
        ctx.set_source_rgb(1., 1., 1.)
        ctx.show_text(self.text)
        ctx.stroke()


class BottomBar(PyWMCairoWidget):
    def __init__(self, wm):
        super().__init__(wm, wm.width, 20)
        self.text = "Bottom"
        self.set_layer(PYWM_LAYER_FRONT)

        self.render()
        self.update(self.wm.state)

    def update(self, wm_state):
        dy = wm_state.bottom_bar_dy * self.height
        self.set_box(0, self.wm.height - dy, self.width,
                     self.height)

    def set_text(self, text):
        self.text = text
        self.render()

    def _render(self, surface):
        ctx = cairo.Context(surface)

        ctx.set_source_rgba(.0, .0, .0, .7)
        ctx.rectangle(0, 0, self.width, self.height)
        ctx.fill()

        ctx.select_font_face('Source Code Pro for Powerline')
        ctx.set_font_size(12)
        ctx.move_to(10, .5 * self.height + 6)
        ctx.set_source_rgb(1., 1., 1.)
        ctx.show_text(self.text)
        ctx.stroke()
