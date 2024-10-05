import os

def rename_images_in_directory():
    # Get the directory where the script is located
    directory = os.path.dirname(os.path.abspath(__file__))
    
    # Loop through all files in the specified directory
    for filename in os.listdir(directory):
        # Check if the file has a .jpeg extension
        if filename.lower().endswith('.jpeg'):
            # Create the new filename with .jpg extension
            new_filename = filename[:-5] + '.jpg'  # Remove .jpeg and add .jpg
            # Get the full path for the old and new filenames
            old_file = os.path.join(directory, filename)
            new_file = os.path.join(directory, new_filename)
            # Rename the file
            os.rename(old_file, new_file)
            print(f'Renamed: {old_file} to {new_file}')

# Run the function
rename_images_in_directory()