import sys

def process_methylation(file_path):
    methpositions = []

    # Read methylation positions from file
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) == 2:
                try:
                    end_position = int(parts[0])
                    methpositions.append(end_position)
                except ValueError:
                    print(f"Skipping line due to invalid format: {line}")
            else:
                print(f"Skipping line with unexpected number of columns: {line}")

    start = 60
    end = 912
    step = 24
    sites = list(range(start, end + 1, step))

    methylation_status = [1 if pos in methpositions else 0 for pos in sites]

    # Grouping the methylation status into 8-bit chunks
    group_size = 8
    grouped_strings = []

    for i in range(0, len(methylation_status), group_size):
        chunk = methylation_status[i:i + group_size]
        chunk_str = ''.join(str(x) for x in chunk)
        grouped_strings.append(chunk_str)

    ascii_chars = []
    for s in grouped_strings:
        if len(s) == 8:
            num = int(s, 2)
            char = chr(num)
            ascii_chars.append(char)

    print("Generated ASCII characters:", ascii_chars)
    return ascii_chars

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 process_methylation.py <methpos_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    process_methylation(file_path)
