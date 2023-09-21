import requests
import json
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
from bokeh.models import DatetimeTickFormatter,HoverTool
import math


from bokeh.palettes import plasma
from bokeh.plotting import figure, show
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter
from bokeh.io import output_notebook
import math

from bokeh.core.properties import value
from bokeh.io import show, output_file, curdoc
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.transform import dodge
from bokeh.models import SingleIntervalTicker, NumeralTickFormatter,Range1d, LinearAxis
from bokeh.layouts import column
from bokeh.layouts import gridplot
# from bokeh.models.widgets import Tabs, Panel
from bokeh.models import TabPanel
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager

# new headless stuff
from selenium.webdriver.chrome.options import Options

################ REFRESH DATA##################

def getApproved(docketID):
    commentsURL='https://api.regulations.gov/v4/comments?filter[commentOnId]='+docketID+'&api_key=apiKey'
    commentsRes =  requests.get(commentsURL, verify=True)        
    commentsMeta = json.loads(commentsRes.content.decode("utf-8"))
    commentsAgg = json.loads(commentsRes.content.decode("utf-8"))['meta']
    commentsCount = 0
    if commentsAgg:
        commentsCount = commentsAgg['totalElements']
    
    return commentsCount+1

def getSubmitted(docketName):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('---incognito')
    chrome_options.add_argument('---disable-extension')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    browser = webdriver.Chrome(options=chrome_options)
    try:
        browser.get("https://www.regulations.gov/document/"+docketName)
        wait = WebDriverWait(browser,5)
        wait.until(EC.visibility_of_element_located((By.XPATH, '//p[@class="mb-0 js-comments-received"]')))
        element = browser.find_element(By.XPATH, '//p[@class="mb-0 js-comments-received"]').text
    except:
        element = '0'
        

    finally:
        browser.quit()
    return int(element.replace(',',''))

def getStatsString(html, title, submitted, approved, unpublished, downloaded, unscored):
    if html:
        baseString='<p>{0}</p>\n<p>{1:,} submitted</p>\n<p>{2:,} approved</p>\n<p>{3:,} unpublished</p>\n<p>{4:,} downloaded</p>\n<p>{5:,} left to download</p>'
        stringFormatted = baseString.format(title, submitted, approved, unpublished, downloaded, unscored)
    else:
        baseString = '{0}\n{1:,} submitted\n{2:,} approved\n{3:,} unpublished\n{4:,} downloaded\n{5:,} left to download'
        stringFormatted = baseString.format(title, submitted, approved, unpublished, downloaded, unscored )
        
    return stringFormatted

def getDailyChart(df, title):
    print(len(df))
    df['receiveDate_dt'] = pd.to_datetime(df['receiveDate']).apply(lambda x: x.replace(tzinfo=None))
    g = df.groupby(['receiveDate_dt',"sentimentPosition"], as_index = False).size()
    g = g.pivot_table(values='size'
                    , index='receiveDate_dt'
                    , columns='sentimentPosition'
                    , aggfunc='first').reset_index().rename_axis(None, axis=1)#.set_index('receiveDate_dt')
    g.fillna(0, inplace=True)

    #convert datetimes to strings
    g['receiveDate_dt'] = g['receiveDate_dt'].dt.strftime('%Y-%m-%d')
    #convert dataframe to dict
    data = g.to_dict(orient='list')
    dates = g['receiveDate_dt'].tolist()

    source = ColumnDataSource(data=data)


    #get max possible value of plotted columns with some offset
    p = figure( width=chartWidth
               , height=chartHeight
               , x_range=dates
               , y_range=(0, g[['neutral','oppose', 'support']].values.max() + 5000)
               , title=title
               , toolbar_location="left"
               , tools="pan,wheel_zoom,box_zoom,reset")

    p.vbar(x=dodge('receiveDate_dt', -.2, range=p.x_range), top='support', width=0.2, source=source,
           color="#1A71F2", legend_label="support")

    p.vbar(x=dodge('receiveDate_dt',  0,  range=p.x_range), top='oppose', width=0.2, source=source,
           color="#F92518", legend_label="oppose")

    p.vbar(x=dodge('receiveDate_dt',  .2,  range=p.x_range), top='neutral', width=0.2, source=source,
           color="#DEDEDE", legend_label="neutral")

    p.add_tools(HoverTool(tooltips=[("Date","@receiveDate_dt")
                                     , ("Oppose", "@oppose")
                                     , ("Support", "@support")
                                     , ("Neutral", "@neutral")]))
    
    p.xaxis.formatter=DatetimeTickFormatter(
            hours="%I:00 %p",
            days="%m-%d",
            months="%m-%d",
            years="%m-%d"
    )

    p.xaxis.major_label_orientation = math.pi/2
    p.xaxis.major_label_text_color = '#FFFFFF'
    p.yaxis.major_label_text_color = '#FFFFFF'

    p.title.text_color = '#FFFFFF'

    p.xaxis.axis_line_color = '#FFFFFF'
    p.yaxis.axis_line_color = '#FFFFFF'

    p.xaxis.major_tick_line_color = '#FFFFFF'
    p.yaxis.major_tick_line_color = '#FFFFFF'
    p.yaxis.minor_tick_line_color = '#FFFFFF'   

    p.xgrid.grid_line_color = '#333333'
    p.ygrid.grid_line_color = '#5C5B5B'
    p.ygrid.minor_grid_line_color = '#373636'

    p.toolbar.logo = None
    p.border_fill_color = '#191919'
    p.background_fill_color = '#191919'
    p.legend.background_fill_alpha = 0.7

    p.x_range.range_padding = 0.03
    p.xgrid.grid_line_color = None
    p.legend.location = "top_center"
    p.legend.orientation = "horizontal"
    p.yaxis[0].ticker.desired_num_ticks = 10

    return p

