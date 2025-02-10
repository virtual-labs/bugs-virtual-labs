import os
import shutil

current_directory = os.getcwd() 
target_directory = 'img/older' 

if not os.path.exists(target_directory):
    os.makedirs(target_directory)

for file_name in os.listdir(current_directory):
    if file_name.lower().endswith('.png'):
        file_path = os.path.join(current_directory, file_name)
        
        target_path = os.path.join(current_directory, target_directory, file_name)
        
        shutil.move(file_path, target_path)
        print(f"Moved {file_name} to {target_directory}")
