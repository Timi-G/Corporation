# Corporation
Automations and analysis used by corporations.

# Code Files
- kbreport_organizer.py is the Main code file, it contains all the classes that manage reporting an has a sample code snippet to give an excel output. API endpoints will be built on top of the dataframe results from this file to ensure the option of further development and use cases.
Sample output file is 'MEG 2023 Farm Reports.xlsx'
- get_kbdata_report.py can access Kobotoolbox API to get data that will be worked on for reporting.
- post_data_streamlit.py file contains code for the Visualization of data and metrics desired by users. This file will use Streamlit extensively.

# Things To Do
* Update output function to enable user choose format of output file.
* Further customize Excel file output.
* Finish Visualization in post_data_streamlit.py