def getCumlDailyChart(df, title):
################################cumulative comment by day############################
    df['receiveDate_dt'] = pd.to_datetime(df['receiveDate']).apply(lambda x: x.replace(tzinfo=None))

    g = df.groupby(['receiveDate_dt',"sentimentPosition"], as_index = False).size()
    g = g.pivot_table(values='size'
                        , index='receiveDate_dt'
                        , columns='sentimentPosition'
                        , aggfunc='first').reset_index().rename_axis(None, axis=1)#.set_index('receiveDate_dt')
    g.fillna(0, inplace=True)
    g['receiveDate_dt'] = g['receiveDate_dt'].dt.strftime('%Y-%m-%d')

    g1 = g.set_index('receiveDate_dt').cumsum()
    g1= g1.reset_index()

    #convert dataframe to dict
    data1 = g1.to_dict(orient='list')
    dates1 = g1['receiveDate_dt'].tolist()

    source1 = ColumnDataSource(data=data1)


    #get max possible value of plotted columns with some offset
    p = figure( width=chartWidth
               , height=chartHeight
               , x_range=dates1
               , y_range=(0, g1[['neutral','oppose', 'support']].values.max() + 10000)
               , title=title
               , toolbar_location="left"
               , tools="pan,wheel_zoom,box_zoom,reset")

    p.line('receiveDate_dt', 'support', line_width=2, line_color="#1A71F2", legend_label='support', source=source1)
    p.line('receiveDate_dt', 'oppose', line_width=2, line_color="#F92518", legend_label='oppose', source=source1)
    p.line('receiveDate_dt', 'neutral', line_width=2, line_color="#DEDEDE", legend_label='neutral', source=source1)

    p.add_tools(HoverTool(tooltips=[("Date","@receiveDate_dt")
                                     , ("Oppose", "@oppose")
                                     , ("Support", "@support")
                                     , ("Neutral", "@neutral")
                                     ]
                            )
                 )
    
    p.xaxis.formatter=DatetimeTickFormatter(
            hours="%I:00 %p",
            days="%m-%d",
            months="%m-%d",
            years="%m-%d"
    )

    p.xaxis.major_label_orientation = math.pi/2
    p.xaxis.major_label_text_color = '#FFFFFF'
    p.yaxis.major_label_text_color = '#FFFFFF'

    p.title.text_color = '#FFFFFF'

    p.xaxis.axis_line_color = '#FFFFFF'
    p.yaxis.axis_line_color = '#FFFFFF'

    p.xaxis.major_tick_line_color = '#FFFFFF'
    p.yaxis.major_tick_line_color = '#FFFFFF'
    p.yaxis.minor_tick_line_color = '#FFFFFF'   

    p.xgrid.grid_line_color = '#333333'
    p.ygrid.grid_line_color = '#5C5B5B'
    p.ygrid.minor_grid_line_color = '#373636'

    p.toolbar.logo = None
    p.border_fill_color = '#191919'
    p.background_fill_color = '#191919'
    p.legend.background_fill_alpha = 0.7

    p.x_range.range_padding = 0.03
    p.xgrid.grid_line_color = None
    p.legend.location = "top_center"
    p.legend.orientation = "horizontal"
    p.yaxis[0].ticker.desired_num_ticks = 10
    p.yaxis.formatter=NumeralTickFormatter(format="0")
    return p

