import FLP
import pandas as pd
import camelot
import requests
import os
#url = "http://tworobins.io/freeplus/FPPL 2021-08-06.pdf"   #Could not read malformed PDF file
url = "http://164.52.223.72:8080/freeplus/FPPL%202021-08-06.pdf"
#url = "https://www.freeplus.com.hk/quotation.pdf" # working
#url = "http://164.52.223.72:8080/freeplus/FPPL%202021-08-11.pdf" #working
#url = "http://164.52.223.72:8080/freeplus/FPPL%202021-08-16.pdf"
data = requests.get(url)
print(data)
#print(data.content)

#try:
#    os.mkdir('FreePlus_input')
#    os.chdir('FreePlus_input')

#except FileExistsError:
 #   os.chdir('FreePlus_input')
#except Exception as e:
#    print(e)
file_name = 'Freeplus.pdf'
with open(file_name, 'wb') as f:
    f.write(data.content)
#FreePlus_input_path = os.path.abspath(FreePlus_input ) 
#print("FreePlus_input_path",FreePlus_input_path)    
print("file written")
#file = camelot.read_pdf('Freeplus.pdf')
#print("Kavita file size")

#input_folder = "input1"
#filename = "FPPL.pdf"
#from tabula import read_pdf
#df = read_pdf('C:\Python\Python37\9_feb\rpa-main (2)\rpa-main\SKUgenerater\data.pdf')
#input_folder_path = os.path.abspath(input_folder)
#print("input_folder_path",os.path.abspath(input_folder))
#file_data  = camelot.read_pdf("input1/free_plusdata.pdf")
print("control moving to FLP")
FLP.run(200, 5, 'http://164.52.223.72:8080/freeplus/FPPL%202021-08-06.pdf')
print("After call")
