#!/usr/bin/env python

import fileinput
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import re
import platform
import sys

### get_sys_config: define system and diagram geometry here
def get_sys_config():
    hostname=platform.node()
    hostname='trestles'
    if hostname.find("gordon") != -1 or hostname.find("gcn") != -1:
        config = {  'rack_xdim':    8,         # nodes per rack in x direction
                    'rack_ydim':    8,         # nodes per rack in y direction
                    'subrack_ydim': 2,         # rows per subrack (if applicable)
                    'racks_per_row':10,        # racks per row in final plot
                    'size_x':       0.5,       # width of each node's graphic
                    'size_y':       1.0,       # height of each node's graphic
                    'system':       'gordon',  # the system's name
                    'ppn':          16         # how many cores per node
                 }
    else:
        config = {  'rack_xdim':    1,         # nodes per rack in x direction
                    'rack_ydim':    32,        # nodes per rack in y direction
                    'racks_per_row':6,         # racks per row in final plot
                    'size_x':       8.0,       # width of each node's graphic
                    'size_y':       0.75,      # height of each node's graphic
                    'system':       'trestles',# the system's name
                    'ppn':          32         # how many cores per node
                 }
        if hostname.find("trestles") == -1:
            sys.stderr.write("Unknown system %s; assuming %s.\n" % (hostname, config['system']))
    return config

### draw_rack: wrapper function that calls the machine-specific draw function
def draw_rack( loadgrid, cpugrid, rack, ax, config ):
    if config['system'] == 'gordon':
        draw_rack_gordon( loadgrid, cpugrid, rack, ax, config )
    elif config['system'] == 'trestles':
        draw_rack_trestles( loadgrid, cpugrid, rack, ax, config )

### Subroutine to draw Gordon's racks.  Note that the meaning of x/y are
### currently screwed up in the code, but the end result is right.  I need
### to fix this someday.
def draw_rack_gordon( loadgrid, cpugrid, rack, ax, config):

    ppn = config['ppn']

    # how wide/tall do our nodes appear in the plot?
    size_x = config['size_x']
    size_y = config['size_y']

    # how many racks do we draw per row on the plot?
    racks_per_row = config['racks_per_row']

    # coordinates in rack space
    rack_x = float(rack%racks_per_row)
    rack_y = float(int(rack / racks_per_row))

    # coordinates in node space
    # rack_xdim * size_x gives the width of a whole rack.  we add +2 nodes for 
    # padding between racks
    node_x = float(rack_x * ((2+config['rack_xdim'])*size_x))
    node_y = float(rack_y * ((2+config['rack_ydim'])*size_y))

    # add text label for this rack
    plt.text(node_x, node_y-0.1, "rack %d" % rack)

    supernodes = list()

    for (y,x),w in np.ndenumerate(loadgrid):

        if w < -1.5:
            color = 'grey'
        elif w < -0.5:
            color = 'red'
        elif w > (1.1 * float(ppn)):
            color = 'yellow'
        else:
            color = cm((0.50 + w/float(cpugrid[y,x]))/1.25)

        # coordinates on the actual plot
        plot_x = x*size_x + node_x
        plot_y = y*size_y + node_y

        # if this is the last node in a vsmp supernode, draw the supernode
        if cpugrid[y, x] > ppn:
            my_size_x = size_x * config['rack_xdim']
            my_size_y = size_y * config['subrack_ydim']
        else:
            my_size_x = size_x
            my_size_y = size_y
        
        rect = plt.Rectangle([plot_x, plot_y], 
            my_size_x, 
            my_size_y,
            facecolor=color,
            edgecolor='black')

        if cpugrid[y, x] > ppn:
            supernodes.append(rect)
        else:
            ax.add_patch(rect)

    # draw supernodes last so they are on top of the compute nodes
    for rect in supernodes:
        ax.add_patch(rect)

