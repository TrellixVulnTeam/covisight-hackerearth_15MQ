from users.models import profiledetails
from home.models import Notification
import os
import re
from folium.plugins import MarkerCluster
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
import datetime
import json
import numpy as np
import requests
from copy import deepcopy
import pandas as pd
import folium
from datetime import date
from datetime import timedelta
import plotly.graph_objects as go

val = None
val1 = None
val2 = None

# Create your views here.
def cowin(request):
    url12 = None
    if request.user.is_authenticated:
        url12 = request.user.first_name

    if request.method == 'POST':
        dist_inp = request.POST.get('mySelect')
        url = 'https://raw.githubusercontent.com/bhattbhavesh91/cowin-vaccination-slot-availability/main/district_mapping.csv'
        df = pd.read_csv(url, index_col=0)
        df1 = pd.read_csv(url, index_col=0)
        mapping_dict = pd.Series(df["district id"].values,
                                 index=df["district name"].values).to_dict()
        DIST_ID = mapping_dict[dist_inp]
        base = datetime.datetime.today()
        date_list = [base]
        date_str = [x.strftime("%d-%m-%Y") for x in date_list]
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
        final_df = None
        for INP_DATE in date_str:
            URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(
                DIST_ID, INP_DATE)
            # response = requests.get(URL, headers=header)
            response = requests.get(URL)
            if (response.ok) and ('centers' in json.loads(response.text)):
                resp_json = json.loads(response.text)['centers']
                if resp_json is not None:
                    df = pd.DataFrame(resp_json)
                    if len(df):
                        df = df.explode("sessions")
                        df['min_age_limit'] = df.sessions.apply(lambda x: x['min_age_limit'])
                        df['vaccine'] = df.sessions.apply(lambda x: x['vaccine'])
                        df['available_capacity'] = df.sessions.apply(lambda x: x['available_capacity'])
                        df['date'] = df.sessions.apply(lambda x: x['date'])
                        df = df[
                            ["date", "available_capacity", "vaccine", "min_age_limit", "pincode", "name", "state_name",
                             "district_name", "block_name", "fee_type"]]
                        if final_df is not None:
                            final_df = pd.concat([final_df, df])
                        else:
                            final_df = deepcopy(df)
                else:
                    print("No rows in the data Extracted from the API")

        vaccine = list(final_df.loc[:, "vaccine"].unique())
        pincode = list(final_df.loc[:, "pincode"].unique())
        min_age_limit = list(final_df.loc[:, "min_age_limit"].unique())
        min_age_limit.sort()
        unique_districts = list(df1["district name"].unique())
        unique_districts.sort()
        valid_payments = list(final_df.loc[:, "fee_type"].unique())
        valid_capacity = ["Available"]
        global val

        def val():
            return final_df

        context = {
            'select_districts': unique_districts,
            'vaccine': vaccine,
            'pay': valid_payments,
            'min_age_limit': min_age_limit,
            'pincode': pincode,
            'valid_capacity': valid_capacity,
            'final': final_df,
            'proimage': url12,
        }
        return render(request, 'cowinmo.html', context)
    url = 'media/district_mapping.csv'
    df = pd.read_csv(url, index_col=0)
    unique_districts = list(df["district name"].unique())
    unique_districts.sort()

    context = {
        'select_districts': unique_districts,
        'notification': Notification.objects.filter(receiver=request.user.username),
        'proimage': url12,
        'pagetitle': 'Vaccine Info',
    }
    return render(request, 'cowinmo.html', context)


def cowintable(request):
    if request.POST.get('action') != 'post':
        return
    rename_mapping = {
        'date': 'Date',
        'min_age_limit': 'Age Limit',
        'available_capacity': 'Doses Left',
        'vaccine': 'Vaccine',
        'pincode': 'Pincode',
        'name': 'Hospital Name',
        'state_name': 'State',
        'district_name': 'District',
        'block_name': 'Block Name',
        'fee_type': 'Fees'
    }
    try:
        return _extracted_from_cowintable_16(rename_mapping, request)
    except:
        response = {
            'a': 'True',
        }
        return JsonResponse(response)


