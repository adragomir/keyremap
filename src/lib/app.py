import sys, traceback, os, os.path, signal, logging, logging.handlers, subprocess, optparse, time, string, io, pprint
import datetime, time, threading, Queue, re, logging
import functools

import xcb
from xcb.xproto import *
import xcb.xproto
import xcb.render
import xcb.record
import xcb.xtest
from struct import pack

import Xlib.protocol.rq, Xlib.protocol.event

import xpybutil, xpybutil.ewmh, xpybutil.icccm, xpybutil.keysymdef, xpybutil.keybind, xpybutil.util, xpybutil.window

pp = pprint.PrettyPrinter()

CONFIG_DIR = os.path.expanduser("~/.config/keyremap")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.py")


if not os.access(CONFIG_FILE, os.R_OK):
    print >> sys.stderr, 'UNRECOVERABLE ERROR: ' \
            'No configuration file found at %s' % CONFIG_FILE
    sys.exit(1)

execfile(CONFIG_FILE)

LOCK_FILE = CONFIG_DIR + "/keyremap.pid"
LOG_FILE = CONFIG_DIR + "/keyremap.log"
LOG_FILE = CONFIG_DIR + "/keyremap.log"
MAX_LOG_SIZE = 5 * 1024 * 1024 # 5 megabytes
MAX_LOG_COUNT = 3
LOG_FORMAT = "%(asctime)s %(levelname)s - %(name)s - %(message)s"

LOG = logging.getLogger("app")
logging.basicConfig()
LOG.setLevel(logging.DEBUG)

def threaded(f):

    def wrapper(*args):
        t = threading.Thread(target=f, args=args, name="Phrase-thread")
        t.setDaemon(False)
        t.start()

    wrapper.__name__ = f.__name__
    wrapper.__dict__ = f.__dict__
    wrapper.__doc__ = f.__doc__
    return wrapper

def synchronized(lock):
    """ Synchronization decorator. """

    def wrap(f):
        def new_function(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        return new_function
    return wrap

def get_wm_class(conn, win):
    prop = conn.core.GetProperty(0, win, 67, xcb.xproto.Atom.STRING, 0, 10).reply()
    if prop:
        val = str(prop.value.buf())
        if prop.bytes_after:
            prop = conn.core.GetProperty(0, win, 67, xcb.xproto.Atom.STRING, 10, prop.bytes_after / 4 + 1).reply()
            val = val + str(prop.value.buf())

    if prop is None or prop.format != 8:
        return None
    else:
        parts = str(val).split('\0')
        if len(parts) < 2:
            return None
        else:
            return parts[0], parts[1]

class KeyHandler(object):
    def __init__(self):
        self.conn = xcb.connect()
        self.setup = self.conn.get_setup()
        self.root = self.setup.roots[0].root

        self.conn.render = self.conn(xcb.render.key)
        self.conn.record = self.conn(xcb.record.key)
        self.conn.xtest = self.conn(xcb.xtest.key)
        self.catching = None

    def get_window_name(self, window=None, traverse=True):
        pass

    def get_active_window(self):
        return self.conn.core.GetInputFocus().reply().focus

    def get_window_class(self, window=None, traverse=True):
        try:
            if window is None:
                window_tmp = self.conn.core.GetInputFocus().reply().focus
            else:
                window_tmp = window
            return self._get_window_class(window_tmp, traverse)
        except Exception, e:
            LOG.error("Error get_window_class", exc_info=True)
            return ""

    def _get_window_class(self, window, traverse):
        wm_class = get_wm_class(self.conn, window)

        if (wm_class == None or wm_class == ""):
            if traverse:
                return self._get_window_class(xpybutil.window.get_parent_window(window), True)
            else:
                return ""
        if wm_class[0] == "Focus-Proxy-Window":
            # fix for focus proxy
            tmp_wmclass = self._get_window_class(xpybutil.window.get_parent_window(window), True)
            return tmp_wmclass
        return wm_class[0] + '.' + wm_class[1]

    def send_keys(self, key_string):
        xpybutil.keybind.grab_keyboard(self.get_active_window())
        mods, kc = xpybutil.keybind.parse_keystring(key_string)
        kpevent = Xlib.protocol.event.KeyPress(
            detail=kc,
            time=0,
            root=self.root,
            window=self.get_active_window(),
            child=0,
            root_x=1,
            root_y=1,
            event_x=1,
            event_y=1,
            state=mods,
            same_screen=1
        )
        xpybutil.event.send_event(self.get_active_window(), 0, kpevent._binary)
        xpybutil.keybind.ungrab_keyboard()

    def key_handler(self, code, key, e):
        window = self.get_active_window()
        wm_class = self.get_window_class(window)
        wm_name = self.get_window_name(window)
        exec(code)
        LOG.info("Caught key !!!")
    def run(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)

        p = optparse.OptionParser()
        p.add_option("-l", "--verbose", help="Enable verbose logging", action="store_true", default=False)
        options, args = p.parse_args()

        rootLogger = logging.getLogger()

        if options.verbose:
            rootLogger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler(sys.stdout)
        else:
            rootLogger.setLevel(logging.INFO)
            handler = logging.handlers.RotatingFileHandler(
                    LOG_FILE,
                    maxBytes=MAX_LOG_SIZE,
                    backupCount=MAX_LOG_COUNT
            )
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        rootLogger.addHandler(handler)

        global CONFIG
        try:
            for k in CONFIG.iterkeys():
                LOG.debug("binding key " + k)
                code = CONFIG[k]
                compiled_code = compile(code, "<string>", "exec")
                xpybutil.keybind.bind_global_key('KeyPress', k, functools.partial(self.key_handler, compiled_code))
        except Exception, e:
            LOG.error("error binding", exc_info=True)
            sys.exit(1)
        try:
            xpybutil.event.main()
        except KeyboardInterrupt:
            LOG.error("exit")
            sys.exit(1)

if __name__ == "__main__":
    kh = KeyHandler()
    kh.run(sys.argv)
