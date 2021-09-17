import pandas as pd
from wordcloud import WordCloud
import re
from time import time
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from dateutil.parser import parse
import numpy as np

from bokeh.palettes import plasma
from bokeh.plotting import figure, show
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter
import math


from bokeh.palettes import plasma
from bokeh.plotting import figure, show
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter
import math

from bokeh.core.properties import value
from bokeh.io import show, output_file, curdoc
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.transform import dodge
from bokeh.models import SingleIntervalTicker, NumeralTickFormatter,Range1d, LinearAxis
from bokeh.layouts import column
from bokeh.models.widgets import Tabs, Panel

receiverDF = pd.read_csv(r'receiver_sentiment.csv', index_col='idx', header=0)
braceDF = pd.read_csv(r'brace_sentiment.csv', index_col='idx', header=0)

def getP1():
    #####################GENERATE RECEIVERS BY DAY #########################
    print(len(receiverDF))
    g1 = receiverDF.groupby(['receiveDate_dt',"sentimentPosition"], as_index = False).size()
    g1 = g1.pivot_table(values='size'
                        , index='receiveDate_dt'
                        , columns='sentimentPosition'
                        , aggfunc='first').reset_index().rename_axis(None, axis=1)#.set_index('receiveDate_dt')
    g1.fillna(0, inplace=True)
    g1['total']=g1.sum(axis=1)

    #convert datetimes to strings
    g1['receiveDate_dt'] = g1['receiveDate_dt'].dt.strftime('%Y-%m-%d')
    #convert dataframe to dict
    data1 = g1.to_dict(orient='list')
    dates1 = g1['receiveDate_dt'].tolist()

    def getds():
        source = ColumnDataSource(data=data1)
        return source

    #get max possible value of plotted columns with some offset
    p1 = figure( width=1200
               , height=800
               , x_range=dates1
               , y_range=(0, g1[['neutral','oppose', 'support']].values.max() + 1000)
               , title="Comment Sentiment by Day on ATF Docket (ATF-2021-0001)\nDefinition of Frame or Receiver and Identification of Firearms"
               , toolbar_location=None
               , tools="")
    p1.vbar(x=dodge('receiveDate_dt', -.2, range=p1.x_range), top='support', width=0.2, source=getds(),
           color="#1A71F2", legend_label="support")
    p1.vbar(x=dodge('receiveDate_dt',  0,  range=p1.x_range), top='oppose', width=0.2, source=getds(),
           color="#F92518", legend_label="oppose")

    p1.vbar(x=dodge('receiveDate_dt',  .2,  range=p1.x_range), top='neutral', width=0.2, source=getds(),
           color="#DEDEDE", legend_label="neutral")
    p1.xaxis.formatter=DatetimeTickFormatter(
        hours=["%I:00 %p"],
        days=["%m-%d"],
        months=["%m-%d"],
        years=["%m-%d"]
    )
    p1.xaxis.major_label_orientation = math.pi/2
    p1.xaxis.major_label_text_color = '#FFFFFF'
    p1.yaxis.major_label_text_color = '#FFFFFF'

    p1.title.text_color = '#FFFFFF'

    p1.xaxis.axis_line_color = '#FFFFFF'
    p1.yaxis.axis_line_color = '#FFFFFF'

    p1.xaxis.major_tick_line_color = '#FFFFFF'
    p1.yaxis.major_tick_line_color = '#FFFFFF'
    p1.yaxis.minor_tick_line_color = '#FFFFFF'   

    p1.xgrid.grid_line_color = '#333333'
    p1.ygrid.grid_line_color = '#5C5B5B'
    p1.ygrid.minor_grid_line_color = '#373636'

    p1.toolbar.logo = None
    p1.border_fill_color = '#191919'
    p1.background_fill_color = '#191919'
    p1.legend.background_fill_alpha = 0.7

    p1.x_range.range_padding = 0.03
    p1.xgrid.grid_line_color = None
    p1.legend.location = "top_center"
    p1.legend.orientation = "horizontal"
    p1.yaxis[0].ticker.desired_num_ticks = 10
    return p1