def _extracted_from_cowintable_16(rename_mapping, request):
    ok1 = val()
    ok = ok1.copy(deep=True)
    ok.rename(columns=rename_mapping, inplace=True)
    abc = 0
    pincode = request.POST.get('pincode')
    minage = request.POST.get('minage')
    pay = request.POST.get('pay')
    available = request.POST.get('available')
    if pincode in ['Show All', 'empty']:
        abc = ok
    else:
        pincode = int(pincode)
        abc = deepcopy(ok.loc[ok['Pincode'] == pincode])
    if minage in ['Show All', 'empty']:
        abc = abc
    else:
        minage = int(minage)
        abc = deepcopy(abc.loc[abc['Age Limit'] == minage])
    if available in ['Show All', 'empty']:
        abc = abc
    else:
        abc = deepcopy(abc.loc[abc['Doses Left'] > 0])
    if pay in ['Show All', 'empty']:
        abc = abc
    else:
        abc = deepcopy(abc.loc[abc['Fees'] == pay])

    df = re.sub(' mystyle', '" id="example', abc.to_html(classes='mystyle'))
    response = {
        'table1': df,
    }
    return JsonResponse(response)


def covidanalysis(request):
    url = None
    if request.user.is_authenticated:
        url = request.user.first_name
    context = {
        'proimage': url,
        'pagetitle': 'Screening Test',
    }
    return render(request, 'covidquestionare.html', context)


