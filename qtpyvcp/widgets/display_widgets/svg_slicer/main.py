#! /usr/bin/python

import sys
import cairo
import rsvg
import gtk
import hal
import xml.etree.ElementTree as ET
import time


def delete_cb(win, event, h):
    h.exit


def expose_cairo(win, event, data):
    cr = win.window.cairo_create()
    x, y, w, h = win.allocation
    cr.rectangle(x, y, w, h)
    cr.set_source_rgb(0, 0, 0)
    cr.fill()
    cr.scale(data['scale'], data['scale'])
    print "Rendering %s" % data['layerID']
    data['svgfile'].render_cairo(cr=cr, id=data['layerID'])
    return True


def fullscreen(win, event):
    win.window.unfullscreen()


def main():
    win = gtk.Window()
    oldz = 0
    svg = None
    if (len(sys.argv) > 1):
        svg = rsvg.Handle(file=sys.argv[1])
    else:
        raise SystemExit("need svg file")

    layers = dict()
    root = ET.parse(sys.argv[1]).getroot()
    for node in root.iter():
        Z = node.get("{http://www.bodgesoc.org}Z")
        if Z != None:
            layers[node.get("id")] = Z

    data = {'svgfile': svg, 'layerID': '#background', 'scale': 1.0}

    win.connect("expose-event", expose_cairo, data)

    win.show_all()

    h = hal.component("slice-viewer")
    h.newpin("Z", hal.HAL_FLOAT, hal.HAL_IN)
    h.newpin("scale", hal.HAL_FLOAT, hal.HAL_IN)
    h['scale'] = 1
    h.ready
    win.connect("delete-event", delete_cb, h)

    while h['Z'] >= 0 and win.get_visible():
        gtk.main_iteration(False)
        time.sleep(0.001)
        if oldz != h['Z'] or data['scale'] != h['scale']:
            oldz = h['Z']
            data['layerID'] = "#%s" % min(layers.items(), key=lambda (_, v): abs(oldz - float(v)))[0]
            data['scale'] = h['scale']
            win.queue_draw()


if __name__ == '__main__':
    main()