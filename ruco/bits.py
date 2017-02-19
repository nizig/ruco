import collections
import inspect
import json
import os
import sys
import time
import threading
import traceback

DEBUG = 3

def err(msg):
  print("ERR", msg, file=stderr)

def warn(msg):
  DEBUG > 0 and print("WARN", msg, file=stderr)

def dbg(msg):
  DEBUG > 1 and print("DBG", msg, file=sys.stderr)

def spam(msg):
  DEBUG > 2 and print("SPAM", msg, file=sys.stderr)

class attrs(collections.OrderedDict):
  __setattr__ = collections.OrderedDict.__setitem__
  __delattr__ = collections.OrderedDict.__delitem__

  def __getattr__(self, name):
    if name not in self:
      raise AttributeError("No such attribute: %s" % name)
    return self.__getitem__(name)

def dispatch(handlers, *args, **kwargs):
  errors = []
  for fn in handlers:
    try:
      fn(*args, **kwargs)
      errors.append(None)
    except:
      errors.append(sys.exc_info())
      dbg(traceback.format_exc())
      dbg("%s%sUnhandled exception in event dispatch" % (
        os.linesep, traceback.format_exc()
      ))
  return errors

def loads(s, *a, **kw):
  if hasattr(s, "decode"):
    s = s.decode("utf-8")
  return json.loads(s, *a, object_pairs_hook=attrs, **kw)

dumps = json.dumps

def make_exc_info(ex):
  if isinstance(ex, SystemExit):
    raise ex
  try:
    raise Exception(ex)
  except:
    return sys.exc_info()

def spin(timeout, interval, test):
  if interval < 0:
    raise ValueError("'interval' must be >= 0")
  if timeout > 0 and interval > 0:
    interval = min(timeout, interval)
  remaining = timeout > 0 and timeout or 1
  while remaining > 0:
    start = time.time()
    if test and test():
      return True
    if timeout == 0:
      return False
    test_time = time.time() - start
    sleep_time = interval - test_time
    if sleep_time < 0:
      sleep_time = 0
    if timeout < 0:
      time.sleep(sleep_time)
    else:
      start = time.time()
      remaining -= test_time
      if remaining > 0:
        time.sleep(min(sleep_time, remaining))
        remaining -= time.time() - start

def trace(enabled=True, filt=True, indent=True, ignore_self=True):
  def f_module(frame):
    return (
      "__name__" in frame.f_globals and
      "%s." % frame.f_globals["__name__"] or
      ""
    )
  def f_class(frame):
    args, _, _, values = inspect.getargvalues(frame)
    if args and values and "self" in values:
      obj = values["self"]
      return (
        hasattr(obj, "__class__") and
        hasattr(obj.__class__, "__name__") and
        "%s." % obj.__class__.__name__ or
        ""
      )
    return ""
  def f_qualname(frame):
    fn = frame.f_code.co_name
    g = frame.f_globals
    if fn in g:
      fn_obj = g[fn]
      if hasattr(fn_obj, "__qualname__"):
        fn = fn_obj.__qualname__
    return fn
  def filter(module): # FIXME DX
    return (
      filt and not (
        not module or
        module.startswith("ruco") or
        module.endswith("ruco") or
        module.startswith("__")
      ))
  def t(frame, event, arg):
    try:
      label = {"call": "CALL", "return": "EXIT"}.get(event)
      if label is None:
        return
      if ignore_self and frame.f_code in (trace.__code__, t.__code__):
        return
      module = f_module(frame)
      if filter(module):
        return
      sys.stderr.write(
        "%s %s %s %s%s%s%s" % (
          threading.currentThread().name,
          indent and "." * len(inspect.stack()) or "",
          label,
          module,
          f_class(frame),
          f_qualname(frame),
          os.linesep
        ))
    except:
      pass
  if enabled:
    sys.setprofile(None)
    sys.setprofile(t)
  else:
    sys.setprofile(None)
