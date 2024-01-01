import datetime
import random
import time
from datetime import datetime as dt
from datetime import time as tm

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

# create custom excel sheet
def excel_custom(dataframe,workb_n_sheet):
    df2excel=workb_n_sheet[0]
    dataframe.to_excel(df2excel,workb_n_sheet[1],index=False)

# returns extracted data as pandas in a list
def extract_excel(docs):
    st = time.process_time()
    report_dat=[]
    for doc in docs:
        report_dat+=[pd.read_excel(*docs[doc])]
    et = time.process_time()
    return report_dat

# col_name is a list
def get_list_csv(csv_doc,col_name,*val):
    if val:
        # get subset of data filtered by specified column value
        _list = pd.read_csv(csv_doc)
        st = time.process_time()
        sub_lst=_list.query(f"{col_name} == {val}")
        et = time.process_time()
    else:
        # get single column
        sub_lst = pd.read_csv(csv_doc,usecols=col_name)
    return sub_lst

def change_col_to_datetimetype(data_set):
    if not is_datetime64_any_dtype(data_set['date']):
        data_set['date'] = pd.to_datetime(data_set['date'], format='%Y/%m/%d', errors='coerce')

# remove entries before start_date in dataset(s)
def backdated_rep_cleaning(datasets,start_date):
    datasets_copy=[dat.copy() for dat in datasets]
    for d,datset in enumerate(datasets_copy):
        for dat in datset.index:
            if datset['date'][dat] < datetime.date(*start_date) or datset.loc[dat].str.contains(u"^[0-9]{1,2}th$").any():
                datasets[d].drop(index=datset.index[dat], inplace=True)
        datasets[d]=datasets[d].reset_index()

# remove entries after end_date in dataset(s)
def postdated_rep_cleaning(datasets,end_date):
    datasets_copy = [dat.copy() for dat in datasets]
    for d,datset in enumerate(datasets_copy):
        for dat in datset.index:
            if datset['date'][dat] > datetime.date(*end_date):
                datasets[d]=datasets[d].iloc[:dat] #slice needed portion of dataset using iloc
                break

# col_heads parameter takes only a list
def remove_nullentries(dataset,inplace,*col_heads):
    dataset_copy = dataset.copy()
    null_index = []
    nil_index = []
    if col_heads:
        if not isinstance(*col_heads, list):
            raise Exception(f'{col_heads} should be a list, col_heads only takes list type argument')

        for data in dataset_copy.index:
            if dataset_copy[col_heads[0]].loc[data].isnull().all():
                null_index+=[data]
            if dataset_copy[col_heads[0]].loc[data].str.contains("nil").any() or dataset_copy[col_heads[0]].loc[data].str.contains("Nil").any():
                nil_index+=[data]

        if len(null_index)!=0:
            dataset=dataset.drop(null_index)
        if len(nil_index)!=0:
            dataset=dataset.drop(nil_index)
    else:
        dataset=dataset.dropna(inplace=inplace)
    return dataset

# to clean data_set in reports
def rep_cleaning(start_date,end_date,data_sets,*primary_cols):
    # remove rows with any null value in primary_cols(germaine column(s)) and change 'date' column dtype if need be
    for data_set in data_sets:
        remove_nullentries(data_set,True,*primary_cols)
        if not is_datetime64_any_dtype(data_set['date']):
            data_set['date'] = pd.to_datetime(data_set['date'], format='%Y/%m/%d', errors='coerce').dt.date

    # drop backdated entries
    backdated_rep_cleaning(data_sets,start_date)
    # drop postdated entries
    postdated_rep_cleaning(data_sets,end_date)
    # drop duplicate dates for same editor
    return data_sets