def getCommentsAprovedByDay(df, title):
    #####################GENERATE RECEIVERS Approval Rate HTML #########################

    df['postedDate'] = pd.to_datetime(df['postedDate']).apply(lambda x: x.replace(tzinfo=None))
    df['receiveDate'] = pd.to_datetime(df['receiveDate']).apply(lambda x: x.replace(tzinfo=None))
    df['processLagDays'] = (df['postedDate'] - df['receiveDate']).dt.days

    g = df.groupby('postedDate').agg({'comment':'size', 'processLagDays':'mean'})
    g.fillna(0, inplace=True)
    g= g.reset_index()
    #convert datetimes to strings
    g['postedDate'] = g['postedDate'].dt.strftime('%Y-%m-%d')
    #convert dataframe to dict
    data = g.to_dict(orient='list')
    dates = g['postedDate'].tolist()
    source = ColumnDataSource(data=data)


    #get max possible value of plotted columns with some offset
    p= figure( width=chartWidth
               , height=chartHeight
               , x_range=dates
               , y_range=(0, g[['comment']].values.max() + 1000)
               , y_axis_label="Count of Comments Published"
               , title= title
               , toolbar_location="left"
               , tools="pan,wheel_zoom,box_zoom,reset")
    p.extra_y_ranges = {"processLagDays": Range1d(start=0, end=g['processLagDays'].values.max()+1)}
    p.add_layout(LinearAxis(y_range_name="processLagDays",axis_label_text_color='#FFFFFF', axis_label='Avg Days from Sumbit to Publish'), 'right')

    p.vbar(x=dodge('postedDate',  0,  range=p.x_range), top='comment', width=0.2
          , source=source, color="#DEDEDE", legend_label="Count of Comments Published by Day")
    p.line('postedDate'
           , 'processLagDays'
           , line_width=2
           , line_color="#1A71F2"
           , legend_label='Days between Submission and Publication'
           , source=source
           , y_range_name = 'processLagDays'
          )

    p.add_tools(HoverTool(tooltips=[("Posted Date","@postedDate")
                                     ,("Processed", "@comment")
                                     , ("Days of Lag", "@processLagDays")]))
    
    p.xaxis.formatter=DatetimeTickFormatter(
            hours="%I:00 %p",
            days="%m-%d",
            months="%m-%d",
            years="%m-%d"
    )

    p.xaxis.major_label_orientation = math.pi/2
    p.xaxis.major_label_text_color = '#FFFFFF'

    p.title.text_color = '#FFFFFF'

    p.xaxis.axis_line_color = '#FFFFFF'
    p.yaxis.axis_line_color = '#FFFFFF'
    p.yaxis.major_label_text_color = '#FFFFFF'

    p.xaxis.major_tick_line_color = '#FFFFFF'
    p.yaxis.major_tick_line_color = '#FFFFFF'
    p.yaxis.minor_tick_line_color = '#FFFFFF'   
    p.yaxis.axis_label_text_color='#FFFFFF'

    p.xgrid.grid_line_color = '#333333'
    p.ygrid.grid_line_color = '#5C5B5B'
    p.ygrid.minor_grid_line_color = '#373636'

    p.toolbar.logo = None
    p.border_fill_color = '#191919'
    p.background_fill_color = '#191919'
    p.legend.background_fill_alpha = 0.7

    p.x_range.range_padding = 0.03
    p.xgrid.grid_line_color = None
    p.legend.location = "top_center"
    p.legend.orientation = "horizontal"
    p.yaxis[0].ticker.desired_num_ticks = 10
    return p

