"""
Cement pyfiglet extension module.
"""

from cement.core import output
from cement.utils.misc import minimal_logger
from pyfiglet import figlet_format
import six

LOG = minimal_logger(__name__)


# def extend_print(app):
#     def _print(text):
#         app.render({'out': text}, handler='print')
#     app.extend('print', _print)


class PyFigletOutputHandler(output.OutputHandler):

    """
    This class implements the :ref:`Output <cement.core.output>` Handler
    interface.  It takes a dict and only prints out the ``out`` key. It is
    primarily used by the ``app.print()`` extended function in order to replace
    ``print()`` so that framework features like ``pre_render`` and
    ``post_render`` hooks are honored. Please see the developer documentation
    on :cement:`Output Handling <dev/output>`.

    """
    class Meta:

        """Handler meta-data"""

        label = 'pyfiglet'
        """The string identifier of this handler."""

    def render(self, data, font="slant", color="blue", template=None, **kw):
        """
        Take a data dictionary and render only the ``out`` key as text output.
        Note that the template option is received here per the interface,
        however this handler just ignores it.

        Args:
            data (str): The string to render.

        Keyword Args:
            template: This option is completely ignored.

        Returns:
            str: A text string.

        """
        try:
            import colorama
            colorama.init()
        except ImportError:
            colorama = None

        try:
            from termcolor import colored
        except ImportError:
            colored = None
        
        LOG.debug("rendering content as text via %s" % self.__module__)
        return colored(figlet_format(data, font=font), color)
        

def load(app):
    app.handler.register(PyFigletOutputHandler)

