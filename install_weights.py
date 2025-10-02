import gdown
import zipfile
import os

# Ссылка на архив весов на Google Drive
url = 'https://drive.google.com/uc?id=1yrBHeEO8GQU97b8Og_E-LCFrfTawb8E2'

# Локальный путь для сохранения архива
output = 'weights.zip'

# Папка для распаковки
extract_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')

# Скачиваем архив
print("Downloading weights archive...")
# gdown.download(url, output, quiet=False)

# Создаем папку для распаковки если нет
os.makedirs(extract_folder, exist_ok=True)

# Распаковываем архив
print("Extracting weights archive... to:", extract_folder)
with zipfile.ZipFile(output, 'r') as zip_ref:
    zip_ref.extractall(extract_folder)

print("Weights installed successfully.")
