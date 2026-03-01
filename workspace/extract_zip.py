import zipfile
with zipfile.ZipFile('workspace.zip', 'r') as zip_ref:
    zip_ref.extractall('C:\Users\akhil\Test Project\extracted_files')
print('Unzipped files to C:\Users\akhil\Test Project\extracted_files')