from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import traceback

test_content = b'Test file content'

try:
    print("Testing default_storage.save()...")
    path = default_storage.save('test_folder/test_file.txt', ContentFile(test_content))
    print(f'SUCCESS: File saved to: {path}')
    print(f'File exists: {default_storage.exists(path)}')
    default_storage.delete(path)
    print('Test file deleted')
except Exception as e:
    print(f'ERROR: {str(e)}')
    traceback.print_exc()
