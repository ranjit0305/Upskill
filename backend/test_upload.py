import requests
import os

url = "http://127.0.0.1:8000/companies/698045dfbec872713466d484/feedback"
uploader_id = "69804f048a4938c92164b864"

# Create a couple of dummy files
with open("test1.pdf", "w") as f: f.write("dummy pdf 1")
with open("test2.pdf", "w") as f: f.write("dummy pdf 2")

files = [
    ('files', ('test1.pdf', open('test1.pdf', 'rb'), 'application/pdf')),
    ('files', ('test2.pdf', open('test2.pdf', 'rb'), 'application/pdf'))
]
data = {'uploader_id': uploader_id}

response = requests.post(url, files=files, data=data)
print(response.status_code)
print(response.json())

# Cleanup
os.remove("test1.pdf")
os.remove("test2.pdf")
