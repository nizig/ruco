"""
clicker - rapid command-line user interface development

- Provides convenient syntax and semantics for constructing command-line
  interfaces definitions, and tools to speed up development of command-line
  applications.

- Define all commands, options, and arguments accepted by an application using
  a straight-forward syntax in yaml or json.

- For simple applications, an argument parser is easily instantiated for a
  CLI definition, and callbacks for commands/options/arguments are
  automatically mapped to Python functions implemented by the user.
  (See the main function of this script for an example of this idiom.)

- For complex applications, skeleton Python source code can be generated for
  command/option/argument handlers from a CLI definition in yaml/json, which
  can then be implemented incrementally by the user.

- The command-line interface definition semantics allow 'inheritance', that
  is, deriving a new CLI definition from an existing one, which could be useful
  for complex applications with many commands that are more similar than
  different.

- Last but far from least, clicker is built using the (outstanding, fantastic,
  amazing, where-would-I-be-without-it) Click toolkit:

    http://click.pocoo.org/

Nicholas A. Zigarovich <nzigarovich@ritchiebros.com>
"""

from __future__ import print_function

import click
import collections
import copy
import json
import sys
import traceback
import yaml

try:
  import IPython
  pp = IPython.lib.pretty.pprint
  def debug():
    traceback.print_exc()
    IPython.embed()
except ImportError:
  pp = print
  import pdb
  def debug():
    traceback.print_exc()
    pdb.pm()

def popkey(d, key, default=None):
  if key in d:
    r = d[key]
    del d[key]
    return r
  return default

def merge(old, new):
  def shift(k):
    if k in new:
      old[k] = new[k]
  shift("name")
  shift("help")
  shift("options")
  shift("arguments")
  if "commands" in new:
    if "commands" not in old:
      old["commands"] = new["commands"]
    else:
      for new_command in new["commands"]:
        try:
          old_command = [
            x for x in old["commands"]
            if x["name"] == new_command["name"]
          ][0]
          old["commands"].remove(old_command)
        except IndexError:
          pass
        old["commands"].append(new_command)
  if "groups" in new:
    if "groups" not in old:
      old["groups"] = new["groups"]
    else:
        for new_group in new["groups"]:
          try:
            old_group = [
              x for x in old["groups"]
              if x["name"] == new_group["name"]
            ][0]
            merge(old_group, new_group)
          except IndexError:
            old["groups"].append(new_group)
  return old

def stub(
  data, fd=sys.stdout, groups=False, get_cb=None, tab="  ", indent=0,
  imports=True
):
  def tabs(): return indent * tab
  def push(): tabs += 1
  def pop(): tabs -= 1
  def p(s): fd.write(s)

  path = []

  if get_cb is None:
    get_cb = lambda p: "_".join(p)

  def build_options(o):
    pass

  def print_command(c):
    paths.append(c["name"])
    p(tabs() + "def %s(%s):\n" % (get_cb(path), build_options(c)))
    push()
    p(tabs() + "pass\n\n")
    pop()
    paths.pop()

  def print_commands(g):
    for c in g.get("commands", ()):
      print_command(c)

  def print_group(g):
    paths.append(g["name"])
    if groups:
      p(tabs() + "def %s(%s):\n" % (get_cb(path), build_options(g)))
      push()
      p(tabs() + "pass\n\n")
      pop()
    print_commands(g)
    paths.pop()

  def print_groups(g):
    for gg in g.get("groups", ()):
      print_group(gg)

  if imports:
    p(tabs() + "import click\n\n")
    p(tabs() + "get_context = click.get_current_context\n")
    p(tabs() + "get_obj = lambda: get_context().obj\n\n")
  print_group(data)

def build(
  data, env=None, get_cb=None, require_commands=True, require_groups=False
):
  path = []

  if get_cb is None:

    def get_cb(p, r):
      n = "_".join(p)
      f = (env or globals()).get(n)
      if not f and r:
        raise KeyError("Required callback not found in globals(): %s" % n)
      return f

  def build_argument(a):
    a = copy.copy(a)
    name = popkey(a, "name")
    a["type"] = eval(a.get("type", "None"), {"click": click})
    a["default"] = eval(a.get("default", "None"))
    a["nargs"] = eval(a.get("nargs", "None"))
    return click.Argument([name], **a)

  def build_arguments(c):
    return [build_argument(x) for x in c.get("arguments", ())]

  def build_option(o):
    o = copy.copy(o)
    name = popkey(o, "name").split(" ")
    o["type"] = eval(o.get("type", "None"), {"click": click})
    o["default"] = eval(o.get("default", "None"))
    for n in name:
      if n.startswith("--"):
        break
    else:
      n = None
    if n:
      o["envvar"] = "%s_%s" % (
        "_".join(path).upper(),
        n[2:].replace("-", "_").upper()
      )
    return click.Option(name, **o)

  def build_options(o):
    return [build_option(x) for x in o.get("options", ())]

  def build_command(c, require_cb=require_commands, cls=click.Command):
    c = copy.copy(c)
    path.append(c["name"])
    try:
      c["callback"] = get_cb(path, require_cb)
      c["params"] = build_options(c)
      c["params"].extend(build_arguments(c))
      popkey(c, "options")
      popkey(c, "arguments")
      popkey(c, "commands")
      name = popkey(c, "name")
      return cls(name, **c)
    finally:
      path.pop()

  def build_commands(g):
    return [build_command(x) for x in g.get("commands", ())]

  def build_group(g):
    group = build_command(g, require_cb=require_groups, cls=click.Group)
    try:
      path.append(g["name"])
      for subgroup in build_groups(g):
        group.add_command(subgroup, name=subgroup.name)
      for command in build_commands(g):
        group.add_command(command)
      return group
    finally:
      path.pop()

  def build_groups(g):
    return [build_group(x) for x in g.get("groups", ())]

  if len(data.get("groups", ())) == 0 and len(data.get("commands", ())) == 0:
    rv = build_command(data)
  else:
    rv = build_group(data)
  return rv
  #return build_group(data)

