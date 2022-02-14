#!/usr/bin/env python
# coding: utf-8
import os.path

import matplotlib.colors as mcolors
from os import listdir, chdir
import pandas as pd
import datetime

import requests
from currency_converter import CurrencyConverter
from common import shortner, truncate
from FLP_Process import run as run_


PROCESS_DATA = True
GENERATE_SKU = True

c = CurrencyConverter()


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


# chdir('..')
#post_url = 'https://tcesffb3s8.execute-api.ap-south-1.amazonaws.com/dev/rpa/rpaoutput1'
post_url = 'http://164.52.223.72:8080/Daas-Sender/api/createtemplatehistory'

def clear_price(value: str):
    return value.replace('$', '').replace(',', '').strip()


# noinspection DuplicatedCode
def generate_sku(vendor_id, template_id):
    try:

        fieldnames = ['retailer_sku', 'vendor_sku', 'quantity', 'cost', 'leadtime', 'vendor_name', 'purchase_name']
        # filename = 'FPPL.xlsx'
        filename = 'FPPL.xlsx'
        extention = filename.split('.')[-1]
        if extention == 'csv':
            template_df = pd.read_csv(filename, 'Lookup')
        elif extention == 'xls' or extention == 'xlsx':
            template_df = pd.read_excel(filename, 'Lookup')
        else:
            return False
        print("hello kavita")
        input_folder_name = 'flp'
        #input_folder_name = 'test'
        input_folder_path = os.path.abspath(input_folder_name)
        print("input_folder_path",input_folder_path)
        final_df = pd.DataFrame(columns=fieldnames)
        for file in listdir(input_folder_path):
            file_path = os.path.join(input_folder_path, file)
            print(f'Reading file {file}..')
            fn_list = file.lower().split('.')
            extention = fn_list[-1]
            file_name = '_'.join(fn_list)
            final_datetime = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
            file_sv_name = file_name + '-' + final_datetime

            print(file_sv_name)
            print(type(file_sv_name))

            get_df = False
            print("get_df_kavita")
            if extention == 'csv':
                df = pd.read_csv(file_path)
                get_df = True
            elif extention == 'xlsx' or extention == 'xls':
                df = pd.read_excel(file_path)
                ind = df.columns[0]
                df[ind] = df[ind].fillna(method='ffill')
                get_df = True
            else:
                return False

            if not get_df:
                print(f'Unable to read Data of file\n\tName: {file}\n\tLocation: {file_path}')
                print('Skipping to next file...')
                continue
           
            df.fillna("", inplace=True)

            cols = df.columns.values[1:]
            brand = cols[0]

            count = 0
            start = False
            print("after get_df")
            for index, row in df.iterrows():
                if df.columns[0] == 'Brand':
                    start = True

                if start:
                    vals = row.values
                    brand = vals[0]
                    model = vals[1]
                    cost = final_price(clear_price(vals[2]), 'HKD', 'AUD')

                    avg = 1000
                    # cost = 570
                    leadtime = 2
                    vendor = 'FreePlus'
                    purchase = model

                    remark1 = vals[3]
                    try:
                        remark2 = shortner(vals[3])
                    except Exception as e:
                        remark2 = remark1
                        print(e)

                    rs = f'{brand}-{model}-{remark1}'.replace(' ', '-').replace('-nan', '').replace('--', '-').replace(
                        ',', '').lower()
                   
                    purchase = (str(purchase.strip()) + ' ' + str(remark1)).replace(' nan', '')
                    val = template_df.loc[template_df[template_df.columns[0]] == rs][template_df.columns[1]]
                    if len(val) > 0:
                        vs = val.values[0]
                    else:
                        vs = 'NA'

                    formated_data = [vs, rs, avg, cost, leadtime, vendor, purchase]

                    final_df = final_df.append(pd.DataFrame([formated_data], columns=fieldnames), ignore_index=True)
                else:
                    if row.values[0] == 'Brand':
                        start = True
            print("After  2 get")
            current_datetime_stamp = (str(datetime.datetime.now()).split('.'))[0] \
                .replace(':', '_').replace('-', '_').replace(' ', '_')

            get_file_name = (file.split('.'))[0]
            genrate_final_file = get_file_name + '_SKUgenerator_' + current_datetime_stamp + '.csv'
            print('printing {}'.format(genrate_final_file))
            print("after file generate")
            done = True
            try:
                os.chdir('output')
            except FileNotFoundError:
                os.mkdir('output')
                os.chdir('output')
            except Exception as e:
                print(e)
                done = False
            final_df.to_csv(genrate_final_file, index=False)
            
            final_df['templateId'] = template_id
            final_df['vendorId'] = vendor_id
            final_df['fileName'] = file
            
            final_df.to_json('temp.json', orient='records')
           
            try:
                with open('temp.json') as content:
                    
                    #doc_content = content.read()
                    doc_content = content.read()
                    headers = {
                         'Content-Type': 'application/json'
                    }
                    result = requests.request("POST", post_url, headers=headers, data=doc_content)
                    print("result",result)
                    #result = requests.post(url=post_url, data=doc_content)
                    if result.status_code == 200:
                        print('data posted successfully.')
                        os.remove('temp.json')
            except Exception as ex:
                print(ex)
            if done:
                os.chdir('..')
    except IndentationError as e:
        print('\nError..\n')
        print(e, end='\n\n')
    return True


def run(vendor_id, template_id, url):
    if PROCESS_DATA:
        print('Starting the process for FPL...')
        run_(url)

    if GENERATE_SKU:
        ret = generate_sku(vendor_id, template_id)
        if ret:
            print('Sku generation completed...')
        else:
            print('Sku generate error....')


if __name__ == '__main__':
    run(200, 5, 'http://164.52.223.72:8080/freeplus/FPPL%202021-08-06.pdf')