def getTotals(df, title):
    # sns.set(font_scale=1.4)
    # valuesCountDF =pd.DataFrame(df[['sentimentPosition']].value_counts())
    # total = valuesCountDF['count'].values.sum()
    # valuesCountDF.plot(kind='bar', figsize=(7, 6), rot=0)
    # xlabel="Comments retrieved: \n{:,}"
    # plt.xlabel(xlabel.format(total), labelpad=14)
    # plt.ylabel("Count of Comments", labelpad=14)
    # plt.title(title, y=1.02)
    # return plt
    g = pd.DataFrame(df.groupby(['sentimentPosition'], as_index = False).size())


    columns = g['sentimentPosition']#.to_dict()#(orient='list')
    counts = g['size']/1000#.to_dict()
    colors = ["#DEDEDE","#F92518","#1A71F2"]
    y_top = (g['size'].values.max()+5000)/1000
    source = ColumnDataSource(data=dict(columns=columns, counts=counts, color=colors))
    p = figure(x_range=columns, y_range=(0,y_top), height=500  , width=500, title=title,
            toolbar_location=None, tools="")
    p.vbar(x='columns', top='counts', width=0.9, color='color', legend_field="columns", source=source)
    p.xgrid.grid_line_color = None

    p.add_tools(HoverTool(tooltips=[("Comments","@counts")]))
    
    p.xaxis.major_label_text_color = '#FFFFFF'
    p.yaxis.major_label_text_color = '#FFFFFF'

    p.title.text_color = '#FFFFFF'

    p.xaxis.axis_line_color = '#FFFFFF'
    p.yaxis.axis_line_color = '#FFFFFF'

    p.xaxis.major_tick_line_color = '#FFFFFF'
    p.yaxis.major_tick_line_color = '#FFFFFF'
    p.yaxis.minor_tick_line_color = '#FFFFFF'   

    p.xgrid.grid_line_color = '#333333'
    p.ygrid.grid_line_color = '#5C5B5B'
    p.ygrid.minor_grid_line_color = '#373636'

    p.toolbar.logo = None
    p.border_fill_color = '#191919'
    p.background_fill_color = '#191919'

    p.x_range.range_padding = 0.03
    p.xgrid.grid_line_color = None
    p.yaxis[0].ticker.desired_num_ticks = 10
    # p.legend.background_fill_alpha = 0.7
    p.legend.visible = False
    p.toolbar.visible = False
    p.yaxis.axis_label = "Thousands of Comments"

    return p

