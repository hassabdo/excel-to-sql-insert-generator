import os
import pandas as pd
import re
from pathlib import Path
from colorama import Fore, init
from core.exceptions import MissingFileException, WrongFileFormat

init()
class SQLFileGenerator():
    def __init__(self, schema_file, input_dir, output_file):
        self.schema_file = schema_file
        self.input_dir = Path(input_dir)
        self.output_file = os.path.join(os.getcwd(), "output", output_file)
        self.schema = {}
        self.constraints = {}
        self.dataframes = {}  # Add this line
        self._load_dataframes()  # Method to load Excel files into dataframes
        
    def _load_dataframes(self):
        """Loads Excel files from the input directory into dataframes."""
        for file in os.listdir(self.input_dir):
            if file.endswith('.xlsx'):
                table_name = file[:-5]  # Assuming the file name matches the table name
                self.dataframes[table_name] = self._read_excel(os.path.join(self.input_dir, file))
                
    def _parse_schema_and_dependencies(self):
        """Parses the CREATE TABLE statements to extract column types and foreign key dependencies."""
        with open(self.schema_file, 'r', encoding='utf-8') as f:
            content = f.read()

        create_table_pattern = r'CREATE TABLE `(\w+)` \((.*?)\);'
        foreign_key_pattern = r'FOREIGN KEY \(`(\w+)`\) REFERENCES `(\w+)`'

        dependencies = {}
        for match in re.finditer(create_table_pattern, content, re.S):
            table_name, columns_block = match.groups()
            self.schema[table_name] = {}
            dependencies[table_name] = []

            # Extract column types
            column_pattern = r'`(\w+)`\s+(\w+)'
            columns = re.findall(column_pattern, columns_block)
            self.schema[table_name] = {col: col_type for col, col_type in columns}

            # Extract foreign key dependencies
            for fk_match in re.finditer(foreign_key_pattern, columns_block):
                _, referenced_table = fk_match.groups()
                dependencies[table_name].append(referenced_table)

        self.dependencies = dependencies

    def _read_excel(self, file_path):
        """Reads an Excel file and returns a DataFrame."""
        return pd.read_excel(file_path)

    def _format_value(self, row, i, col, col_types):
        """Formats a value based on its SQL column type."""
        if col.lower() == "id":
            return str(i+1)
        if col not in row:
            return "NULL"
        value = row[col]
        col_type = col_types[col]
        if pd.isnull(value):
            return "NULL"
        if col_type.lower() in ["integer", "bigint", "smallint", "tinyint"]:
            return str(int(value))
        if col_type.lower() in ["float", "double", "decimal"]:
            return str(float(value))
        if col_type.lower() in ["datetime", "timestamp"]:
            return f"'{pd.to_datetime(value).strftime('%Y-%m-%d %H:%M:%S')}'"
        # Default to string type for other cases
        return "'" + str(value).replace("'", "''") + "'"
    
    def _resolve_table_order(self):
        """Resolves the order of tables based on foreign key dependencies using topological sort."""
        from collections import defaultdict, deque

        # Build adjacency list for the dependency graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        for table, deps in self.dependencies.items():
            for dep in deps:
                graph[dep].append(table)
                in_degree[table] += 1

        # Perform topological sort
        queue = deque([table for table in self.dependencies if in_degree[table] == 0])
        sorted_tables = []

        while queue:
            current = queue.popleft()
            sorted_tables.append(current)
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_tables) != len(self.dependencies):
            raise ValueError("Cyclic dependency detected in table relationships!")

        return sorted_tables    
    
    def generate_insert_statements(self):
        """Generates the SQL INSERT statements in the correct order."""
        self._parse_schema_and_dependencies()
        sorted_tables = self._resolve_table_order()

        with open(self.output_file, 'w', encoding='utf-8') as f:
            # Write CREATE TABLE statements without constraints
            for table in sorted_tables:
                f.write(f"\n-----------------------------------------------------\n")
                f.write(f"--- Inserting data into table {table} ---\n")
                f.write(f"-----------------------------------------------------\n\n")
                if(table not in self.dataframes):
                    continue
                df = self.dataframes[table]
                columns = self.schema[table].keys()
                col_types = self.schema[table]

                values_list = []
                for i, row in df.iterrows():
                    values = [
                        self._format_value(row, i, col, col_types)
                        for col in columns
                    ]
                    values_list.append(f"\n({', '.join(values)})")

                insert_statement = f"INSERT INTO `{table}` ({', '.join([f'`{col}`' for col in columns])}) VALUES {', '.join(values_list)};\n"
                f.write(insert_statement)
                f.write(f"\n---------------------------------------------------\n")

            # Write constraints at the end
            for table, constraints in self.constraints.items():
                for constraint in constraints:
                    f.write(f"ALTER TABLE {table} ADD {constraint};\n")

        print(Fore.GREEN + f"SQL script written to {self.output_file}" + Fore.RESET)
