import pandas as pd
import glob
import os

directory = './data/'

def process_excel_file(file):
    # Step 1: Read the entire file
    df_extra_row = pd.read_excel(file, header=None)
    
    # Step 2: Extract the extra_row (first row)
    extra_row = df_extra_row.iloc[0]  # First row contains the extra data
    distance_value = extra_row[1]  # Get the distance value
    distance_unit = extra_row[2]    # Get the unit ('cm')
    
    # Step 3: Read the actual data starting from the second row
    df_data = pd.read_excel(file, skiprows=1)  # Skip the extra row, get headers from row 1
    
    print(f"Distance from targets: {distance_value} {distance_unit}")
    
    return distance_value, df_data

def process_all_excel_files():
    # Use glob to find all Excel files in the current directory
    excel_files = glob.glob(os.path.join(directory, "*.xlsx"))  # Or specify the path to the files if needed
    
    if not excel_files:
        print("No Excel files found in the directory.")
    else:
        for file in excel_files:
            distance, data = process_excel_file(file)
            # You can now work with the `distance` and `data` from each file
            # Example: store the distances or analyze the data
    
# Run the function to process all Excel files
process_all_excel_files()