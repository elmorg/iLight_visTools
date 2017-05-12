# Description: This code enables the playback of iLight data from the Assembly Rooms
# over the course of a selected day.
#   - Lights are shown as circles overlaid on a floor plan
#   - The brightness of each circle is relative to the brightness of the light at that point in time
#   - Hovering over a circle will reveal the percentage brightness

# Written by Evan Morgan, School of Informatics, University of Edinburgh
# Distributed under the MIT Licence - https://opensource.org/licenses/MIT
# Copyright (c) 2016 University of Edinburgh


from __future__ import print_function
from bokeh.io import show, curdoc
from bokeh.models import ColumnDataSource, HoverTool, Circle, Button, Range1d, Plot, Slider, Label,DatePicker
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

# plot parameters
TOOLS = "hover,save"
pWidth = 5375
pHeight = 3519
scaler = 7.874 # scale light positions = PPI/(mm in an inch) = 200/25.4
scale = 6 # scale plot size (smaller = larger)
shiftX = 0
shiftY = 0
period = timedelta(minutes=5)
refreshSpeed = 100
mornCut = 6 # hours to cut off in the morning

# load floor plan image
#url = 'http://groups.inf.ed.ac.uk/enhanced/wordpress/wp-content/uploads/FirstFloorPlan_trimmed_simple_noDoor.png'
url = 'http://groups.inf.ed.ac.uk/enhanced/wordpress/wp-content/uploads/FirstFloorPlan_trimmed_simple_noDoor_inv.png'

# load in required tables
df = pd.read_csv(dir_path + '/Tables/LIGHT_LEVELS.csv', index_col=0, parse_dates=True,dayfirst=True)
light_pos = pd.read_table(dir_path + '/light positions/light_positions.txt')

df = df.asfreq(period) # resample data according to period
periodTs = (totimestamp(df.index[0]+period))-(totimestamp(df.index[0]))

# create a table of all lights with positions specified
for i in light_pos.index:
    if not pd.isnull(light_pos.loc[i,'X']):
        for x, y in zip(light_pos.loc[i,'X'].split(","),light_pos.loc[i,'Y'].split(",")):
            temp = pd.DataFrame({'Area':[str(light_pos.loc[i,'Area'])],
                                 'Channel':[str(light_pos.loc[i,'Channel'])],
                                 'Size':(light_pos.loc[i,'Size'])*8,
                                 'X':int(x)*scaler+shiftX,
                                 'Y':pHeight-(int(y)*scaler+shiftY),
                                 'Colour': ['#FFE900'],
                                 'Name': [str(light_pos.loc[i,'Name'])],
                                 'Level': 0,
                                 'Alpha': 0 })
            if 'lights' in globals():
                lights = pd.concat([lights,temp],axis=0)
            else:
                lights = temp

lights = lights.reset_index(drop=True)
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
plot.circle(x="X", y="Y", source=source, size='Size', color='Colour', line_color= None, fill_alpha="Alpha")

startTime = df.index[0] + timedelta(hours = mornCut)
labelFormat = '%a %b %d     %H:%M'
label = Label(x=50, y=3050, text=startTime.strftime(format = labelFormat), text_font_size='40pt', text_color='#e2e2e2') #b5b5b5
plot.add_layout(label)

datePick = DatePicker(name = "StartD",title = "Date:",max_date = df.index[-1].date(),
                           min_date = df.index[0].date(),value = df.index[0].date(),width = 150)

def updateRange():
    dateVal_start = datePick.value
    dateStr_start = dateVal_start.strftime(format = '%Y-%m-%d'+' '+str(mornCut)+':%M:%S')
    dateVal_end = datePick.value+timedelta(days=1)
    dateStr_end = dateVal_end.strftime(format = '%Y-%m-%d')
    dfT = df.loc[(df.index >=  dateStr_start) & (df.index <=  dateStr_end)]
    return dfT

df2 = updateRange()

def animate_update():
    time = slider.value + periodTs
    if time >= totimestamp(df2.index[-1])-totimestamp(df2.index[0]):
        time = 0
    slider.value = time

def slider_update(attrname, old, new):
    time = slider.value
    label.text = datetime.fromtimestamp(time+totimestamp(df2.index[0])).strftime(labelFormat)
    for a,c in zip(lights['Area'],lights['Channel']):
        lights.loc[(lights['Area']== a) & (lights['Channel'] == c), 'Alpha'] = df2.loc[datetime.fromtimestamp(time+totimestamp(df2.index[0])),a+'.'+c]
    source.data['Alpha'] = list(lights['Alpha']/100)
    source.data['Level'] = list(lights['Alpha'])

slider = Slider(start=0, end=totimestamp(df2.index[-1])-totimestamp(df2.index[0]), value=0, step=periodTs, title="Time (s)")
slider.on_change('value', slider_update)

def animate():
    if button.label == 'Play':
        button.label = 'Pause'
        curdoc().add_periodic_callback(animate_update, refreshSpeed)
    else:
        button.label = 'Play'
        curdoc().remove_periodic_callback(animate_update)

button = Button(label='Play', width=60)
button.on_click(animate)

def dateChange(attrname, old, new):
    global df2
    if button.label == 'Pause':
        button.label = 'Play'
        curdoc().remove_periodic_callback(animate_update)
    df2 = updateRange()
    label.text = datetime.fromtimestamp(totimestamp(df2.index[0])).strftime(labelFormat)
    slider.end = totimestamp(df2.index[-1])-totimestamp(df2.index[0])
    slider.value = 0

datePick.on_change('value',dateChange)

plot.select_one(HoverTool).tooltips = [
    ('Name', '@Name'),
    ('Level', '@Level'+'%'),
]

layout = layout([
    [plot,datePick],
    [slider, button],
])

curdoc().add_root(layout)
