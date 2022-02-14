from requests import post

endpoint = 'https://tcesffb3s8.execute-api.ap-south-1.amazonaws.com/dev/templatelog'


def validate_dunamis(df):
    df.fillna('', inplace=True)
    first_col = df[df.columns[0]]
    res = False
    for row in first_col:
        if row.lower() == 'brand':
            return True
        else:
            res = False
    return res


def validate_casio(df):
    return list(map(lambda x: x.lower(), df.columns)) == ['model', 'qty', 'hkd', 'order', 'remarks']


def validate_cppl(df):
    res = list(map(lambda x: x.lower(), df.columns[1:]))
    if res == ['hkd', 'usd', 'cost hkd']:
        return True, 1
    elif res == ['hkd']:
        return True, 2
    return False


def post_error(vendor_id, template_id):
    data = {
        "templateId": template_id,
        "errorCode": 200,
        "errormessage": f"Data error with {vendor_id}"
    }
    res = post(endpoint, json=data)
    if res.json()['responseCode'] == 200:
        print("Data for error reported succesfully..")
    else:
        print('Something BAD is happening..\nCan\'t post error data')