def refreshData(apiKey):
    bumpDF = pd.read_csv(r'bumpstock_sentiment.csv', index_col = 'idx', header =0)
    # print('bumpDF:'+ str(len(bumpDF)))

    receiverDF = pd.read_csv(r'receiver_sentiment.csv', index_col='idx', header=0)
    # print('receiverDF: '+ str(len(receiverDF)))

    braceDF = pd.read_csv(r'brace_sentiment.csv', index_col='idx', header=0)
    # print('braceDF: '+ str(len(braceDF)))

    engagedDF = pd.read_csv(r'EngagedInBiz_sentiment.csv', index_col = 'idx', header =0)
    # print('engagedDF:'+ str(len(engagedDF)))

    chartHeight = 700
    chartWidth =1100

    docketName = 'ATF-2018-0002-0001'
    docketID = '0900006483074524'
    bumpCommentsTitle = 'Bump-Stock Type Device Comment Statistics:'
    bumpCommentsDownloaded = len(bumpDF)#engagedDF.index.values.max()
    bumpCommentsSubmitted= 193297 #getSubmitted(docketName)
    bumpCommentsApproved = 95084 #getApproved(docketID)
    bumpCommentsUnpublished = bumpCommentsSubmitted-bumpCommentsApproved
    bumpCommentsUnscored = bumpCommentsApproved-bumpCommentsDownloaded
    bumpStatsFormatted = getStatsString(   
                                           False
                                         , bumpCommentsTitle
                                         , bumpCommentsSubmitted
                                         , bumpCommentsApproved
                                         , bumpCommentsUnpublished
                                         , bumpCommentsDownloaded
                                         , bumpCommentsUnscored
                                        )
    print (bumpStatsFormatted)

    docketName = 'ATF-2021-0001-0001'
    docketID = '0900006485512a37'
    receiverCommentsTitle = 'Definition of Frame or Receiver Statistics:'
    receiverCommentsDownloaded = len(receiverDF)#engagedDF.index.values.max()
    receiverCommentsSubmitted= 294633 #getSubmitted(docketName)
    receiverCommentsApproved = 249299 #getApproved(docketID)
    receiverCommentsUnpublished = receiverCommentsSubmitted-receiverCommentsApproved
    receiverCommentsUnscored = receiverCommentsApproved-receiverCommentsDownloaded
    receiverStatsFormatted = getStatsString( 
                                              False 
                                            , receiverCommentsTitle
                                            , receiverCommentsSubmitted
                                            , receiverCommentsApproved
                                            , receiverCommentsUnpublished
                                            , receiverCommentsDownloaded
                                            , receiverCommentsUnscored
                                         )
    print (receiverStatsFormatted)

    docketName = 'ATF-2021-0002-0001'
    docketID = '0900006484b63c61'
    braceCommentsTitle = 'Factoring Criteria for Firearms with Attached "Stabilizing Braces" Statistics:'
    braceCommentsDownloaded = len(braceDF)#engagedDF.index.values.max()
    braceCommentsSubmitted= 237569 #getSubmitted(docketName)
    braceCommentsApproved = 210614#getApproved(docketID)
    braceCommentsUnpublished = braceCommentsSubmitted-braceCommentsApproved
    braceCommentsUnscored = braceCommentsApproved-braceCommentsDownloaded
    braceStatsFormatted = getStatsString( 
                                              False 
                                            , braceCommentsTitle
                                            , braceCommentsSubmitted
                                            , braceCommentsApproved
                                            , braceCommentsUnpublished
                                            , braceCommentsDownloaded
                                            , braceCommentsUnscored
                                         )
    print (braceStatsFormatted)

    docketName = 'ATF-2023-0002-0001'
    docketID = '0900006485f5bba1'
    engagedCommentsTitle = 'Definition of Engaged in the Business as a Dealer in Firearms Comment Statistics:'
    engagedCommentsDownloaded = len(engagedDF)#engagedDF.index.values.max()
    engagedCommentsSubmitted= getSubmitted(docketName)
    engagedCommentsApproved = getApproved(docketID)
    engagedCommentsUnpublished = engagedCommentsSubmitted-engagedCommentsApproved
    engagedCommentsUnscored = engagedCommentsApproved-engagedCommentsDownloaded
    engagedStatsFormatted = getStatsString( 
                                            True
                                          , engagedCommentsTitle
                                          , engagedCommentsSubmitted
                                          , engagedCommentsApproved
                                          , engagedCommentsUnpublished
                                          , engagedCommentsDownloaded
                                          , engagedCommentsUnscored
                                         )
    print(engagedStatsFormatted)

def getGrid():

    titleBumpTotals = "ATF Docket (ATF-2018-0002)\nBump-Stock Type Device\n"+"Comment Totals"
    pltBumpTotals = getTotals(bumpDF, titleBumpTotals)

    titleReceiverTotals = f"ATF Docket (ATF-2021-0001)\nDefinition of Frame or Receiver and \nIdentification of Firearms\nComment Totals"
    pltReceiverTotals = getTotals(receiverDF, titleReceiverTotals)

    titleBraceTotals = "ATF Docket (ATF-2021-0002)\nFactoring Criteria for\nFirearms with Attached 'Stabilizing Braces'\nComment Totals"
    pltBraceTotals = getTotals(braceDF, titleBraceTotals)

    titleEngagedTotals = "ATF Docket (ATF-2023-0002)\nDefinition of Engaged in the Business \nas a Dealer in Firearms\nComment Totals"
    pltEngagedTotals = getTotals(engagedDF, titleEngagedTotals)

    plots =[[pltEngagedTotals, pltBraceTotals], [pltReceiverTotals, pltBumpTotals]]

    grid = gridplot(plots, width=420, height=400, toolbar_options=dict(logo=None))
    return grid

