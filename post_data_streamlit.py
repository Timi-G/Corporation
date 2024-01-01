import streamlit as st
import pandas as pd
import plotly.express as px

from get_kbdata_report import personalfinancemetrics as pfm

def first_page():
    main_container = st.empty()

    with main_container.container():
        st.header('Overbrim Analytics')
        personal_col, business_col = st.columns(2)

        if 'personalbtn' not in st.session_state:
            st.session_state.personalbtn = False
        def personal_btn():
            st.session_state.personalbtn = True
        with personal_col:
            st.button('Personal', on_click = personal_btn, use_container_width=True)

        if 'businessbtn' not in st.session_state:
            st.session_state.businessbtn = False
        def business_btn():
            st.session_state.businessbtn = True
        with business_col:
            st.button('Business', on_click = business_btn, use_container_width=True)

    if st.session_state.personalbtn:
        main_container.empty()
        personal_container(pfm,['description','amount'])
    if st.session_state.businessbtn:
        main_container.empty()
        business_container(pfm)

def personal_container(financemetrics,plot_axes):
    st.header('Personal')
    # get names of finance metrics in Sentence case
    fm_names = [fk.capitalize() for fk in list(financemetrics.keys())]
    metrics_tabs = st.tabs(fm_names)

    # use loop to insert buttons and other widgets in tab of each finance metric
    for n in range(len(metrics_tabs)):
        fm_name=fm_names[n].lower()
        with metrics_tabs[n]:
            stats = list(financemetrics[fm_name].keys())
            st.subheader('Chart')

            if 'show_chart' not in st.session_state:
                st.session_state.show_chart = 'biggest'
            # callable for when stats buttons are clicked. Included active_btn_name to store name of stat
            def fm_stats_chart(btn_key):
                st.session_state.show_chart = btn_key
                print(st.session_state.show_chart)

            # instantiate column container that stats button will fill
            graph_cons = st.columns(len(stats)+3)
            # create stats widgets (button & date_input) and insert in appropriate column container
            for x,gph_con in enumerate(graph_cons[:len(graph_cons)-3]):
                with gph_con:
                    st.button(stats[x].capitalize(), on_click=fm_stats_chart(stats[x]), key=fm_name+'_'+stats[x])
            with graph_cons[-2]:
                from_date = st.date_input('From', key=fm_name+'_'+'from')
            with graph_cons[-1]:
                to_date = st.date_input('To', key=fm_name+'_'+'to')

            # plot and show chart
            # '''include from and to date conditions in plotting and showing chart and writing table'''
            f'''{st.session_state.show_chart}'''
            chart = plot_chart(financemetrics[fm_name][st.session_state.show_chart],plot_axes)
            st.plotly_chart(chart)
            st.subheader('Table')
            # write and show table of metric's stat
            # '''make writing table a function to apply pythonic flexible choice of columns to show'''
            st.write(financemetrics[fm_names[n].lower()][st.session_state.show_chart][['date','description','amount','cumsum']])


def business_container(financemetrics):
    st.header('Business')

def basic_metric_plot():
    pass

def plot_chart(data,axes):
    metric_plot = px.line(data,x=axes[0],y=axes[1])
    return metric_plot

first_page()
