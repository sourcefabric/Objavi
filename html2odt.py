#!/usr/bin/python
"""Convert html files to ODF.

html2odt source.html destination.odt
"""

from __future__ import with_statement
import sys, os, subprocess, time

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException

def _inspect_obj(o):
    print >> sys.stdout, 'inspecting %r' % o
    for a in  dir(o):
        try:
            print >> sys.stdout, "%25s %s" % (a, getattr(o, a))
        except Exception, e:
            print >> sys.stdout, "%s DOES NOT WORK! (%s)" % (a, e)

def file_url(path):
    if path.startswith('file:///'):
        return path
    return "file://" + os.path.abspath(path)

class Oo(object):
    def __init__(self):
        """Start up an open office and connect to it."""
        accept_string = "socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"

        self.ooffice = subprocess.Popen(["ooffice", "-nologo", "-nodefault",
                                         "-norestore",
                                         "-headless", # "-invisible",
                                         "-accept=%s" % accept_string])

        for i in range(10):
            time.sleep(0.5)
            try:
                local = uno.getComponentContext()
                self.resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
                self.context = self.resolver.resolve("uno:" + accept_string)
                self.desktop = self.unobject("com.sun.star.frame.Desktop", self.context)
                return

            except NoConnectException:
                print '.',

    def unobject(self, klass, context=None):
        """get an instance of the class named by <klass>.  It will
        probably be a string that looks like
        'com.sun.something.SomeThing'."""
        if context is None:
            return self.context.ServiceManager.createInstance(klass)
        return self.context.ServiceManager.createInstanceWithContext(klass, context)

    def convert(self, src, dest):
        """Use the connected open office instance to convert the file
        named by <src> into odf and save it as <dest>.

        The main trick here is forcing the images to be stored inline."""
        src = file_url(src)
        dest = file_url(dest)

        doc = self.desktop.loadComponentFromURL(src, "_blank", 0,
                                                (PropertyValue("Hidden" , 0 , True, 0),))

        gp = self.unobject("com.sun.star.graphic.GraphicProvider")

        #Reset each graphic object to an embedded copy of itself.
        #there are probably simpler ways to iterate, but this works.
        for gn in doc.GraphicObjects.ElementNames:
            g = doc.GraphicObjects.getByName(gn)
            props = (PropertyValue("URL", 0, g.GraphicURL, 0),)
            g.setPropertyValue("Graphic", gp.queryGraphic(props))

        doc.storeToURL(dest, (PropertyValue("FilterName", 0, 'writer8', 0),
                              PropertyValue("Overwrite", 0, True, 0 )))
        doc.dispose()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.desktop.dispose()
        self.context.dispose()
        self.ooffice.kill()


if __name__ == '__main__':
    src, dest = sys.argv[1:3]
    with Oo() as oo:
        oo.convert(src, dest)


