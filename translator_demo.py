from google.cloud import translate_v2
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath('gkey.json')

def translate(text):
    try:
        translator = translate_v2.Client()
        ret = translator.translate(text)['translatedText']
    except:
        ret = text
    return ret
    
print(translate(" é›™å¡é»‘è—å•žéŠ€ç²‰8+128gb ")  )  
