import os


def find_missing_numbers(directory):
    # Step 1: List all files in the directory
    file_names = os.listdir(directory)

    # Step 2: Extract numerical values from file names
    numbers = []
    for file_name in file_names:
        try:
            number = int(file_name.split('.')[0])  # Assuming files are named as "number.ext"
            numbers.append(number)
        except ValueError:
            pass  # Skip files that don't start with a number

    # Step 3: Identify the range
    if not numbers:
        return []

    min_num, max_num = 1, max(numbers)

    # Step 4: Find missing numbers
    full_set = set(range(min_num, max_num + 1))
    existing_set = set(numbers)
    missing_numbers = sorted(full_set - existing_set)

    return missing_numbers