def _setup_yaml():
  def representer(dumper, data):
    return dumper.represent_dict(data.items())
  def constructor(loader, node):
    return collections.OrderedDict(loader.construct_pairs(node))
  tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG
  yaml.add_representer(collections.OrderedDict, representer)
  yaml.add_constructor(tag, constructor)

JSON = "json"
YAML = "yaml"

def loads(s, type=YAML, data={}):
  "Load from string."
  if type == JSON:
      new_data = json.loads(s, object_pairs_hook=collections.OrderedDict)
  elif type == YAML:
    _setup_yaml()
    new_data = yaml.load(s, Loader=yaml.loader.BaseLoader)
  else:
    raise ValueError("Invalid type: %s" % type)
  return merge(data, new_data)

def loadf(f, type=None, data={}):
  "Load from file."
  if type is None:
    if path.lower().endswith("json"):
      type = JSON
    elif path.lower()[-4:] in (".yml", "yaml"):
      type = YAML
    else:
      raise ValueError("Can't determine file type: %s" % f)
  with open(f) as fd:
    return loads(fd.read(), type=type, data=data)

def loadmf(files, type=None, data={}):
  "Load from many files."
  for f in files:
    load(f, type=type, data=data)
  return data

def loadfd(fd, type=YAML, data={}):
  "Load from file descriptor."
  raise NotImplementedError()

def loadmfd(fds, type=YAML, data={}):
  "Load from many file descriptors."
  raise NotImplementedError()

class Cli:

  def __init__(self):
    self.data = {}
    self.cli = None

  def loads(self, s, type=YAML):
    loads(s, type=type, data=self.data)

  def loadf(self, file, type=None):
    loadf(file, type=type, data=self.data)

  def loadmf(self, files, type=None):
    loadmf(files, data=self.data)

  def loadfd(self, fd, type=YAML):
    loadfd(fd, type=type, data=self.data)

  def loadmfd(self, fds, type=YAML):
    loadmfd(fds, type=type, data=self.data)

  def build(self, *args, **kwargs):
    self.cli = build(self.data, *args, **kwargs)

  def run(self, *args, **kwargs):
    self.build(*args, **kwargs)
    self.cli()

  def clear(self):
    self.__init__()

_yaml = """

name: clicker
help: Do things with clicker CLI definitions
commands:
  - name: merge
    help: Merge multiple definition files into one
    options:
      - name: -o --output
        help: Output file, default -
        type: click.File('wb')
        default: '"-"'
      - name: -f --format
        help: Output format, default yaml
        type: click.Choice(["json", "yaml"])
        default: '"yaml"'
    arguments:
      - name: files
        nargs: -1
        required: yes
  - name: stub
    help: Generate Python stubs from defininition files
    options:
      - name: -o --output
        help: Output file, default -
        type: click.File("wb")
        default: '"-"'
      - name: -g --groups
        help: Generate group callbacks
        is_flag: yes
      - name: --no-imports
        help: Don't generate imports
        is_flag: yes
      - name: -t --tab
        help: Tab string, default '"  "'
        default: '"  "'
      - name: -c --click-stubs
        help: Generate Click stubs
        is_flag: yes
    arguments:
      - name: files
        nargs: -1
        required: yes
"""

def clicker_merge(output, format, files):
  d = loadmf(files)
  if format == YAML:
    output.write(yaml.dump(d))
  elif format == JSON:
    output.write(json.dumps(d))

def clicker_stub(output, groups, no_imports, tab, click_stubs, files):
  d = loadmf(files)
  stub(d, fd=output, groups=group, imports=(not no_imports), tab=tab)

def main():
  cli = Cli()
  cli.loads(_yaml)
  cli.run(require_groups=True)

if __name__ == "__main__":
  main()