def getP2():
    ################################cumulative comment by day############################
    g1 = receiverDF.groupby(['receiveDate_dt',"sentimentPosition"], as_index = False).size()
    g1 = g1.pivot_table(values='size'
                        , index='receiveDate_dt'
                        , columns='sentimentPosition'
                        , aggfunc='first').reset_index().rename_axis(None, axis=1)#.set_index('receiveDate_dt')
    g1.fillna(0, inplace=True)
    g1['total']=g1.sum(axis=1)
    g1['receiveDate_dt'] = g1['receiveDate_dt'].dt.strftime('%Y-%m-%d')
    
    g2 = g1.set_index('receiveDate_dt').cumsum()
    g2= g2.reset_index()
    #convert dataframe to dict
    data2 = g2.to_dict(orient='list')
    dates2 = g2['receiveDate_dt'].tolist()

    source2 = ColumnDataSource(data=data2)
    #get max possible value of plotted columns with some offset
    p2 = figure( width=1200
               , height=800
               , x_range=dates2
               , y_range=(0, g2[['neutral','oppose', 'support']].values.max() + 10000)
               , title="Cumulative Comment Sentiment by Day on ATF Docket (ATF-2021-0001)\nDefinition of Frame or Receiver and Identification of Firearms"
               , toolbar_location=None
               , tools="")

    p2.line('receiveDate_dt', 'support', line_width=2, line_color="#1A71F2", legend_label='support', source=source2)
    p2.line('receiveDate_dt', 'oppose', line_width=2, line_color="#F92518", legend_label='oppose', source=source2)
    p2.line('receiveDate_dt', 'neutral', line_width=2, line_color="#DEDEDE", legend_label='neutral', source=source2)

    p2.xaxis.formatter=DatetimeTickFormatter(
            hours=["%I:00 %p"],
            days=["%m-%d"],
            months=["%m-%d"],
            years=["%m-%d"]
    )
    p2.xaxis.major_label_orientation = math.pi/2
    p2.xaxis.major_label_text_color = '#FFFFFF'
    p2.yaxis.major_label_text_color = '#FFFFFF'

    p2.title.text_color = '#FFFFFF'

    p2.xaxis.axis_line_color = '#FFFFFF'
    p2.yaxis.axis_line_color = '#FFFFFF'

    p2.xaxis.major_tick_line_color = '#FFFFFF'
    p2.yaxis.major_tick_line_color = '#FFFFFF'
    p2.yaxis.minor_tick_line_color = '#FFFFFF'   

    p2.xgrid.grid_line_color = '#333333'
    p2.ygrid.grid_line_color = '#5C5B5B'
    p2.ygrid.minor_grid_line_color = '#373636'

    p2.toolbar.logo = None
    p2.border_fill_color = '#191919'
    p2.background_fill_color = '#191919'
    p2.legend.background_fill_alpha = 0.7

    p2.x_range.range_padding = 0.03
    p2.xgrid.grid_line_color = None
    p2.legend.location = "top_center"
    p2.legend.orientation = "horizontal"
    p2.yaxis[0].ticker.desired_num_ticks = 10
    p2.yaxis.formatter=NumeralTickFormatter(format="0")
    return p2