def vaccinechart(request):
    url12 = None
    if request.user.is_authenticated:
        url12 = request.user.first_name
    
    districtwisereading = pd.read_csv('http://api.covid19india.org/csv/latest/cowin_vaccine_data_districtwise.csv', sep=',',
                     error_bad_lines=False, index_col=False, dtype='unicode')
    
    global val2
    def val2():
        return districtwisereading
    print('working or not')
    
    today = date.today()
    # a = today.strftime("%d_%m_%Y") + '.csv'
    # b = os.path.exists('media/' + a)
    # if not b:
    #     req = requests.get('http://api.covid19india.org/csv/latest/cowin_vaccine_data_statewise.csv')
    #     url_content = req.content
    #     csv_file = open('media/' + a, 'wb')
    #     csv_file.write(url_content)
    #     csv_file.close()
    # vaccinestate = pd.read_csv('media/' + a)
    vaccinestate = pd.read_csv('http://api.covid19india.org/csv/latest/cowin_vaccine_data_statewise.csv')
    vaccinestate.columns = [col.replace("Updated On", "Date") for col in vaccinestate.columns]
    vaccinestate.columns = [col.replace("Total Doses Administered", "Doses") for col in vaccinestate.columns]
    vaccinestate.columns = [col.replace("First Dose Administered", "fDoses") for col in vaccinestate.columns]
    vaccinestate.columns = [col.replace("Second Dose Administered", "sDoses") for col in vaccinestate.columns]
    vaccinestate.columns = [col.replace(" Covaxin (Doses Administered)", "Covaxin") for col in vaccinestate.columns]
    vaccinestate.columns = [col.replace("CoviShield (Doses Administered)", "CoviShield") for col in vaccinestate.columns]
    vaccinestate.columns = [col.replace("Sputnik V (Doses Administered)", "Sputnik") for col in vaccinestate.columns]
    # vaccinestate.columns = [col.replace("Total Covaxin Administered", "Covaxin") for col in vaccinestate.columns]
    # vaccinestate.columns = [col.replace("Total CoviShield Administered", "CoviShield") for col in vaccinestate.columns]
    # vaccinestate.columns = [col.replace("Total Sputnik V Administered", "Sputnik") for col in vaccinestate.columns]
    # vaccinestate.columns = [col.replace("Male(Individuals Vaccinated)", "Male") for col in vaccinestate.columns]
    # vaccinestate.columns = [col.replace("Female(Individuals Vaccinated)", "Female") for col in vaccinestate.columns]
    # vaccinestate.columns = [col.replace("Transgender(Individuals Vaccinated)", "Transgender") for col in vaccinestate.columns]
    # vaccinestate.columns = [col.replace("Male (Doses Administered)", "Male") for col in vaccinestate.columns]
    # vaccinestate.columns = [col.replace("Female (Doses Administered)", "Female") for col in vaccinestate.columns]
    # vaccinestate.columns = [col.replace("Transgender (Doses Administered)", "Transgender") for col in vaccinestate.columns]
    vaccinestate.columns = [col.replace("Male(Individuals Vaccinated)", "Male") for col in vaccinestate.columns]
    vaccinestate.columns = [col.replace("Female(Individuals Vaccinated)", "Female") for col in vaccinestate.columns]
    vaccinestate.columns = [col.replace("Transgender(Individuals Vaccinated)", "Transgender") for col in vaccinestate.columns]
    vaccinestate.columns = [col.replace("Total Individuals Vaccinated", "Totalindiviual") for col in vaccinestate.columns]
    vaccinestate.dropna(subset=["Doses"], inplace=True)
    vaccinestate.dropna(subset=["fDoses"], inplace=True)
    vaccinestate.dropna(subset=["sDoses"], inplace=True)
    vaccinestate.dropna(subset=["Covaxin"], inplace=True)
    vaccinestate.dropna(subset=["CoviShield"], inplace=True)
    
    df = vaccinestate.copy()
    df1 = vaccinestate.copy()
    df2 = vaccinestate.copy()
    df3 = vaccinestate.copy()
    coordinates = pd.read_csv("media/state.csv")
    
    # today = date.today()
    # yesterday = today - timedelta(days=2)
    # a = yesterday.strftime("%d/%m/%Y")
    last_element = vaccinestate.iloc[-1]
    abc = vaccinestate.loc[vaccinestate['Date'] == last_element.Date]
    # abc = vaccinestate.loc[vaccinestate["Date"] == a]
    covid = abc.join(coordinates.set_index('State'), on='State')
    covid.dropna(subset=["Longitude"], inplace=True)
    covid.dropna(subset=["Latitude"], inplace=True)
    # zoom_control = False,scrollWheelZoom = False,dragging = False
    m1 = folium.Map(location=[22.5937, 78.9629], zoom_start=5, width='100', height='100', scrollWheelZoom=False)
    state = list(covid['State'])
    latitude = list(covid['Latitude'])
    longitude = list(covid['Longitude'])
    total = list(covid['fDoses'])
    
    for s, lat, long, t in zip(state, latitude, longitude, total):
        folium.Circle(
            location=[lat, long],
            radius=float(t * .01),
            tooltip='State  : ' + s + ' \n\n Total Vaccination : ' + str(t) + '',
            color='green',
            fill=True,
            fill_color='green'
        ).add_to(m1)
    folium.raster_layers.TileLayer('Open Street Map').add_to(m1)
    folium.raster_layers.TileLayer('Stamen Terrain').add_to(m1)
    folium.raster_layers.TileLayer('Stamen Toner').add_to(m1)
    folium.raster_layers.TileLayer('Stamen Watercolor').add_to(m1)
    folium.raster_layers.TileLayer('CartoDB Positron').add_to(m1)
    folium.raster_layers.TileLayer('CartoDB Dark_Matter').add_to(m1)
    folium.LayerControl().add_to(m1)
    m1 = m1._repr_html_()
    
    df = df.loc[df['State'] == 'India']
    df['Date'] = pd.to_datetime(df["Date"], format='%d/%m/%Y')
    df.dropna(subset=["Doses"], inplace=True)
    # df.head()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=list(df.Date), y=list(df.Doses), name='Total Doses'))
    fig.add_trace(
        go.Scatter(x=list(df.Date), y=list(df.fDoses), name='First Doses'))
    fig.add_trace(
        go.Scatter(x=list(df.Date), y=list(df.sDoses), name='Second Doses'))
    # Set title
    fig.update_layout(
        title_text="Vaccination Time series"
    )
    
    # Add range slider
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )
    m2 = fig.to_html(full_html=False)
    
    """ vaccine administered comparison """
    df1 = df1.loc[df1['State'] == 'India']
    last_element = df1.iloc[-1]
    
    df1 = df1.loc[df1['Date'] == last_element.Date]
    z = [list(df1.fDoses), list(df1.sDoses)]
    z = z[0] + z[1]
    
    y = [list(df1.Covaxin), list(df1.CoviShield), list(df1.Sputnik)]
    a = y[0] + y[1] + y[2]
    
    
    labels = ['Covaxin', 'CoviShield', 'Sputnik']
    values = a
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.update_layout(
        title_text="Vaccination Types")
    m3 = fig.to_html(full_html=False)
    
    """ vaccination male-female """
    df2 = df2.loc[df2['State'] == 'India']
    df2['Date'] = pd.to_datetime(df2["Date"], format='%d/%m/%Y')
    df2.dropna(subset=["Male"], inplace=True)
    df2.dropna(subset=["Female"], inplace=True)
    df2.dropna(subset=["Transgender"], inplace=True)
    fig1 = go.Figure()
    fig1.add_trace(
        go.Scatter(x=list(df2.Date), y=list(df2.Male), name='Male'))
    fig1.add_trace(
        go.Scatter(x=list(df2.Date), y=list(df2.Female), name='Female'))
    fig1.add_trace(
        go.Scatter(x=list(df2.Date), y=list(df2.Transgender), name='Transgender'))
    # Set title
    fig1.update_layout(
        title_text="Vaccination Gender Wise"
    )
    
    # Add range slider
    fig1.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )
    m4 = fig1.to_html(full_html=False)
    
    """vaccination top 20 state"""
    df3 = df3.loc[df3['State'] != 'India']
    last_element = df3.iloc[-1]
    df3 = df3.loc[df3['Date'] == last_element.Date]
    global val1
    
    def val1():
        return df3.copy()
    
    Top5 = df3.nlargest(20, 'Doses').reset_index(drop=True)
    State = list(Top5["State"])
    
    First = list(Top5["fDoses"])
    
    Second = list(Top5["sDoses"])
    fig2 = go.Figure(data=[
    
        go.Bar(name='First Dose', x=State, y=First),
        go.Bar(name='Both Doses', x=State, y=Second)
    ])
    # Change the bar mode
    fig2.update_layout(barmode='group')
    fig2.update_layout(
        title_text="Vaccination Chart of 20 States"
    )
    m5 = fig2.to_html(full_html=False)
    
    """ Total Vaccinated  """
    z1 = int(z[0])
    z2 = int(z[1])
    pop = 1392790451
    first = (z1 / pop) * 100
    second = (z2 / pop) * 100
    first = round(first, 2)
    per = first
    second = round(second, 2)
    
    unique_state = pd.read_csv("media/state.csv")
    unique_state = list(unique_state["State"].unique())
    unique_state.sort()
    
    context = {
        'm1': m1,
        'm2': m2,
        'm3': m3,
        'm4': m4,
        'm5': m5,
        'per': per,
        'first': first,
        'second': second,
        'select_state': unique_state,
        'notification': Notification.objects.filter(receiver=request.user.username),
        'proimage': url12,
        'pagetitle': 'Vaccine chart',
    }
    return render(request, 'vaccinechart.html',context)


