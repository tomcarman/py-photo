import os
import csv
import shutil

with open('python_output.csv', 'r') as csvfile:
	csv_reader = csv.reader(csvfile)

	for row in csv_reader:

		old_path = row[1]
		new_path = row[2]

		new_dir = row[2].rsplit('/', 1)[0]

		if not os.path.exists(new_dir):
			os.makedirs(new_dir)

		if not os.path.exists(new_path):
			shutil.copy2(old_path, new_path)
			print('Successfully Copied: ' + new_path)
		else: 
			print('Skipped: ' + new_path + ' already exists.')

