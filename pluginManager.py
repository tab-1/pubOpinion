#! usr/bin/env python3
from iPlugin import Plugin
from imp import find_module,load_module,acquire_lock,release_lock
import os
import sys

class PluginManager(object):
    """Base class for plugin managers. Does not implement loadPlugins, so it
    may only be used with a static list of plugins.
    """
    name = "base"

    def __init__(self,plugins=(),config={}):
        self.__plugins = []
        if plugins:
            self.addPlugins(plugins)

    def __iter__(self):
        return iter(self.plugins)

    def addPlugin(self,plug):
        print ('PluginManager add plugin:', plug)
        self.__plugins.append(plug)

    def addPlugins(self,plugins):
        for plug in plugins:
            self.addPlugin(plug)

    def delPlugin(self,plug):
        if plug in self.__plugins:
            self.__plugins.remove(plug)

    def delPlugins(self,plugins):
        for plug in plugins:
            self.delPlugin(plug)

    def getPlugins(self,name=None):
        plugins = []
        for plugin in self.__plugins:
            if(name is None or plugin.name == name ):
                plugins.append(plugin)
                print('plugin.name: ', plugin.name)
        return plugins

    def _loadPlugin(self,plug):
        loaded = False
        print('******PluginManager _loadPlugin, ',self.plugins)
        for p in self.plugins:
            if p.name == plug.name:
                loaded = True
                break
        if not loaded:
            self.addPlugin(plug)
            print  ("%s: loaded plugin %s " % (self.name, plug.name))

    def loadPlugins(self):
        pass

    def _get_plugins(self):
        return self.__plugins

    def _set_plugins(self, plugins):
        self.__plugins = []
        self.addPlugins(plugins)

    plugins = property(_get_plugins, _set_plugins, None,
                       """Access the list of plugins managed by
                       this plugin manager""")



class DirectoryPluginManager(PluginManager):
    """Plugin manager that loads plugins from plugin directories.
    """
    name = "directory"

    def __init__(self, plugins=(), config={}):
        default_directory = os.path.join(os.path.dirname(__file__),"plugins")
        self.directories = config.get("directories", (default_directory,))
        print ('========DirectoryPlugManager========',plugins)
        PluginManager.__init__(self, plugins, config)

    def loadPlugins(self):
        """Load plugins by iterating files in plugin directories.
        """
        plugins = []
        print ('********Directory directories:',self.directories)
        for dir in self.directories:
            try:
                for f in os.listdir(dir):
                    if f.endswith(".py") and f != "__init__.py":
                        plugins.append((f[:-3], dir))
            except OSError:
                print ("Failed to access: %s" % dir)
                continue

        fh = None
        mod = None
        print ('********Directory all plugins:',plugins)
        for (name, dir) in plugins:
            try:
                acquire_lock()
                fh, filename, desc = find_module(name, [dir])
                print ('********Directory fh,filename,desc:',fh,filename,desc,name)
                old = sys.modules.get(name)
                if old is not None:
                    # make sure we get a fresh copy of anything we are trying
                    # to load from a new path
                    del sys.modules[name]
                mod = load_module(name, fh, filename, desc)
            finally:
                if fh:
                    fh.close()
                release_lock()
            if hasattr(mod, "__all__"):
                print ('********Directory mod  __all__:',mod.__all__)
                attrs = [getattr(mod, x) for x in mod.__all__]
                print ('********Directory attrs:',attrs)
                for plug in attrs:
                    if not issubclass(plug, Plugin):
                        continue
                    self._loadPlugin(plug())