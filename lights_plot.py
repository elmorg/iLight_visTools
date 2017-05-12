# Description: This code enables the static visualisation of iLight data from the Assembly Rooms.
#   - Each row represents a light, and columns represent points in time
#   - The brightness of each block represents how bright that light was at that point in time

# Written by Evan Morgan, School of Informatics, University of Edinburgh
# Distributed under the MIT Licence - https://opensource.org/licenses/MIT
# Copyright (c) 2016 University of Edinburgh

from __future__ import print_function
from bokeh.io import show, curdoc
from bokeh.models import ColumnDataSource, HoverTool, LinearColorMapper,CustomJS, Circle, Legend, Button, Range1d, DataRange1d, DatetimeTickFormatter
from bokeh.plotting import figure, output_file
from bokeh.models.widgets import DatePicker, MultiSelect, Paragraph
from bokeh.layouts import column, layout, row, widgetbox
from bokeh.palettes import small_palettes, Viridis256, grey, magma, plasma, inferno, viridis
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import os

# create colour gradient here - https://www.strangeplanet.fr/work/gradient-generator/index.php
gradient =  ["#242424", "#282623", "#2C2922", "#302C22", "#352E21", "#393120",
"#3D3420", "#41371F", "#46391E", "#4A3C1E", "#4E3F1D", "#53411C", "#57441C",
"#5B471B", "#5F4A1A", "#644C1A", "#684F19", "#6C5218", "#715418", "#755717",
"#795A16", "#7D5D16", "#825F15", "#866214", "#8A6514", "#8F6813", "#936A12",
"#976D12", "#9B7011", "#A07210", "#A47510", "#A8780F", "#AC7B0E", "#B17D0E",
"#B5800D", "#B9830C", "#BE850C", "#C2880B", "#C68B0A", "#CA8E0A", "#CF9009",
"#D39308", "#D79608", "#DC9807", "#E09B06", "#E49E06", "#E8A105", "#EDA304",
"#F1A604", "#F5A903", "#FAAC03", "#FAAD07", "#FAAF0B", "#FAB00F", "#FAB214",
"#FAB318", "#FAB51C", "#FAB621", "#FAB825", "#FAB929", "#FBBB2E", "#FBBD32",
"#FBBE36", "#FBC03A", "#FBC13F", "#FBC343", "#FBC447", "#FBC64C", "#FBC750",
"#FBC954", "#FCCB59", "#FCCC5D", "#FCCE61", "#FCCF66", "#FCD16A", "#FCD26E",
"#FCD472", "#FCD577", "#FCD77B", "#FCD87F", "#FDDA84", "#FDDC88", "#FDDD8C",
"#FDDF91", "#FDE095", "#FDE299", "#FDE39E", "#FDE5A2", "#FDE6A6", "#FDE8AA",
"#FEEAAF", "#FEEBB3", "#FEEDB7", "#FEEEBC", "#FEF0C0", "#FEF1C4", "#FEF3C9",
"#FEF4CD", "#FEF6D1", "#FFF8D6"]

def totimestamp(dt, epoch=datetime(1970,1,1)):
    td = dt - epoch
    # return td.total_seconds()
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6

dir_path = os.path.dirname(os.path.realpath(__file__))
plotWidth = 1000
plotHeight = 600
colors = grey(100)
colors = gradient
mapper = LinearColorMapper(palette=colors)
period = timedelta(hours=1)
TOOLS = "hover,save,reset"

df = pd.read_csv(dir_path + '/Tables/LIGHT_LEVELS.csv', index_col=0, parse_dates=True,dayfirst=True)
cn = pd.read_csv(dir_path + '/Tables/channel_names.csv', index_col=0)
an = pd.read_csv(dir_path + '/Tables/area_names.csv', index_col=0)
columnNames = []
for x, y in zip(cn['Area'],cn['Name']) :
    columnNames.append(an.loc[x,'Name']+" - "+y)
df.columns = columnNames
df = df.asfreq(period)
df.index.name ='Time'
df = df.stack() # restructure table
df = df.reset_index()
df.columns = ['Time','Light','Level']


p1 = figure(title="Daily Lighting Use",tools=TOOLS,x_axis_type="datetime",
            y_range=list(reversed(columnNames[0:-6])),x_axis_label='Date',toolbar_location="above")

