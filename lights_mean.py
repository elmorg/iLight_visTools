# Description: This code enables the visualisation of average light levels  at the Assembly Rooms
# between specified hours (startTime and endTime).
#   - Lights are shown as circles overlaid on a floor plan
#   - The colour of each circle is relative to the average brightness of the light (red > green)

# Written by Evan Morgan, School of Informatics, University of Edinburgh
# Distributed under the MIT Licence - https://opensource.org/licenses/MIT
# Copyright (c) 2016 University of Edinburgh


from __future__ import print_function
from bokeh.io import show, curdoc
from bokeh.models import ColumnDataSource, HoverTool, LinearColorMapper, Circle, Button, Range1d, Plot, Slider, Label,DatePicker
from bokeh.layouts import layout
from bokeh.plotting import figure, output_file
from datetime import datetime, date, timedelta
import time
from bokeh.models.glyphs import ImageURL
from bokeh.resources import INLINE
from bokeh.util.browser import view
import pandas as pd
import numpy as np
import os

def totimestamp(dt):
    return time.mktime(dt.timetuple())

dir_path = os.path.dirname(os.path.realpath(__file__))

colours =  ["#4FFF8A", "#57FA83", "#5FF67C", "#67F176", "#6FED6F", "#77E868",
"#7FE462", "#87DF5B", "#8FDB54", "#97D64E", "#9FD247", "#A7CD40", "#AFC93A",
"#B7C433", "#BFC02C", "#C7BB26", "#CFB71F", "#D7B218", "#DFAE12", "#E7A90B",
"#F0A505", "#F09C06", "#F09308", "#F18B09", "#F1820B", "#F17A0C", "#F2710E",
"#F26910", "#F26011", "#F35813", "#F34F14", "#F44716", "#F43E17", "#F43619",
"#F52D1B", "#F5251C", "#F51C1E", "#F6141F", "#F60B21", "#F70323"]

# plot parameters
TOOLS = "save"
pWidth = 5375
pHeight = 3519
scaler = 7.874 # scale light positions = PPI/(mm in an inch) = 200/25.4
scale = 6 # scale plot size (smaller = larger)
shiftX = 0
shiftY = 0
period = timedelta(minutes=5)
refreshSpeed = 100
mornCut = 6 # hours to cut off in the morning
mapper = LinearColorMapper(palette=colours)
startTime = 0
endTime = 24
# load floor plan image
#url = 'http://groups.inf.ed.ac.uk/enhanced/wordpress/wp-content/uploads/FirstFloorPlan_trimmed_simple_noDoor.png'
url = 'http://groups.inf.ed.ac.uk/enhanced/wordpress/wp-content/uploads/FirstFloorPlan_trimmed_simple_noDoor_inv.png'

# load in required tables
df = pd.read_csv(dir_path + '/Tables/LIGHT_LEVELS.csv', index_col=0, parse_dates=True,dayfirst=True)
light_pos = pd.read_table(dir_path + '/light positions/light_positions.txt')

df = df.asfreq(period) # resample data according to period

df = df.loc[(df.index.hour >  startTime) & (df.index.hour <=  endTime),:]
meanLight = df.mean(axis = 0)
periodTs = (totimestamp(df.index[0]+period))-(totimestamp(df.index[0]))

# create a table of all lights with positions specified
for i in light_pos.index:
    if not pd.isnull(light_pos.loc[i,'X']):
        for x, y in zip(light_pos.loc[i,'X'].split(","),light_pos.loc[i,'Y'].split(",")):
            temp = pd.DataFrame({'Area':[str(light_pos.loc[i,'Area'])],
                                 'Channel':[str(light_pos.loc[i,'Channel'])],
                                 'AreaN':[light_pos.loc[i,'Area']],
                                 'Size':(light_pos.loc[i,'Size'])*8,
                                 'X':int(x)*scaler+shiftX,
                                 'Y':pHeight-(int(y)*scaler+shiftY),
                                 'Colour': ['#FFE900'],
                                 'Name': [str(light_pos.loc[i,'Name'])],
                                 'Level': meanLight.loc[str(light_pos.loc[i,'Area'])+'.'+str(light_pos.loc[i,'Channel'])],
                                 'Alpha': 1 })
            if 'lights' in globals():
                lights = pd.concat([lights,temp],axis=0)
            else:
                lights = temp

lights = lights.reset_index(drop=True)
# select only main areas (not corridors)
lights = lights.loc[lights['AreaN']>9]

source = ColumnDataSource(lights) # convert lights dataframe to datasource

xdr = Range1d(start=0, end=pWidth)
ydr = Range1d(start=0, end=pHeight)

plot = figure(x_range=xdr, y_range=ydr,logo = None,tools=TOOLS)
image1 = ImageURL(url=dict(value=url), x=0, y=0, w= pWidth, h=pHeight,anchor="bottom_left", global_alpha=1)
plot.add_glyph(image1)
plot.plot_height = int(pHeight/scale)
plot.plot_width = int(pWidth/scale)
plot.background_fill_color = "#3b4049"
plot.grid.grid_line_color = None
plot.axis.axis_line_color = None
plot.axis.major_tick_line_color = None
plot.axis.visible = False

# Plot circles for lights
plot.circle(x="X", y="Y", source=source, size='Size', color='#5a5d63', line_color=None) # light off circle #e2e2e2
plot.circle(x="X", y="Y", source=source, size='Size', color={'field': 'Level', 'transform': mapper}, line_color= None, fill_alpha="Alpha")

label = Label(x=100, y=3050, text=str(startTime)+':00 - '+str(endTime)+':00', text_font_size='40pt', text_color='#e2e2e2') #b5b5b5
plot.add_layout(label)

# layout = layout(plot)

# curdoc().add_root(layout)
show(plot)
