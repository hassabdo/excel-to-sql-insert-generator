import argparse
from core import SQLFileGenerator

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--schema_file', required=True, 
                        help="SQL file containing CREATE TABLE statements.")
    parser.add_argument('-i', '--input_dir', required=False, default='input',
                        help="Directory containing Excel files (one per table).")
    parser.add_argument('-o', '--output_file', required=False, default='dump.sql',
                        help="Output SQL file to save the generated script.")
    args = parser.parse_args()
    generator = SQLFileGenerator(schema_file=args.schema_file, input_dir=args.input_dir, output_file=args.output_file)
    generator.generate_insert_statements()
    exit(0)