def getFinalChart():
    # EXPORT BOKEH PLOT########################################

    p1Panel = TabPanel(child=getDailyChart(receiverDF
                                        , "Comment Sentiment by Day on ATF Docket (ATF-2021-0001)\
                                            \nDefinition of Frame or Receiver and Identification of Firearms"),
                                        title= 'Recveiver By Day')
    p2Panel = TabPanel(child=getCumlDailyChart(receiverDF
                                        , "Cumulative Comment Sentiment by Day on ATF Docket (ATF-2021-0001)\
                                            \nDefinition of Frame or Receiver and Identification of Firearms")
                                        , title='Cuml Receiver By Day')
    p3Panel = TabPanel(child=getCommentsAprovedByDay(receiverDF
                                        , "Count of Comments approved by Day on ATF Docket (ATF-2021-0001)\
                                            \nDefinition of Frame or Receiver and Identification of Firearms")
                                        , title='Receiver Approval Lag')

    p4Panel = TabPanel(child=getDailyChart(braceDF
                                        ,"Comment Sentiment by Day on ATF Docket (ATF-2021-0002)\
                                            \nFactoring Criteria for Firearms with Attached 'Stabilizing Braces'" )
                                        , title='Brace By Day')
    p5Panel = TabPanel(child=getCumlDailyChart(braceDF
                                        , "Cumulative Comment Sentiment by Day on ATF Docket (ATF-2021-0002)\
                                            \nFactoring Criteria for Firearms with Attached 'Stabilizing Braces'")
                                        , title='Cuml Brace By Day')
    p6Panel = TabPanel(child=getCommentsAprovedByDay(braceDF
                                        , "Count of Comments approved by Day on ATF Docket (ATF-2021-0002)\
                                            \nFactoring Criteria for Firearms with Attached 'Stabilizing Braces'")
                                        , title='Receiver Approval Lag')

    p7Panel = TabPanel(child=getDailyChart(bumpDF
                                        , "Comment Sentiment by Day on ATF Docket (ATF-2018-0002)\nBump-Stock Type Device")
                                        , title='Bump-stock By Day')
    p8Panel = TabPanel(child=getCumlDailyChart(bumpDF
                                        , "Cumulative Comment Sentiment by Day on ATF Docket (ATF-2018-0002)\nBump-Stock Type Device")
                                        , title='Cuml Bump-stock By Day')
    p9Panel = TabPanel(child=getCommentsAprovedByDay(bumpDF
                                        , "Count of Comments approved by Day on ATF Docket (ATF-2018-0002)\nBump-Stock Type Device'")
                                        , title='Bump-stock Approval Lag')


    p10Panel = TabPanel(child=getDailyChart(engagedDF
                                        ,"Comment Sentiment by Day on ATF Docket (ATF-2023-0002)\
                                            \nDefinition of Engaged in the Business as a Dealer in Firearms" )
                                        , title='Engaged Dealer By Day')
    p11Panel = TabPanel(child=getCumlDailyChart(engagedDF
                                        , "Cumulative Comment Sentiment by Day on ATF Docket (ATF-2023-0002)\
                                            \nDefinition of Engaged in the Business as a Dealer in Firearms") 
                                        , title='Cuml Engaged Dealer By Day')
    p12Panel = TabPanel(child=getCommentsAprovedByDay(engagedDF
                                        , "Count of Comments approved by Day on ATF Docket (ATF-2023-0002)\
                                            \nDefinition of Engaged in the Business as a Dealer in Firearms")
                                        , title='Engaged Dealer Approval Lag')
    p13Panel = TabPanel(child=getGrid(), title='Docket Comments')


    outfilePath = r'PATH'
    output_file(outfilePath, title = 'ATF Shenanigans')

    # Assign the panels to Tabs
    tabs = Tabs(tabs=[
          p13Panel
        , p10Panel
        , p11Panel
        , p12Panel
        , p1Panel
        , p2Panel
        # , p3Panel
        , p4Panel
        , p5Panel
        # , p6Panel
        , p7Panel
        , p8Panel
        # , p9Panel
        ])


    # Show the tabbed layout
    # show(tabs)

    soup = BeautifulSoup(open(outfilePath),'html.parser')
    title = soup.find('title')
    link = soup.new_tag('link')
    link['rel'] = "icon" 
    link['href']="favicon.ico" 
    link['type']="image/x-icon"
    title.insert_after(link)


    extra_html = '''
        <div class="text">
            <p> last updated at: '''+ str(datetime.now())+'''</p>'''+engagedStatsFormatted+'''</div>'''


    soup.body.insert(len(soup.body.contents), BeautifulSoup(extra_html, 'html.parser'))

    with open(outfilePath, "w") as file:
        file.write(str(soup))

    return tabs