def getP3():
    #####################GENERATE RECEIVERS Approval Rate HTML #########################
    receiverDF['postedDate_dt'] = pd.to_datetime(receiverDF['postedDate']).apply(lambda x: x.replace(tzinfo=None))
    receiverDF['receiveDate_dt'] = pd.to_datetime(receiverDF['receiveDate']).apply(lambda x: x.replace(tzinfo=None))
    receiverDF['processLagDays'] = (receiverDF['postedDate_dt'] - receiverDF['receiveDate_dt']).dt.days

    g3 = receiverDF.groupby('postedDate_dt').agg({'comment':'size', 'processLagDays':'mean'})
    g3.fillna(0, inplace=True)
    g3= g3.reset_index()
    #convert datetimes to strings
    g3['postedDate_dt'] = g3['postedDate_dt'].dt.strftime('%Y-%m-%d')
    #convert dataframe to dict
    data3 = g3.to_dict(orient='list')
    dates3 = g3['postedDate_dt'].tolist()
    source3 = ColumnDataSource(data=data3)
    #get max possible value of plotted columns with some offset
    p3= figure( width=1200
               , height=800
    #            , x_axis_type="datetime"
               , x_range=dates3
               , y_range=(0, g3[['comment']].values.max() + 1000)
               , y_axis_label="Count of Comments Published"
               , title="Count of Comments approved by Day on ATF Docket (ATF-2021-0001)\nDefinition of Frame or Receiver and Identification of Firearms"
               , toolbar_location=None
               , tools="")
    p3.extra_y_ranges = {"processLagDays": Range1d(start=0, end=g3['processLagDays'].values.max()+1)}
    p3.add_layout(LinearAxis(y_range_name="processLagDays",axis_label_text_color='#FFFFFF', axis_label='Days between Submission and Publication'), 'right')

    p3.vbar(x=dodge('postedDate_dt',  0,  range=p3.x_range), top='comment', width=0.2
            , source=source3, color="#DEDEDE", legend_label="Count of Comments Published by Day")
    p3.line('postedDate_dt'
           , 'processLagDays'
           , line_width=2
           , line_color="#1A71F2"
           , legend_label='Days between Submission and Publication'
           , source=source3
           , y_range_name = 'processLagDays'
          )

    p3.xaxis.formatter=DatetimeTickFormatter(
            hours=["%I:00 %p"],
            days=["%m-%d"],
            months=["%m-%d"],
            years=["%m-%d"]
    )
    p3.xaxis.major_label_orientation = math.pi/2
    p3.xaxis.major_label_text_color = '#FFFFFF'

    p3.title.text_color = '#FFFFFF'

    p3.xaxis.axis_line_color = '#FFFFFF'
    p3.yaxis.axis_line_color = '#FFFFFF'
    p3.yaxis.major_label_text_color = '#FFFFFF'

    p3.xaxis.major_tick_line_color = '#FFFFFF'
    p3.yaxis.major_tick_line_color = '#FFFFFF'
    p3.yaxis.minor_tick_line_color = '#FFFFFF'   
    p3.yaxis.axis_label_text_color='#FFFFFF'

    p3.xgrid.grid_line_color = '#333333'
    p3.ygrid.grid_line_color = '#5C5B5B'
    p3.ygrid.minor_grid_line_color = '#373636'

    p3.toolbar.logo = None
    p3.border_fill_color = '#191919'
    p3.background_fill_color = '#191919'
    p3.legend.background_fill_alpha = 0.7

    p3.x_range.range_padding = 0.03
    p3.xgrid.grid_line_color = None
    p3.legend.location = "top_center"
    p3.legend.orientation = "horizontal"
    p3.yaxis[0].ticker.desired_num_ticks = 10
    return p3

def getP4():
    braceDF['receiveDate_dt'] = pd.to_datetime(braceDF['receiveDate']).apply(lambda x: x.replace(tzinfo=None))
    g4 = braceDF.groupby(['receiveDate_dt',"sentimentPosition"], as_index = False).size()
    g4 = g4.pivot_table(values='size'
                        , index='receiveDate_dt'
                        , columns='sentimentPosition'
                        , aggfunc='first').reset_index().rename_axis(None, axis=1)#.set_index('receiveDate_dt')
    g4.fillna(0, inplace=True)
    # display(g4)

    #convert datetimes to strings
    g4['receiveDate_dt'] = g4['receiveDate_dt'].dt.strftime('%Y-%m-%d')
    #convert dataframe to dict
    data4 = g4.to_dict(orient='list')
    dates4 = g4['receiveDate_dt'].tolist()