### Subroutine to draw Trestles's racks.  TODO: merge this with draw_rack_gordon
def draw_rack_trestles( loadgrid, cpugrid, rack, ax, config):

    ppn = config['ppn']

    # how wide/tall do our nodes appear in the plot?
    size_x = config['size_x']
    size_y = config['size_y']

    # how many racks do we draw per row on the plot?
    racks_per_row = config['racks_per_row']

    # coordinates in rack space
    rack_x = float((rack-1) % racks_per_row)
    rack_y = float(int((rack-1) / racks_per_row))

    # coordinates in node space
    # rack_xdim * size_x gives the width of a whole rack.  we add +2 for 
    # padding between racks
    node_x = float(rack_x * (config['rack_xdim']*size_x + 2.0) )
    node_y = float(rack_y * (config['rack_ydim']*size_y + 2.0))

    # add text label for this rack
    plt.text(node_x, node_y+0.5, "rack %d" % rack)

    supernodes = list()

    for (x,y),w in np.ndenumerate(loadgrid):

        # special hacks for trestles-some racks are just not populated
        if y < 2:
            continue
        if rack == 12 and y > 25:
            continue

        if w < -1.5:
            color = 'grey'
        elif w < -0.5:
            color = 'red'
        elif w > (1.1 * float(ppn)):
            color = 'yellow'
        else:
            color = cm((0.50 + w/float(cpugrid[x,y]))/1.25)

        # coordinates on the actual plot
        plot_x = x*size_x + node_x
        plot_y = y*size_y + node_y

        my_size_x = size_x
        my_size_y = size_y
        
        rect = plt.Rectangle([plot_x, plot_y], 
            my_size_x, 
            my_size_y,
            facecolor=color,
            edgecolor='black')

        ax.add_patch(rect)


if __name__ == '__main__':

    config = get_sys_config()

    ### initialize the plot
    ax = plt.gca()
#   ax.patch.set_facecolor('white')
    ax.patch.set_facecolor((1,1,1,0.0))
    ax.axis('off')
    
    ax.set_aspect('equal', 'box')
    ax.xaxis.set_major_locator(plt.NullLocator())
    ax.yaxis.set_major_locator(plt.NullLocator())
    cm = plt.get_cmap('Blues')

    linerex = re.compile(r"""
        ^(\S+)-(\d+)-(\d+)\s+
        \d+\s+
        \d+\s+
        (\d+)\s+
        \d+/\d+\s+
        \S+\s+
        \S+\s+
        (\d+\.\d+)\s*
        (\S+)\s*$""", re.VERBOSE)
    staterex = re.compile("(offline|down)")

    cpugrid = np.empty([config['rack_xdim'],config['rack_ydim']])
    cpugrid[:] = config['ppn']
    loadgrid = np.empty([config['rack_xdim'],config['rack_ydim']])
    loadgrid[:] = -2.0      # -2 means node doesn't exist in queue
    this_rack = -1
    last_rack_printed = -1;
    ax = plt.gca()

    for line in fileinput.input():
        match = linerex.match(line)
        if not match:
            continue
        nodename = match.group(1)
        rack = int(match.group(2))
        slot = int(match.group(3))
        cpus = int(match.group(4))
        load = float(match.group(5))

        if rack != this_rack:
            if this_rack >= 0:
                draw_rack( loadgrid, cpugrid, this_rack, ax, config )
                last_rack_printed = this_rack

            loadgrid[:] = -2.0      # initialize a new rack of unknown nodes
            cpugrid[:] = config['ppn']
            this_rack = rack

        if staterex.match(match.group(6)):
            load = -1.00

        # Gordon's node numbering is encoded in tens and ones digits, not 
        # ordered sequentially
        if config['system'] == "gordon":
            x = int(slot/10) - 1    # row
            y = slot % 10 - 1       # column
        else:
            x = 0                   # row
            y = slot - 1            # column

        loadgrid[x, y] = load
        cpugrid[x, y] = cpus

    # don't forget about the final rack
    if last_rack_printed != this_rack and this_rack >= 0 and nodename != "ion":
        draw_rack( loadgrid, cpugrid, this_rack, ax, config )

    ax.autoscale_view()
    ax.invert_yaxis()
#   plt.show()
    plt.savefig('%s-load.png' % config['system'], bbox_inches='tight')