# Report Class
class Report():
    def __init__(self,name):
        org_name=name

    # entries parameter takes entry per day for farm reporting
    def sort_entries_to_section(self,  entries, sections):
        '''update searching appearance of sections' name in entries to concurrent searches'''
        # change entries to list of list with entries
        # e.g [[Task 1a&b, Task 2a&b]...] to [[Task 1a, Task 1b],[Task 2a, Task 2b]...]
        ents_by_rows = []
        for ents in entries:
            sub_ebr = []
            ents = [e for e in ents if str(e) != 'nan' and str(e) != 'nil' and str(e) != 'Nil.']
            # entries without full stop
            if not any('.' in e for e in ents):
                ents_by_rows += [[ent.lower() for ent in ents]]
            # entries with full stop
            for ent in ents:
                if '.' in ent:
                    sub_ebr += ent.lower().split('.')
            if sub_ebr != []:
                ents_by_rows += [sub_ebr]

        # remove '' and ' ' in entries. Also remove leading and trailing whitespaces with strip()
        ents_by_rows = [[e.strip() for e in ents if e and e != ' ' and e != '\n'] for ents in ents_by_rows]
        unsorted_entries = []
        sorted_entries = {s: [] for s in sections}
        # iterate through sections
        for sect in sections:
            for ents in ents_by_rows:
                for n, ent in enumerate(ents):
                    # check if current section name is used in entry
                    if sect in ent:
                        sorted_entries[sect] += [ent.capitalize() + '.']
                        ents.remove(ent)
                    # if none of section names is used and entry is not the first for current entries iterable,
                    # add entry as part of current section
                    elif sect not in ent:
                        ent_any_sect = list(map(lambda x: False if x not in ent else True, sections))
                        if not any(ent_any_sect) and n != 0 and len(sorted_entries[sect]) != 0:
                            sorted_entries[sect] += [ent.capitalize() + '.']
                            ents.remove(ent)
                        elif not any(ent_any_sect):
                            unsorted_entries += [ent.capitalize() + '.']
                            ents.remove(ent)
            sorted_entries[sect] = ' '.join(sorted_entries[sect])
        sorted_entries['Others'] = ' '.join(unsorted_entries)
        # remove empty sections
        sorted_entries = {k: v for (k, v) in sorted_entries.items() if v != ''}
        return sorted_entries

    # returns [[editors],[entries]...]
    def col_entry_and_editor(self,data, editor_registry, col_header):
        # single or double column entry and their editors
        if isinstance(col_header, str):
            clean_data = remove_nullentries(data, False, [col_header])
            if clean_data.empty:
                return
            raw_lst_data = clean_data[['_submitted_by', col_header]].values.tolist()
        else:
            clean_data = remove_nullentries(data, False, col_header)
            if clean_data.empty:
                return
            raw_lst_data = clean_data[['_submitted_by', *col_header]].values.tolist()

        ord_lst_data = [[raw_lst_data[ele][lst] for ele in range(len(raw_lst_data))] for lst in
                        range(len(raw_lst_data[0]))]
        ord_lst_data[0] = self.entries_submitted_by(ord_lst_data[0], editor_registry).split(', ')
        return ord_lst_data

    # editors_id takes a list argument
    # editors_registry should be a dictionary
    def entries_submitted_by(self, editors_id, editors_registry):
        if len(editors_id) == 1:
            eid = editors_id[0].split('_')[0].upper()
            editors = editors_registry[eid]
        else:
            editors_id = [eid.split('_')[0].upper() for eid in editors_id]
            editors = [editors_registry[eid] for eid in editors_id if eid in editors_registry]
            editors = ', '.join(editors)
        return editors

    # In farm reporting, to check supervisor for tasks
    def check_editor_used_keyword(self, keyword_var, entries):
        kw_check = []
        for kw in keyword_var:
            if any([kw for ent in entries if kw in ent]):
                kw_check += [True]
        if any(kw_check):
            return True

    def get_supervisors(self, editors_n_entries, keyword_var):
        supervisors = []
        for n, (ent1, ent2) in enumerate(zip(editors_n_entries[1], editors_n_entries[2])):
            if self.check_editor_used_keyword(keyword_var, [ent1, ent2]):
                supervisors += [editors_n_entries[0][n]]
        return supervisors


