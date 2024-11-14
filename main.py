import argparse
from core import SQLFileGenerator

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--table','-t',required=True,help='table name')
    parser.add_argument('--file','-f',required=True,help='data file path')
    parser.add_argument('--output','-o',required=False,default='output',help='output folder')
    args = parser.parse_args()
    generator = SQLFileGenerator(args)
    generator.generate_insert_queries()
    exit(0)