#     output_file(r'viz\\BraceSentimentByDay.html')

    source4 = ColumnDataSource(data=data4)
    p4 = figure( width=1200
               , height=800
               , x_range=dates4
               , y_range=(0, g4[['neutral','oppose', 'support']].values.max() + 1000)
               , title="Comment Sentiment by Day on ATF Docket (ATF-2021-0002)\nFactoring Criteria for Firearms with Attached 'Stabilizing Braces'"
               , toolbar_location=None
               , tools="")

    p4.vbar(x=dodge('receiveDate_dt', -.2, range=p4.x_range), top='support', width=0.2, source=source4,
           color="#1A71F2", legend_label="support")

    p4.vbar(x=dodge('receiveDate_dt',  0,  range=p4.x_range), top='oppose', width=0.2, source=source4,
           color="#F92518", legend_label="oppose")

    p4.vbar(x=dodge('receiveDate_dt',  .2,  range=p4.x_range), top='neutral', width=0.2, source=source4,
           color="#DEDEDE", legend_label="neutral")


    p4.xaxis.formatter=DatetimeTickFormatter(
            hours=["%I:00 %p"],
            days=["%m-%d"],
            months=["%m-%d"],
            years=["%m-%d"]
    )
    p4.xaxis.major_label_orientation = math.pi/2
    p4.xaxis.major_label_text_color = '#FFFFFF'
    p4.yaxis.major_label_text_color = '#FFFFFF'

    p4.title.text_color = '#FFFFFF'

    p4.xaxis.axis_line_color = '#FFFFFF'
    p4.yaxis.axis_line_color = '#FFFFFF'

    p4.xaxis.major_tick_line_color = '#FFFFFF'
    p4.yaxis.major_tick_line_color = '#FFFFFF'
    p4.yaxis.minor_tick_line_color = '#FFFFFF'   

    p4.xgrid.grid_line_color = '#333333'
    p4.ygrid.grid_line_color = '#5C5B5B'
    p4.ygrid.minor_grid_line_color = '#373636'

    p4.toolbar.logo = None
    p4.border_fill_color = '#191919'
    p4.background_fill_color = '#191919'
    p4.legend.background_fill_alpha = 0.7

    p4.x_range.range_padding = 0.03
    p4.xgrid.grid_line_color = None
    p4.legend.location = "top_center"
    p4.legend.orientation = "horizontal"
    p4.yaxis[0].ticker.desired_num_ticks = 10
    return p4

def getP5():
    ################################ BRACE cumulative comment by day############################
    g4 = braceDF.groupby(['receiveDate_dt',"sentimentPosition"], as_index = False).size()
    g4 = g4.pivot_table(values='size'
                        , index='receiveDate_dt'
                        , columns='sentimentPosition'
                        , aggfunc='first').reset_index().rename_axis(None, axis=1)
    g4.fillna(0, inplace=True)
    g4['receiveDate_dt'] = g4['receiveDate_dt'].dt.strftime('%Y-%m-%d')
    g5 = g4.set_index('receiveDate_dt').cumsum()
    g5= g5.reset_index()
    #convert dataframe to dict
    data5 = g5.to_dict(orient='list')
    dates5 = g5['receiveDate_dt'].tolist()
    source5 = ColumnDataSource(data=data5)
    #get max possible value of plotted columns with some offset
    p5 = figure( width=1200
               , height=800
               , x_range=dates5
               , y_range=(0, g5[['neutral','oppose', 'support']].values.max() + 10000)
               , title="Cumulative Comment Sentiment by Day on ATF Docket (ATF-2021-0002)\nFactoring Criteria for Firearms with Attached 'Stabilizing Braces'"
               , toolbar_location=None
               , tools="")

    p5.line('receiveDate_dt', 'support', line_width=2, line_color="#1A71F2", legend_label='support', source=source5)
    p5.line('receiveDate_dt', 'oppose', line_width=2, line_color="#F92518", legend_label='oppose', source=source5)
    p5.line('receiveDate_dt', 'neutral', line_width=2, line_color="#DEDEDE", legend_label='neutral', source=source5)

    p5.xaxis.formatter=DatetimeTickFormatter(
            hours=["%I:00 %p"],
            days=["%m-%d"],
            months=["%m-%d"],
            years=["%m-%d"]
    )
    p5.xaxis.major_label_orientation = math.pi/2
    p5.xaxis.major_label_text_color = '#FFFFFF'
    p5.yaxis.major_label_text_color = '#FFFFFF'

    p5.title.text_color = '#FFFFFF'

    p5.xaxis.axis_line_color = '#FFFFFF'
    p5.yaxis.axis_line_color = '#FFFFFF'

    p5.xaxis.major_tick_line_color = '#FFFFFF'
    p5.yaxis.major_tick_line_color = '#FFFFFF'
    p5.yaxis.minor_tick_line_color = '#FFFFFF'   

    p5.xgrid.grid_line_color = '#333333'
    p5.ygrid.grid_line_color = '#5C5B5B'
    p5.ygrid.minor_grid_line_color = '#373636'

    p5.toolbar.logo = None
    p5.border_fill_color = '#191919'
    p5.background_fill_color = '#191919'
    p5.legend.background_fill_alpha = 0.7

    p5.x_range.range_padding = 0.03
    p5.xgrid.grid_line_color = None
    p5.legend.location = "top_center"
    p5.legend.orientation = "horizontal"
    p5.yaxis[0].ticker.desired_num_ticks = 10
    p5.yaxis.formatter=NumeralTickFormatter(format="0")
    return p5

