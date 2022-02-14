import email
import imaplib
import os
import sys
import shutil
from datetime import datetime

import schedule
import time

import requests
import Dunamis
import Casio
import CCPL
import FLP
from Data import data
from common import get_name

input_folder_name = 'input'
output_folder_name = 'output'
detach_dir = '.'
if input_folder_name not in os.listdir(detach_dir):
    os.mkdir(input_folder_name)
input_folder_path = os.path.abspath(input_folder_name)

if output_folder_name not in os.listdir(detach_dir):
    os.mkdir(output_folder_name)
output_folder_path = os.path.abspath(output_folder_name)
# email_id = "rpa@xtremeonline.com.au"
# password= "asnlhzigjprlmahk" #Xtreme@2020
# email_id = "rpa@megthinksolutions.com"
# password= "Rpa@1234"
user_credentials_api = 'https://tcesffb3s8.execute-api.ap-south-1.amazonaws.com/dev/rpa/getcredential'


def clear(folder_name):
    done = 'completed'
    try:
        os.mkdir(done)
    except FileExistsError:
        pass
    except Exception as e_:
        print(e_)
    from_path = os.path.abspath(folder_name)
    to_path = os.path.abspath(done)
    items = list(os.listdir(from_path))
    if len(items) > 0:
        print(f'Clearing {len(items)} files from {from_path}')
    for item in items:
        original_path = os.path.join(from_path, item)
        target = f'{folder_name}_{get_name(item.split(".")[0])}.{item.split(".")[-1]}'
        final_path = os.path.join(to_path, target)
        shutil.move(original_path, final_path)
DEVMODE = False
def get(give_data=None):
    print('Start Fetchng data...')
    time.sleep(1)
    clear(input_folder_name)
    clear(output_folder_name)

    global DEVMODE
    if give_data is None:
        DEVMODE = False
    try:
        # if True:
        # imapSession = imaplib.IMAP4_SSL('imap.megthinksolutions.com')
        if DEVMODE:
            data_list = give_data["rpaCredential"]
        else:
            data_list = []
            get_details = requests.get(url=user_credentials_api)
            if get_details.status_code == 200:
                vendor_details = get_details.json()
                if vendor_details["responseCode"] == 200:
                    data_list = vendor_details["rpaCredential"]
                else:
                    print('Unable to get details from API.')
            else:
                print(
                    "Unable to proceed further. Getting status code {} and reason {}: ".format(get_details.status_code,
                                                                                               get_details.reason))
        for give_data in data_list:
            print('Getting data from API...')
            time.sleep(1)
            run = False
            email_id = give_data["loginId"]
            password = give_data["password"]
            port = give_data["port"]
            vendorId = give_data["userId"]
            vendor_name = data_list[0]['vendor_name'] # give_data["vendor_name"]
            templateId = data_list[0]['templateId']#give_data["templateId"]
            domain = give_data["domain"]
            try:
               # ftp_url = give_data["ftp"]
               ftp_url = "http://tworobins.io/freeplus/FPPL 2021-08-06.pdf"
            except KeyError:
                ftp_url = ''
            except Exception as e:
                print(e)
                ftp_url = ''

            if vendor_name.lower() != 'freeplus':
                try:
                    imapSession = imaplib.IMAP4_SSL(domain, port)
                    typ, accountDetails = imapSession.login(email_id, password)
                    imapSession.select('INBOX')
                    typ_, msgs = imapSession.search(None, 'UNSEEN')  # ALL
                    msgs = msgs[0].split()
                except Exception as e:
                    print('Unable to get authenticate..')
                    print(f'Email: {email_id}, Vendor: {vendor_name}')
                    print(e)
                    continue

                for emailid in msgs:
                    resp, give_data = imapSession.fetch(emailid, "(RFC822)")
                    email_body = give_data[0][1]
                    m = email.message_from_bytes(email_body)

                    if m.get_content_maintype() != 'multipart':
                        continue

                    for part in m.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue
                        if part.get('Content-Disposition') is None:
                            continue

                        filename = part.get_filename()
                        if filename is not None:
                            sv_path = os.path.join(input_folder_path, filename)
                            try:
                                done_ = False
                                while not done_:
                                    if not os.path.isfile(sv_path):
                                        print(f'Saving {filename} to {sv_path}\n\tVENDOR NAME: {vendor_name}')
                                        fp = open(sv_path, 'wb')
                                        fp.write(part.get_payload(decode=True))
                                        run = True
                                        done_ = True
                                        fp.close()
                                    else:
                                        os.remove(sv_path)
                                        print('File already exist. Removing and trying again..')
                            except Exception as e:
                                print(e)
                                continue

                imapSession.close()
                imapSession.logout()
                
            if 'dunamis' in vendor_name.lower() and run:
                Dunamis.run(vendorId, templateId)
            elif 'casio' in vendor_name.lower() and run:
                Casio.run(vendorId, templateId)
            elif 'ccpl' in vendor_name.lower() and run:
                CCPL.run(vendorId, templateId)
            elif 'freeplus' in vendor_name.lower() and run:
                FLP.run(vendorId, templateId, ftp_url)
            elif run:
                print(f'Vendor {vendor_name} not found..')
            else:
                print(f'Data for {vendor_name} not found..')
            clear(input_folder_name)
            clear(output_folder_name)
            print("wating")
            
    except Exception as e:
        print(e)


def mainloop():
    while True:
        try:
            get(data)
        except KeyboardInterrupt:
            print('Exiting the loop..')
            sys.exit()


if __name__ == '__main__':
    mainloop()
