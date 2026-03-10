import requests, os

UPLOAD_DIR = r'd:\Upskill_github\Upskill\backend\uploads\feedback'
pdf_files = sorted(
    [f for f in os.listdir(UPLOAD_DIR) if 'ZOHO_FB' in f],
    key=lambda x: os.path.getmtime(os.path.join(UPLOAD_DIR, x)),
    reverse=True
)
print('Using file:', pdf_files[0] if pdf_files else 'NO FILE FOUND')

if pdf_files:
    import pymongo
    client = pymongo.MongoClient('mongodb://localhost:27017')
    company = client['upskill_db']['companies'].find_one()
    COMPANY_ID = str(company['_id'])
    UPLOADER_ID = 'test_admin'
    print(f'Uploading to company {company["name"]} ({COMPANY_ID})')

    file_path = os.path.join(UPLOAD_DIR, pdf_files[0])
    with open(file_path, 'rb') as f:
        resp = requests.post(
            f'http://localhost:8000/companies/{COMPANY_ID}/feedback',
            files=[('files', (pdf_files[0], f, 'application/pdf'))],
            data={'uploader_id': UPLOADER_ID},
            timeout=300
        )
    print('Status:', resp.status_code)
    try:
        print('Response:', resp.json())
    except:
        print('Raw response:', resp.text[:500])