def getP6():
    #####################GENERATE RECEIVERS Approval Rate HTML #########################
    braceDF['postedDate_dt'] = pd.to_datetime(braceDF['postedDate']).apply(lambda x: x.replace(tzinfo=None))
    braceDF['receiveDate_dt'] = pd.to_datetime(braceDF['receiveDate']).apply(lambda x: x.replace(tzinfo=None))
    braceDF['processLagDays'] = (braceDF['postedDate_dt'] - braceDF['receiveDate_dt']).dt.days
    g6 = braceDF.groupby('postedDate_dt').agg({'comment':'size', 'processLagDays':'mean'})
    g6.fillna(0, inplace=True)
    g6= g6.reset_index()
    #convert datetimes to strings
    g6['postedDate_dt'] = g6['postedDate_dt'].dt.strftime('%Y-%m-%d')
    #convert dataframe to dict
    data6 = g6.to_dict(orient='list')
    dates6 = g6['postedDate_dt'].tolist()
    source6 = ColumnDataSource(data=data6)
    #get max possible value of plotted columns with some offset
    p6 = figure( width=1200
               , height=800
               , x_range=dates6
               , y_range=(0, g6[['comment']].values.max() + 1000)
               , y_axis_label="Count of Comments Published"
               , title="Count of Comments approved by Day on ATF Docket (ATF-2021-0002)\nFactoring Criteria for Firearms with Attached 'Stabilizing Braces'"
               , toolbar_location=None
               , tools="")
    p6.extra_y_ranges = {"processLagDays": Range1d(start=0, end=g6['processLagDays'].values.max()+1)}
    p6.add_layout(LinearAxis(y_range_name="processLagDays",axis_label_text_color='#FFFFFF', axis_label='Days between Submission and Publication'), 'right')

    p6.vbar(x=dodge('postedDate_dt',  0,  range=p6.x_range), top='comment', width=0.2, source=source6,
           color="#DEDEDE", legend_label="Count of Comments Published by Day")
    p6.line('postedDate_dt'
           , 'processLagDays'
           , line_width=2
           , line_color="#1A71F2"
           , legend_label='Days between Submission and Publication'
           , source=source6
           , y_range_name = 'processLagDays'
          )

    p6.xaxis.formatter=DatetimeTickFormatter(
            hours=["%I:00 %p"],
            days=["%m-%d"],
            months=["%m-%d"],
            years=["%m-%d"]
    )
    p6.xaxis.major_label_orientation = math.pi/2
    p6.xaxis.major_label_text_color = '#FFFFFF'

    p6.title.text_color = '#FFFFFF'

    p6.xaxis.axis_line_color = '#FFFFFF'
    p6.yaxis.axis_line_color = '#FFFFFF'
    p6.yaxis.major_label_text_color = '#FFFFFF'

    p6.xaxis.major_tick_line_color = '#FFFFFF'
    p6.yaxis.major_tick_line_color = '#FFFFFF'
    p6.yaxis.minor_tick_line_color = '#FFFFFF'   
    p6.yaxis.axis_label_text_color='#FFFFFF'

    p6.xgrid.grid_line_color = '#333333'
    p6.ygrid.grid_line_color = '#5C5B5B'
    p6.ygrid.minor_grid_line_color = '#373636'

    p6.toolbar.logo = None
    p6.border_fill_color = '#191919'
    p6.background_fill_color = '#191919'
    p6.legend.background_fill_alpha = 0.7

    p6.x_range.range_padding = 0.03
    p6.xgrid.grid_line_color = None
    p6.legend.location = "top_center"
    p6.legend.orientation = "horizontal"
    p6.yaxis[0].ticker.desired_num_ticks = 10
    return p6

def getChart():
    p1Panel = Panel(child=getP1(), title='Receiver By Day')
    p2Panel = Panel(child=getP2(), title='Cuml Receiver By Day')
    p3Panel = Panel(child=getP3(), title='Receiver Comments Processed By Day')
    p4Panel = Panel(child=getP4(), title='Brace By Day')
    p5Panel = Panel(child=getP5(), title='Cuml Brace By Day')
    p6Panel = Panel(child=getP6(), title='Brace Comments Processed By Day')
    tabs = Tabs(tabs=[p1Panel,p2Panel, p3Panel, p4Panel, p5Panel, p6Panel])
    return tabs