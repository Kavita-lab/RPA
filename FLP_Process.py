import pandas as pd
import camelot
from os import mkdir, chdir, listdir, remove
import pandas
import requests

from colors import names
import os

from google.cloud import translate_v2

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath('gkey.json')


def translate(text):
    try:
        translator = translate_v2.Client()
        ret = translator.translate(text)['translatedText']
    except:
        ret = text
    return ret


# ## Part 1

def generate_sku(url):
    data = requests.get(url)
    try:
        os.mkdir('input')
        os.chdir('input')
    except FileExistsError:
        os.chdir('input')
    except Exception as e:
        print(e)
    file_name = 'Freeplus.pdf'
    with open(file_name, 'wb') as f:
        f.write(data.content)

    file = camelot.read_pdf(file_name)

    os.chdir('..')
    csv_folder_name = 'fppl_csv'
    try:
        mkdir(csv_folder_name)
        csv_file_path = os.path.abspath(csv_folder_name)
    except FileExistsError:
        csv_file_path = os.path.abspath(csv_folder_name)

    def get_dataframe(final_dframe):
        colors = ['red', 'dark red', 'purple']

        index_position = 0
        new_data = {
            'Brand': [],
            'Model': [],
            'Cost': [],
            'Remark': []
        }
        for color in colors:
            if final_dframe.Model.str.contains(color).any():
                val = final_dframe.loc[final_dframe.Model.str.contains(color), 'Model']
               
                for occurence in val.index:
                    final_dframe.loc[occurence, 'Model'] = final_dframe['Model'][occurence].replace(color + ' ', '')
                    
                    index_position = occurence
                new_data['Brand'].append(str(final_dframe.loc[index_position, 'Brand']))
                new_data['Model'].append(str(final_dframe.loc[index_position, 'Model']))
                new_data['Cost'].append(str(final_dframe.loc[index_position, 'Cost']))
                new_data['Remark'].append(color)
        

        newdframe = pd.DataFrame(new_data)
        
        dfname = pd.concat([final_dframe, newdframe], ignore_index=True)
        
        dfname.fillna('', inplace=True)
        dfname.sort_values(by=['Brand', 'Model'], ascending=[True, True], ignore_index=True, inplace=True)

        return dfname

    for tdf in range(len(file)):
        partdf = file[tdf].df

        exclude = ['Apple']

        lst = ['SAMSUNG', 'HTC', 'ASUS', 'Xero', 'Alcatel', 'CAT', 'Sony Xperia', 'SAMSUNG TABLET',
               'Huawei', '小米產品', 'Black shark', 'OPPO', 'JBL', 'Apple', 'One Plus', 'Xiaomi (小米)',
               'Hongmi (紅米)', 'Poco', 'Nokia', 'Google']

        new_lst = []

        for index, row in partdf.iterrows():
            for i in range(len(lst)):
                if lst[i] in row[1] and lst[i] not in exclude:
                    new_lst.append(index)
        mylist = list(dict.fromkeys(new_lst))
        mylist.append(len(partdf))

        flist = []
        for k in range(len(mylist) - 1):
            flist.append(list(range(mylist[k], mylist[k + 1])))

        for d in flist:
            dff = pd.DataFrame()
            slist = []
            for g in d:
                q = list(partdf.iloc[g])
                slist.append(q)
            dff = pd.DataFrame(slist)

            nan_value = float("NaN")
            dff.replace("", nan_value, inplace=True)
            dff.dropna(how='all', inplace=True)
            dff.replace('\n', '', regex=True, inplace=True)
            dff.replace('\\s\\s+', '', regex=True, inplace=True)
            csv_clip_path = os.path.join(csv_file_path, f'{str(dff.loc[0, 1])}.csv')
            dff.to_csv(csv_clip_path, index=False, header=False)

    # ## Part 2

    try:
        # fieldnames = ['Brand', 'Model', 'Description', 'Comments', 'Colors', 'Cost']

        fieldnames = ['Brand', 'Model', 'Cost', 'Remark']

        final_df = pd.DataFrame(columns=fieldnames)

        for file in listdir(csv_file_path):
            print(f'Reading file {file}..')
            file_path_ = os.path.join(csv_file_path, file)
            df = pandas.read_csv(file_path_)
            cols = df.columns.values[1:]
            brand = cols[0]
            if 'hongmi' in brand.lower():
                brand = 'Xiaomi'
            count = 0

            for index, row in df.iterrows():
                count += 1

                vals = row.values

                price_f = vals[-2]
                price_l = vals[-1]

                if str(price_f) != 'nan':
                    price = price_f
                else:
                    price = price_l

                vals = row.values

                trans_data = [translate(brand), vals[0], translate(vals[1]), price]

                brand = trans_data[0]
                model_no = trans_data[1]
                sep_data = trans_data[2]

                try:
                    data_list = str(sep_data).lower().replace(',', '').split(' ')
                except Exception as e:
                    print(f'{e} of {brand} in line number {count}')
                    continue

                cn = []
                for name, code in names:
                    cn.append(name.lower())

                colors = []
                model = ''
                desc = []

                for data_ in data_list:
                    if data_ in cn:
                        colors.append(data_)
                    #                 elif 'gb' in data_:
                    #                     model = data_
                    else:
                        desc.append(data_)

                gb_data = []
                simp_data = []

                for check in desc:
                    if 'gb' in check:
                        gd = check.split('gb')
                        gb_data.append(f'{gd[0]}gb')
                        try:
                            simp_data.append(gd[1])
                        except:
                            pass
                    else:
                        simp_data.append(check)
                desc = simp_data + gb_data

                description = ' '.join(desc)

                if str(model_no) != 'nan':
                    description = str(model_no) + ' ' + description

                color = ' ,'.join(colors)
                try:
                    d = color.split(' ,')
                    d1 = d[0]
                    for cl in d:
                        formated_data = [brand, description, price, cl]
                        final_df = final_df.append(pd.DataFrame([formated_data], columns=fieldnames), ignore_index=True)
                except:
                    formated_data = [brand, description, price, color]
                    final_df = final_df.append(pd.DataFrame([formated_data], columns=fieldnames), ignore_index=True)

            print(f'{count} rows processed')
            # remove(file)
        try:
            os.mkdir('flp')
            os.chdir('flp')
        except FileExistsError:
            os.chdir('flp')
        except Exception as e:
            print(e)

        final_df.to_csv('Freeplus.csv', index=False)
        processed_data = pd.read_csv('Freeplus.csv')
        dframe = get_dataframe(processed_data)
        try:
            dframe.to_csv('Freeplus.csv', index=False)
            path = os.path.abspath('Freeplus.csv')
        except Exception as e:
            print(e)
            print('Trying again..')
            os.remove('Freeplus.csv')
            dframe.to_csv('Freeplus.csv', index=False)
            path = os.path.abspath('Freeplus.csv')
        os.chdir('..')
        return path
    except Exception as e:
        print('\nError..\n')
        print(e, end='\n\n')
        return ''


def run(url='http://164.52.223.72:8080/freeplus/FPPL%202021-08-06.pdf'):
    # noinspection SpellCheckingInspection
    print('Collecting data for FLP...')
    path = generate_sku(url)
    print('Data collection completed...')
    print(f'PATH: {path}')

