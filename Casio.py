#!/usr/bin/env python
# coding: utf-8
import os

import requests
import json

import matplotlib.colors as mcolors
from os import listdir, chdir
import pandas as pd
import string
import datetime
from currency_converter import CurrencyConverter
from validation import validate_casio, post_error
from common import truncate

colors = list(mcolors.cnames.keys())
post_url = 'https://tcesffb3s8.execute-api.ap-south-1.amazonaws.com/dev/rpa/rpaoutput'
output_folder_name = 'output'
c = CurrencyConverter()


def clean(data):
    return ''.join(char for char in data if char in string.ascii_letters + '-' + string.digits + ' ')


# function to convert HKD to AUD
def final_price(input_price, input_currency, output_currency):
    try:
        return truncate(c.convert(input_price, input_currency, output_currency), 2)
    except ValueError:
        print('Price data is empty.. Returned Null...')
    except Exception as e:
        print('Got error on price conversion...')
        print(e)
    return 0

# noinspection DuplicatedCode
def generate_sku(vendor_id, template_id):
    try:
        fieldnames = ['retailer_sku', 'vendor_sku', 'quantity', 'cost', 'leadtime', 'vendor_name', 'purchase_name']
        filename = 'UP Casio Template 20210726.xlsx'
        template_df = pd.read_excel(filename, 'Lookup')
        print(template_df)
        
        input_folder_name = 'input'

        for file in listdir(input_folder_name):
            file_path = f'{input_folder_name}/{file}'

            print(f'Reading file {file}..')

            final_df = pd.DataFrame(columns=fieldnames)

            temp_df = pd.read_excel(file_path)

            validate = validate_casio(temp_df)
            if not validate:
                print('Wrong data found in CASIO')
                post_error(vendor_id, template_id)
                return False

            temp_df_qty = temp_df[
                (temp_df['QTY'] != 0) & (temp_df['QTY'] != 1) & (temp_df['QTY'] != 2)& (temp_df['QTY'] != 3)& (temp_df['QTY'] != 4)  & (temp_df['QTY'] != "TAKE ALL")]

            
            temp_df_qty.fillna("", inplace=True)
            index = temp_df_qty[temp_df_qty.QTY.str.contains(r'[^a-zA-Z]', na=False)].index
            temp_df_qty.drop(index, inplace=True)
            
            temp_df_qty.columns = ['MODEL', 'QTY', 'HKD', 'ORDER', 'Remarks']
           
            df = temp_df_qty[(temp_df_qty['Remarks'] != 'DISCONTINUED') & (temp_df_qty['Remarks'] != 'NO TAG') & (
                        temp_df_qty['Remarks'] != 'NO MANUAL') & (temp_df_qty['Remarks'] != 'NO PACKING') & (
                                         temp_df_qty['Remarks'] != 'NO PAPER BOX') & (
                                         temp_df_qty['Remarks'] != 'not perfect  paper box') & (
                                         temp_df_qty['Remarks'] != 'Replaced the original rubber strap')]
            
            df = df[~df["Remarks"].str.contains('DECODE', na=False)]

            cols = df.columns.values[1:]
            brand = cols[0]

            count = 0
            start = False

            file_sv_name = f'{datetime.datetime.now()}'.split('.')[0]

            for index, row in df.iterrows():
                if df.columns[0] == 'MODEL':
                    start = True

                if start:
                    vals = row.values
                    # sku = vals[0]
                    sku = clean(vals[0])
                    qty = vals[1]
                    
                    cost = final_price(vals[2], 'HKD', 'AUD')

                    vendor = "Union Promise Limited"
                    leadtime = 2

                    remark = vals[4]

                    val = template_df.loc[template_df[template_df.columns[0]] == sku][template_df.columns[1]]

                    

                    if len(val) > 0:
                        vs = val.values[0]
                    else:
                        vs = 'N/F'

                    formatted_data = [vs, sku, qty, cost, leadtime, vendor, sku]
                    fieldnames = ['retailer_sku', 'vendor_sku', 'quantity', 'cost', 'leadtime', 'vendor_name',
                                  'purchase_name']

                    final_df = final_df.append(pd.DataFrame([formatted_data], columns=fieldnames), ignore_index=True)
                    final_df.fillna("#N/A", inplace=True)
                else:
                    if row.values[0] == 'MODEL':
                        start = True

            try:
                os.chdir(output_folder_name)
            except FileNotFoundError:
                os.mkdir(output_folder_name)
                os.chdir(output_folder_name)
            final_df.to_csv("sku_file.csv", index=False)
            os.chdir('..')
            
            final_df['templateId'] = template_id
            final_df['vendorId'] = vendor_id
            final_df['fileName'] = file
            
            final_df.to_json('temp.json', orient='records')
            
            try:
                with open('temp.json') as content:
                   
                    doc_content = content.read()
                    result = requests.post(url=post_url, data=doc_content)
                    print('data posted successfully.')
                    
            except Exception as ex:
                print(ex)
    except IndentationError as e:
        print('\nError..\n')
        print(e, end='\n\n')
    finally:
        return True


def run(vendor_id, template_id):
    print('Generating sku for casio...')
    ret = generate_sku(vendor_id, template_id)
    if ret:
        print('Sku generation completed...')
    else:
        print('Sku generate error....')
