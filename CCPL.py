import pandas as pd
from os import listdir
import requests
from currency_converter import CurrencyConverter
import os
from common import truncate
from validation import validate_cppl, post_error

post_url = 'https://tcesffb3s8.execute-api.ap-south-1.amazonaws.com/dev/rpa/rpaoutput'
user_credentials_api = 'https://tcesffb3s8.execute-api.ap-south-1.amazonaws.com/dev/rpa/getcredential'
c = CurrencyConverter()


# function to convert HKD to AUD
def final_price(input_price, input_currency, output_currency):
    return truncate(c.convert(input_price, input_currency, output_currency), 2)


def generate_sku(vendor_id, template_id):
    try:
        fieldnames = ['retailer_sku', 'vendor_sku', 'quantity', 'cost', 'leadtime', 'vendor_name', 'purchase_name',
                      'templateId']

        filename = 'CC PL LOOKUP.xlsx'
        template_df = pd.read_excel(filename)

        input_folder_name = 'input'

        get_details = requests.get(url=user_credentials_api)
        vendor_details = get_details.json()
        templateId = vendor_details['rpaCredential'][0]['templateId']
        print('Getting files..')
        for file in listdir(input_folder_name):
            file_path = f'{input_folder_name}/{file}'
            data = pd.read_excel(file_path)
            validate, input_type = validate_cppl(data)
            if not validate:
                print('Wrong data found in CPPL')
                post_error(vendor_id, template_id)
                return False

            data = data.dropna(how='all')
            data = data[data[data.columns[0]].notna()]
            data.reset_index(drop=True, inplace=True)
            if input_type == 1:
                brands = data[data['COST HKD'].isna()]
                last_col = 'COST HKD'
                cost_index = 3
                print('Data type 1 found..')
            else:
                brands = data[data['HKD'] == 'HKD']
                last_col = 'HKD'
                cost_index = 1
                print('Data type 2 found..')
            sep_index = brands.index

            final_df = pd.DataFrame(columns=fieldnames)

            first = 0
            last = 0
            name = list(data.columns)
            mx = len(sep_index) + 1
            dfs = []
            n = 0
            print('Generating new dataframe..')
            for i in range(mx):
                if n == mx:
                    last = -1
                else:
                    try:
                        last = sep_index[n]
                    except:
                        last = -1

                name[0] = name[0].strip()

                new_df = pd.DataFrame(data.iloc[first:last])
                new_df.columns = name
                dfs.append(new_df)

                try:
                    name = list(data.iloc[sep_index[n]])
                    name[-1] = last_col
                except:
                    pass

                n += 1
                first = last + 1
            print('Appending to data...')
            for df in dfs:
                brand = df.columns[0]
                for index, row in df.iterrows():
                    qty = 100
                    # convert cost to AUD
                    cost = final_price(row[cost_index], 'HKD', 'AUD')
                    leadtime = 2
                    vendor = 'Union Promise Limited'
                    name = row[0]

                   
                    v_sku = (brand + '-' + row[0].strip()).replace(' ', '-')
                    r_sku_r = template_df.loc[template_df[template_df.columns[0]] == v_sku][template_df.columns[1]]
                    try:
                        r_sku = r_sku_r.values[0]
                    except:
                        r_sku = 'NA'

                    formated_data = [r_sku, v_sku, qty, cost, leadtime, vendor, name, templateId]

                    final_df = final_df.append(pd.DataFrame([formated_data], columns=fieldnames), ignore_index=True)
            print('Saving data....')
            name = f"{file.split('.')[0]}.csv"
            final_df.to_csv(os.path.join(os.path.abspath('output'), name), index=False)
            final_df['templateId'] = template_id
            final_df['vendorId'] = vendor_id
            final_df['fileName'] = file
            
            final_df.to_json('temp.json', orient='records')
           
            print('Posting data....')
            try:
                with open('temp.json') as content:
                   
                    doc_content = content.read()
                    print(doc_content)
                    result = requests.post(url=post_url, data=doc_content)
                    print(result)
                    print('data posted successfully.')
                   
            except Exception as ex:
                print(ex)
                print('Error in posting data...')
    except Exception as e:
        print(e)
        pass
    finally:
        return True


def run(vendor_id, template_id):
    print('Generating sku for CCPL...')
    ret = generate_sku(vendor_id, template_id)
    if ret:
        print('Sku generation completed...')
    else:
        print('Sku generate error....')


if __name__ == '__main__':
    run(200, 50)
