import os

import matplotlib.colors as mcolors
from os import listdir, chdir
import pandas as pd
import datetime
import requests
import json

from currency_converter import CurrencyConverter
from common import shortner, truncate

from validation import validate_dunamis, post_error

colors = list(mcolors.cnames.keys())
post_url = 'https://tcesffb3s8.execute-api.ap-south-1.amazonaws.com/dev/rpa/rpaoutput'
output_folder_name = 'output'

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


# noinspection DuplicatedCode
def generate_sku(vendor_id, template_id):
    try:
        # noinspection SpellCheckingInspection
        fieldnames = ['retailer_sku', 'vendor_sku', 'quantity', 'cost', 'leadtime', 'vendor_name', 'purchase_name']
        # noinspection SpellCheckingInspection
        filename = 'Dunamis.xlsx'
        template_df = pd.read_excel(filename, 'Lookup')
        template_df = template_df.apply(lambda x: x.astype(str).str.lower())
        input_folder_name = 'input'
        final_df = pd.DataFrame(columns=fieldnames)
        for file in listdir(input_folder_name):
            file_path = f'{input_folder_name}/{file}'
            print(f'Reading file {file}..')
            fn_list = file.lower().split('.')
            extension = fn_list[-1]
            file_name = '_'.join(fn_list)
            final_datetime = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
            file_sv_name = file_name + '-' + final_datetime
            print(file_sv_name)
            print(type(file_sv_name))

            df = pd.DataFrame()

            if extension == 'csv':
                df = pd.read_csv(file_path)
            elif extension == 'xlsx' or extension == 'xls':
                df = pd.read_excel(file_path)
                ind = df.columns[0]
                # noinspection SpellCheckingInspection
                df[ind] = df[ind].fillna(method='ffill')

            validate = validate_dunamis(df)
            if not validate:
                print('Wrong data found in Dunamis')
                post_error(vendor_id, template_id)
                return False

            df = df.apply(lambda x: x.astype(str).str.lower())
            cols = df.columns.values[1:]
            brand = cols[0]

            count = 0
            start = False

            for index, row in df.iterrows():
                if df.columns[0] == 'brand':
                    start = True

                if start:
                    vals = row.values
                    brand = vals[0]
                    model = vals[1]
                    cost = final_price(vals[2], 'HKD', 'AUD')

                    avg = 1000
                    # cost = 570
                    # noinspection SpellCheckingInspection
                    leadtime = 2
                    # noinspection SpellCheckingInspection
                    vendor = ' Dunamis (UP)'
                    purchase = model.lower()

                    remark1 = vals[3]
                    try:
                        remark2 = shortner(vals[3])
                    except Exception as e:
                        print(e)
                        remark2 = None
                    if remark2 is None:
                        remark2 = remark1

                    rs = f'{brand}-{model}-{remark1}' \
                        .replace(' ', '-') \
                        .replace('-nan', '') \
                        .replace('--', '-') \
                        .replace(',', '')
                

                    val = template_df.loc[template_df[template_df.columns[0]] == rs][template_df.columns[1]]
                    if len(val) > 0:
                        vs = val.values[0]
                    else:
                        vs = 'NA'

                    formatted_data = [vs, rs, avg, cost, leadtime, vendor, purchase]

                    final_df = final_df.append(pd.DataFrame([formatted_data], columns=fieldnames), ignore_index=True)
                else:
                    if row.values[0] == 'brand':
                        start = True
        try:
            os.chdir(output_folder_name)
        except FileNotFoundError:
            os.mkdir(output_folder_name)
            os.chdir(output_folder_name)
        # noinspection SpellCheckingInspection
        final_df.to_csv("Final Sku Gen_Dunamis.csv", index=False)
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