class FarmReport(Report):
    def __init__(self):
        pass

    def gen_activities_report(self,docsheet, dates, org):
        dataset_raw = extract_excel(docsheet)
        dataset = rep_cleaning(*dates, dataset_raw, ['Tasks (AM)', 'Tasks (PM)'])
        return self.activities_report(dataset[0], org)

    def activities_report(self, dataset, org):
        report_df = pd.DataFrame()

        dates = list(set(dataset[['date']].values.reshape(-1, ).tolist()))
        dates.sort()
        sections = get_list_csv("Farm Report Keywords.csv", ['Farms']).dropna().values.reshape(
            -1, ).tolist()  # switch to global var or class attribute
        editors_registry = self.editors_register('Staff List.csv', 'Organization', org)
        supervisor_kw = ['supervis', 'Supervis']

        for date in dates:
            sub = dataset[dataset['date'] == date]
            entries = sub[['Tasks (AM)', 'Tasks (PM)']].values.tolist()
            ents_4_edts = [[str(entries[n][m]) for n in range(len(entries))] for m in range(len(entries[0]))]
            farm_nat_of_work = self.sort_entries_to_section(entries, sections)
            no_of_ents = len(farm_nat_of_work)
            editors_id = sub[['_submitted_by']].values.reshape(-1, ).tolist()
            editors_n_entries = [self.entries_submitted_by(editors_id, editors_registry).split(', '), *ents_4_edts]

            date_ = [date] + [''] * (no_of_ents - 1)
            farm = [k.capitalize() for k in farm_nat_of_work.keys()]
            nature_of_work = farm_nat_of_work.values()
            progress = [''] * no_of_ents
            jobs_completed_by = [self.entries_submitted_by(editors_id, editors_registry)] + [''] * (no_of_ents - 1)
            supervisor = [', '.join(self.get_supervisors(editors_n_entries, supervisor_kw))] + [''] * (no_of_ents - 1)
            incidence_delay = [self.combine_col_entries(sub, editors_registry, 'Incidence')] + [''] * (no_of_ents - 1)
            comments = [self.combine_col_entries(sub, editors_registry, 'Comments')] + [''] * (no_of_ents - 1)

            daily_rep_dic = {
                'Date': date_, 'Farm': farm, 'Nature Of Work': nature_of_work, 'Progress': progress,
                'Jobs Completed BY': jobs_completed_by, 'Supervisor': supervisor, 'Incidence/Delay': incidence_delay,
                'Comments': comments
            }
            daily_rep_df = pd.DataFrame(daily_rep_dic)
            report_df = pd.concat([report_df, daily_rep_df], ignore_index=True)
        return report_df

    # combine incidence, comments or any other column entries
    def combine_col_entries(self, data, editor_registry, col_header=None):
        if 'Incidence' in col_header:
            inc_data = self.col_entry_and_editor(data, editor_registry, 'Incidence/Delay')
            # return if there is no entry of incidences
            if inc_data is None:
                return ''
            incidences_lst = [f'{inc_data[0][dat]} reported that {inc_data[1][dat].lower()}'
                              if '.' in inc_data[1][
                dat] else f'{inc_data[0][dat]} reported that {inc_data[1][dat].lower()}.'
                              for dat in range(len(inc_data[0]))]
            new_entry = ' '.join(incidences_lst)
        elif 'Comments' in col_header:
            comm_data = self.col_entry_and_editor(data, editor_registry, 'Comments')
            # return if there is no comments entries
            if comm_data is None:
                return ''
            comments_lst = [f'{comm_data[0][dat]} commented that {comm_data[1][dat].lower()}'
                            if '.' in comm_data[1][
                dat] else f'{comm_data[0][dat]} commented that {comm_data[1][dat].lower()}.'
                            for dat in range(len(comm_data[0]))]
            new_entry = ' '.join(comments_lst)
        elif col_header == None:
            pass
        else:
            data = self.col_entry_and_editor(data, editor_registry, col_header)
            # return if there is no data entry
            if data is None:
                return ''
            lst = [f'{data[0][dat]}: {data[1][dat].lower()}'
                   if '.' in data[1][
                dat] else f'{data[0][dat]}: {data[1][dat].lower()}.'
                   for dat in range(len(data[0]))]
            new_entry = ' '.join(lst)
        return new_entry

    def editors_register(self, doc, col, val_filter):
        register = get_list_csv(doc, col, val_filter)
        editor_raw = register[['ID Acronym', 'First Name', 'Last Name']].values.tolist()
        editors = {ent[0]: f'{ent[1]} {ent[2]}' for ent in editor_raw}
        return editors


