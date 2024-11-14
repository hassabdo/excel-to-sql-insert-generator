import os
import pandas as pd
import re

from core.exceptions import MissingFileException, WrongFileFormat

class SQLFileGenerator():
    def __init__(self, Kwags) -> None:
        attrs = vars(Kwags)
        for key in attrs:
            setattr(self, key, attrs[key])

        self.validate_files()
        self.create_output_folder()
        self.output_file_name = os.path.join(os.getcwd(), self.output, self.table + "_table.sql")

    def create_output_folder(self):
        print('Creating output folder...')
        self.output_path = os.path.join(os.getcwd(), self.output)
        os.makedirs(self.output_path, exist_ok=True)

    def validate_files(self):
        print('File validation...')
        if not os.path.isfile(self.file):
            raise MissingFileException(f'Input file not found {self.file} !')

        if not self.file.lower().endswith(('.csv', '.xlsx')):
            raise WrongFileFormat(
                f'Wrong file format ! Accepts only files with format (csv,xlsx)')

    def read_data(self):
        print('Reading data...')
        data = []
        if self.file.lower().endswith('.csv'):
            file_data = pd.read_csv(self.file, encoding='utf-8')
        if self.file.lower().endswith('.xlsx'):
            file_data = pd.read_excel(self.file)
        # Sanitize column names
        self.columns = [self._sanitize_column_name(col) for col in file_data.columns]
        # Append each row as a list
        for _, row in file_data.iterrows():
            data.append(row.tolist())
        return data

    def _sanitize_column_name(self, column_name):
        print('Sanitizing column...')
        # Remove leading/trailing whitespace and replace non-alphanumeric characters with underscores
        sanitized = re.sub(r'\W+', '_', column_name.strip())
        return f"`{sanitized}`"  # Enclose in backticks for SQL compatibility
    
    def generate_insert_queries(self):
        print('Generating Insert Query...')
        data = self.read_data()  # Assuming _read_data is in the same class
        with open(self.output_file_name, 'w', encoding='utf-8') as f:
            # Write header comments
            f.write("-- SQL Insert Statements\n")
            f.write(f"-- Generated for table: {self.table}\n")
            f.write("-- This is a single INSERT statement for all rows\n\n")
            f.write("---------------------------------------------------------------------------------------------------------------------------\n\n")

            # Start the INSERT statement
            f.write(f"INSERT INTO {self.table} ({', '.join(self.columns)}) VALUES\n")
            
            # Generate the values for each row
            value_strings = []
            for row in data:
                values = [
                    "'" + str(value).replace("'", "''") + "'" if isinstance(value, str) else
                    ('NULL' if pd.isnull(value) else str(value))
                    for value in row
                ]
                value_strings.append(f"({', '.join(values)})")
            
            # Join all row values with commas and write to file
            f.write(",\n".join(value_strings) + ";\n")
            f.write("\n\n---------------------------------------------------------------------------------------------------------------------------")
            f.write("---------------------------------------------------------------------------------------------------------------------------\n\n")
        print("\033[1;32;40mFile generated successfully ! \033[0m")
        print("Output file path : ", self.output_file_name)