def mapupdate(request):
    if request.POST.get('action') == 'post':
        dist_inp = request.POST.get('mySelect')
        print(dist_inp)
        # today = date.today()
        # a = today.strftime("%d_%m_%Y") + 'district.csv'
        # b = os.path.exists('media/' + a)
        # if not b:
        #     req = requests.get('http://api.covid19india.org/csv/latest/cowin_vaccine_data_districtwise.csv')
        #     url_content = req.content
        #     csv_file = open('media/' + a, 'wb')
        #     csv_file.write(url_content)
        #     csv_file.close()
        # df = pd.read_csv('http://api.covid19india.org/csv/latest/cowin_vaccine_data_districtwise.csv', sep=',', error_bad_lines=False, index_col=False, dtype='unicode')
        pk3 = val2()
        df = pk3.copy(deep=True)
        newdf = df.dropna(axis=1).copy() #.copy() is only here to suppress a warning.
        newdf['District'] = df['District']
        newdf['State'] = df['State']
        df = newdf
        
        today = date.today()
        today1 = today
        a = today1.strftime("%d/%m/%Y")
        i = 0
        c = 0
        v = []
        while True:
            i += 1
            for col in df.columns:
                if a == col:
                    biz = a
                    v = ["State", "District", a]
                    for i in range(1, 10):
                        j = a + '.' + str(i)
                        v.append(j)

                    c = 1
            if c == 1:
                break
            b = today - timedelta(days=i)
            a = b.strftime("%d/%m/%Y")

        drop_list = v
        df = df.drop(df.columns.difference(drop_list), axis=1)
        df = df.loc[df['State'] == dist_inp]
        coordinates = pd.read_csv("media/coviddistrict.csv")
        covid = df.merge(coordinates, on='District', how='left')
        covid['Latitude'] = covid['Latitude'].fillna(0)
        covid['Longitude'] = covid['Longitude'].fillna(0)
        covid = covid.drop(['State'], axis=1)
        covid = covid.iloc[1:]
        covid = covid.dropna()
        District = list(covid['District'])
        latitude = list(covid['Latitude'])
        longitude = list(covid['Longitude'])
        total = list(covid[biz])
        firstdose = list(covid[biz + '.3'])
        seconddose = list(covid[biz + '.4'])
        districtloc = pd.read_csv("media/state.csv")
        districtloc = districtloc.loc[districtloc['State'] == dist_inp]
        a = districtloc.mean().Latitude
        b = districtloc.mean().Longitude
        population = districtloc['Population']
        # c = a + b
        f = folium.Figure(width=730, height=600)
        m1 = folium.Map(location=[a, b], zoom_start=6.2, width='100', height='100', scrollWheelZoom=True)
        for s, lat, long, t in zip(District, latitude, longitude, total):
            folium.Circle(
                location=[lat, long],
                radius=float(int(t) * .03),
                tooltip='District  : ' + s + ' \n\n Total Vaccination : ' + str(t) + '',
                color='green',
                fill=True,
                fill_color='green'
            ).add_to(m1)
        folium.raster_layers.TileLayer('Open Street Map').add_to(m1)
        folium.raster_layers.TileLayer('Stamen Terrain').add_to(m1)
        folium.raster_layers.TileLayer('Stamen Toner').add_to(m1)
        folium.raster_layers.TileLayer('Stamen Watercolor').add_to(m1)
        folium.raster_layers.TileLayer('CartoDB Positron').add_to(m1)
        folium.raster_layers.TileLayer('CartoDB Dark_Matter').add_to(m1)
        folium.LayerControl().add_to(m1)
        m1 = m1._repr_html_()

        today = date.today()
        a = today.strftime("%d_%m_%Y") + '.csv'

        population = int(population)
        ok = val1()
        ok = ok.loc[ok['State'] == dist_inp]

        z1 = int(ok['fDoses'])
        z2 = int(ok['sDoses'])

        first = (z1 / population) * 100
        second = (z2 / population) * 100
        first = round(first, 2)
        second = round(second, 2)


        """ vaccine administered comparison """
        y = [list(ok.Covaxin), list(ok.CoviShield), list(ok.Sputnik)]
        a = y[0] + y[1] + y[2]


        labels = ['Covaxin', 'CoviShield', 'Sputnik']
        values = a
        fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
        fig.update_layout(
            title_text="Vaccination Types")
        m3 = fig.to_html(full_html=False)

        """vaccination District"""

        State = District
        First = firstdose
        Second = seconddose
        for i in range(len(First)):
            First[i] = int(First[i])
            Second[i] = int(Second[i])

        fig2 = go.Figure(data=[

            go.Bar(name='First Dose', x=State, y=First),
            go.Bar(name='Both Doses', x=State, y=Second)
        ])
        # Change the bar mode
        fig2.update_layout(barmode='group')
        fig2.update_layout(
            title_text="Vaccination Chart of District"
        )
        m5 = fig2.to_html(full_html=False)

        context = {
            'h1': m1,
            'h2': m3,
            'h3': m5,
            'disfirst': first,
            'dissecond': second,
        }
    return JsonResponse(context)