class FinanceReport():
    def __init__(self, dataset, col_to_float):
        self.dataset = self.convert_col_to_float(dataset,col_to_float)

    def convert_col_to_float(self, dataset, col):
        if col in dataset:
            dataset[col] = dataset[col].astype(float)
            return dataset
        else:
            return dataset

    def col_metrics_data(self, col_name, group, sort_by, dataset):
        datagroup = dataset[dataset[col_name] == group].copy()
        datagroup.sort_values(by=sort_by, inplace=True)
        return datagroup

    # can be used to get basic income, sales, expenses metrics
    def basic_metrics(self, dataset):
        biggest = dataset.head()
        smallest = dataset.tail()
        dataset['cumsum'] = dataset[['amount']].cumsum()
        return [biggest, smallest, dataset]

    # e.g. entry_types = ['income', 'sales', 'expenses']
    # metric_category can be personal or business
    def get_basic_metrics(self, entry_types, metric_category):
        data_groups={ent_type: self.col_metrics_data('entry_type',ent_type,'amount',self.dataset)
                    for ent_type in entry_types
                     }

        # receivables & payables
        # income_dt: get income data as pandas, receivable_dt: filter the receivables,
        # data_groups: include in data_groups dictionary
        if metric_category == 'personal':
            income_dt = self.dataset[self.dataset['entry_type'] == 'income']
            receivable_dt = self.col_metrics_data('payment_status', 'yes', 'amount_owed', income_dt)
            data_groups['receivable'] = receivable_dt

            expenses_dt = self.dataset[self.dataset['entry_type'] == 'expense']
            payable_dt = self.col_metrics_data('payment_status', 'yes', 'amount_owed', expenses_dt)
            data_groups['payable'] = payable_dt

        elif metric_category == 'business':
            sales_dt = self.dataset[self.dataset['entry_type'] == 'sales']
            receivable_dt = self.col_metrics_data('payment_status', 'no', 'amount_owed', sales_dt)
            data_groups['receivable'] = receivable_dt

            expenses_dt = self.dataset[self.dataset['entry_type'] == 'expense']
            payable_dt = self.col_metrics_data('payment_status', 'no', 'amount_owed', expenses_dt)
            data_groups['payable'] = payable_dt

        # basic metrics
        basic_metrics = {}
        for ent_type in entry_types:
            type_basic_metrics = self.basic_metrics(data_groups[ent_type])
            basic_metrics[ent_type] = {'biggest': type_basic_metrics[0], 'smallest': type_basic_metrics[1],
             'cumsum': type_basic_metrics[2]}
        self.basic_metrics_dataset = basic_metrics
        return basic_metrics

    def basic_metrics_json(self):
        pass

# Sample Run
if __name__ == '__main__':
    farm_report= FarmReport()
    report_df=farm_report.gen_activities_report({'Daily_Report':["MEG Farmers Daily Report.xlsx", "MEG Farmers Daily Report"]},
                              [[2023,6,1],[2023,7,31]],'MEG')

    excel_custom(report_df,['MEG 2023 Farm Report.xlsx','MEG Farm Report'])