# configure plot appearance
p1.plot_height = plotHeight
p1.title.text_font_size = "15pt"
p1.plot_width = plotWidth
p1.grid.grid_line_color = None
p1.axis.axis_line_color = None
p1.axis.major_tick_line_color = None
p1.xaxis.axis_line_width = 0
p1.yaxis.axis_line_width = 0
p1.yaxis.major_label_text_font_size = "7pt"
p1.xaxis.major_label_text_font_size = "10pt"
p1.yaxis.major_label_standoff = 0
p1.xaxis.formatter=DatetimeTickFormatter(hourmin=["%R"],days=["%d/%m"],months=["%d/%m"],years=["%d/%m"])
p1.select_one(HoverTool).tooltips = [
    ('Date', '@TLabel'),
    ('Light', '@light'),
    ('Level', '@level'+'%'),
]

# create data
plot_data = ColumnDataSource(data=dict(Time =  df['Time'],
                                       level = df['Level'],
                                       light = df['Light'],
                                       TLabel = df['Time'].map(lambda t: t.strftime(format = '%d/%m %H:%M:%S'))))

# plot rectangles
rectWidth = ((totimestamp(df['Time'][0]+period)*1000)-(totimestamp(df['Time'][0])*1000))*1
p1.rect(x='Time', y='light', width=rectWidth, height=1,source=plot_data,fill_color={'field': 'level', 'transform': mapper},
        line_color={'field': 'level', 'transform': mapper})

# create widgets
datePickStart = DatePicker(name = "StartD",title = "Start Date:",max_date = df['Time'].iloc[-1].date(),
                           min_date = df['Time'][0].date(),value = df['Time'][0].date(),width = 140)

datePickEnd = DatePicker(name = "EndD",title = "End Date:",max_date = df['Time'].iloc[-1].date(),
                         min_date = df['Time'][0].date(),value = df['Time'].iloc[-1].date(),width = 140)
areaList = []
for n in an['Name']:
    areaList.append((n,n))
area_select = MultiSelect(title="Select area:", options=areaList)
channel_select = MultiSelect(title="Select channel:", options=[])
plotDates = Button(label="Plot between start and end dates",button_type="warning")
selectAll = Button(label="Select all lights",button_type="success")

# initialise start and end values for dates
dateVal_start = df['Time'][0].date()
dateVal_end = df['Time'].iloc[-1].date()

def setTitle():
    p1.title.text = "Assembly Rooms Lighting Use: " + dateVal_start.strftime(format = '%d/%m/%y') + \
        " - " + dateVal_end.strftime(format = '%d/%m/%y')

def updateData(dataF): # update current plot data
    plot_data.data = dict(Time =  dataF['Time'],
                          level = dataF['Level'],
                          light = dataF['Light'],
                          TLabel = dataF['Time'].map(lambda t: t.strftime(format = '%d/%m %H:%M:%S')))

def updateDateRange(): # update plot data date range
    global dateVal_start
    global dateVal_end
    dateVal_start = datePickStart.value
    dateStr_start = dateVal_start.strftime(format = '%Y%m%d')
    dateVal_end = datePickEnd.value
    dateStr_end = dateVal_end.strftime(format = '%Y%m%d')
    dfTemp = df.loc[(df['Time'] >=  dateStr_start) & (df['Time'] <=  dateStr_end)]
    setTitle()
    return dfTemp

def dateChange(): # change the dates
    df2 = updateDateRange()
    updateData(df2)
    #p1.set(x_range = Range1d(totimestamp(df2['Time'][0])*1000, totimestamp(df2['Time'].iloc[-1])*1000))

def areaChange(attrname, old, new): # callback function for selection of areas
    areas=[]
    for l in new:
        areas.append(l.encode('UTF8'))
    df2 = updateDateRange()
    lightNames = []
    chanList = []
    for a in areas :
        areaChans =  cn.loc[cn['Area'].isin(an.index[an['Name'] == a]),'Name']
        for c in areaChans:
            lightNames.append(a+" - "+c)
            chanList.append((a+" - "+c,c))
    channel_select.options = chanList
    channel_select.value = lightNames

def channelChange(attrname, old, new): # callback function for selection of channels
    chans=[]
    for l in new:
        chans.append(l.encode('UTF8'))
    df2 = updateDateRange()
    df2 = df2[df2['Light'].isin(chans)]
    updateData(df2)
    p1.y_range.factors=list(reversed(chans))

def allLights(): # callback function for all lights button
    area_select.value = list(an['Name'])

# configure actions for widgets
plotDates.on_click(dateChange)
selectAll.on_click(allLights)
area_select.on_change('value',areaChange)
channel_select.on_change('value',channelChange)
setTitle()

p = Paragraph(text="""""",
width=200, height=10)

l = layout([[p1,column(widgetbox(p),selectAll,area_select,channel_select,row(datePickStart,datePickEnd,height=240),plotDates)]])

curdoc().add_root(l)
