import os
import pandas as pd
from dotenv import load_dotenv

from koboextractor import KoboExtractor as kbx

from kbreport_organizer import FarmReport, FinanceReport, get_list_csv, analyze_data, excel_custom

load_dotenv()
TOKEN = os.environ.get('TOKEN')
form_info = ''

endpoint = 'https://kf.kobotoolbox.org/api/v2'


def get_form_id(token, form_name, deployed_only=True, get_saved_id=False):
    kobo = kbx(token, endpoint)
    assets = kobo.list_assets()

    if get_saved_id:
        form_id = get_list_csv('Info Docs/Form And Form ID.csv', 'Form ID', form_name)
        return form_id

    for asset in range(assets['count']):
        if deployed_only:
            if assets['results'][asset]['name'] == form_name and assets['results'][asset]['deployment_status'] == 'deployed':
                form_id = assets['results'][asset]['uid']
        else:
            if assets['results'][asset]['name'] == form_name:
                form_id = assets['results'][asset]['uid']
    return form_id

def extract_from_kobo(token, form_id):
    kobo = kbx(token, endpoint)
    data = kobo.get_data(form_id)
    return data

def convert_to_df(data):
    df = pd.json_normalize(data['results'])
    return df


id = get_form_id(TOKEN,"Personal Ledger")
ex_data = extract_from_kobo(TOKEN,id)
df = convert_to_df(ex_data)

'''Finance Report'''
personalfinance = FinanceReport(dataset=df, col_to_float='amount')
personalfinancemetrics = personalfinance.get_basic_metrics(['income','expense','receivable'],'personal')
print(personalfinancemetrics)

'''Staff Reports'''
staff_perfomance = analyze_data(dataset_main=[df], dates=[[2023, 3, 1], [2023, 3, 31]],
                                kw_csv='Reports Doc Sheets/Farm Report Keywords.csv',col_kw_csv=['Activities','Farms'],
                                csv_n_extrt_info=['Reports Doc Sheets/Staff List.csv','Organization','MGL'],clean_rem_all_or_any=True)

org_name = 'MGL'
org_mem_info = {'doc': 'Reports Doc Sheets/Staff List.csv', 'col': 'Organization', 'val_filter': org_name}
farm_report = FarmReport(name=org_name, org_mem_info=org_mem_info)
general_activities_report = farm_report.gen_activities_report(
    dataset_main=[df],dates=[[2023, 3, 1], [2023, 3, 31]],clean_rem_all_or_any=False)

# general_activities_report in Excel
excel_custom(general_activities_report,['MGL 2023 Report.xlsx','MGL March Report'])