def hospital(request):
    url = None
    if request.user.is_authenticated:
        url = request.user.first_name
    # m = folium.Map(location=[22.5937, 78.9629], zoom_start=5)
    # marker_cluster = MarkerCluster().add_to(m)
    # count = 0
    # l = ['https://covidaps.com/data/covidaps.com/bed_data.json','https://covidtelangana.com/data/covidtelangana.com/bed_data.json','https://covidbengaluru.com/data/covidbengaluru.com/bed_data.json','https://covidwb.com/data/covidwb.com/bed_data.json', 'https://covidamd.com/data/covidamd.com/bed_data.json', 'https://covidpune.com/data/covidpune.com/bed_data.json', 'https://covidbaroda.com/data/covidbaroda.com/bed_data.json', 'https://covidtnadu.com/data/covidtnadu.com/bed_data.json', 'https://covidmp.com/data/covidmp.com/bed_data.json', 'https://covidgandhinagar.com/data/covidgandhinagar.com/bed_data.json', 'https://covidnashik.com/data/covidnashik.com/bed_data.json', 'https://covidbeed.com/data/covidbeed.com/bed_data.json']
    # s = ['https://raw.githubusercontent.com/covidhospitals/datacollector/main/ap/ap-locations.json','https://raw.githubusercontent.com/covidhospitals/datacollector/main/ts/ts-locations.json','https://raw.githubusercontent.com/covidhospitals/datacollector/main/banglore/bangalore-locations.json','https://raw.githubusercontent.com/covidhospitals/datacollector/main/wb/wb-locations.json','https://raw.githubusercontent.com/covidhospitals/datacollector/main/ahmedabad/ahmedabad-locations.json','https://raw.githubusercontent.com/covidhospitals/datacollector/main/pune/pune-locations.json','https://raw.githubusercontent.com/covidhospitals/datacollector/main/vadodara/vadodara-locations.json','https://raw.githubusercontent.com/covidhospitals/datacollector/main/tn/tn-locations.json','https://raw.githubusercontent.com/covidhospitals/datacollector/main/mp/mp-locations.json','https://raw.githubusercontent.com/covidhospitals/datacollector/main/gandhinagar/gandhinagar-locations.json','https://raw.githubusercontent.com/covidhospitals/datacollector/main/nashik/nashik-locations.json','https://raw.githubusercontent.com/covidhospitals/datacollector/main/beed/beed-locations.json']
    # for i in range(len(l)):
    #     df3 = pd.read_json(s[i])
    #     df = pd.read_json(l[i])
    #     covid = df.copy()
    #     covid.dropna(subset=["hospital_name"], inplace=True)
    #     hospital = list(covid['hospital_name'])
    #     try:
    #         district = list(covid['district'])
    #         for h, d in zip(hospital, district):
    #             try:
    #                 a = h+"::"+d
    #                 dd = df3[a]
    #                 if dd['latitude'] != 28.5917999 and dd['longitude'] != 77.22311429999999:
    #                     folium.Marker(
    #                         location=[dd['latitude'], dd['longitude']],
    #                         # popup ="Phone number: %s"%dd['formattedAddress'],
    #                         tooltip=h,
    #                         icon=folium.Icon(icon='info-sign', color="red"),
    #                         draggable=False
    #                     ).add_to(marker_cluster)
    #                     # print(dd['formattedAddress'])
    #             except:
    #                 try:
    #                     a = h+"::undefined"
    #                     dd = df3[a]
    #                     if dd['latitude'] != 28.5917999 and dd['longitude'] != 77.22311429999999:
    #                         folium.Marker(
    #                             location=[dd['latitude'], dd['longitude']],
    #                             #  popup ="Phone number: %s"%dd['formattedAddress'],
    #                             tooltip=h,
    #                             icon=folium.Icon(icon='info-sign', color="red"),
    #                             draggable=False
    #                         ).add_to(marker_cluster)
    #                         # print(dd)

    #                 except:
    #                     count += 1
    #     except:
    #         print(s[i])
    #         try:
    #             for h in zip(hospital):
    #                 a = h+"::undefined"
    #                 dd = df3[a]
    #                 if dd['latitude'] != 28.5917999 and dd['longitude'] != 77.22311429999999:
    #                     folium.Marker(
    #                         location=[dd['latitude'], dd['longitude']],
    #                         #  popup ="Phone number: %s"%dd['formattedAddress'],
    #                         tooltip=h,
    #                         icon=folium.Icon(icon='info-sign', color="red"),
    #                         draggable=False
    #                     ).add_to(marker_cluster)
    #                     # print(dd)

    #         except:
    #             count += 1
    # folium.raster_layers.TileLayer('Open Street Map').add_to(m)
    # folium.raster_layers.TileLayer('Stamen Terrain').add_to(m)
    # folium.raster_layers.TileLayer('Stamen Toner').add_to(m)
    # folium.raster_layers.TileLayer('Stamen Watercolor').add_to(m)
    # folium.raster_layers.TileLayer('CartoDB Positron').add_to(m)
    # folium.raster_layers.TileLayer('CartoDB Dark_Matter').add_to(m)
    # folium.LayerControl().add_to(m)
    # m = m._repr_html_()
    context = {
        'proimage': url,
        'pagetitle': 'Hospital',
        # 'map': m,
    }
    return render(request, 'hospital.html', context)
