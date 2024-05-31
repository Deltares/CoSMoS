import os

def rename_files1(directory):
    for filename in os.listdir(directory):
        # Check if the file matches the expected pattern
        if filename.startswith("waterlevel") and filename.endswith(".csv.js"):
            # Extract the number part (8760922 in this example)
            parts = filename.split('.')
            number = parts[2]
            model = parts[1]
            # Create the new filename
            new_filename = f"wl.{number}.{model}.csv.js"
            # Create full file paths
            old_file = os.path.join(directory, filename)
            new_file = os.path.join(directory, new_filename)
            # Rename the file
            os.rename(old_file, new_file)
            print(f"Renamed: {filename} to {new_filename}")

def rename_files2(directory):
    for filename in os.listdir(directory):
        # Check if the file matches the expected pattern
        if filename.startswith("wl") and filename.endswith(".js"):
            # Extract the number part (8760922 in this example)
            parts = filename.split('.')
            number = parts[1]
            model = parts[2]
            # Create the new filename
            new_filename = f"wl.{number}.{model}.csv.js"
            # Create full file paths
            old_file = os.path.join(directory, filename)
            new_file = os.path.join(directory, new_filename)
            # Rename the file
            os.rename(old_file, new_file)
            print(f"Renamed: {filename} to {new_filename}")

# Example usage
directory_path = r'p:\11206085-onr-fhics\03_cosmos\webviewers\nopp_event_viewer\data\hurricane_ophelia_hindcast\artificial_cycle\timeseries'  # Replace with the path to your folder
rename_files1(directory_path)