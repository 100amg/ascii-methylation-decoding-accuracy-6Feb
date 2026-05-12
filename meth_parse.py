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
    print(f"Generated positions: {sites}")

    # Determine methylation status for each site
    methylation_status = []
    for pos in sites:
        if pos in methpositions:
            methylation_status.append(1)  # methylated
        else:
            methylation_status.append(0)  # not methylated

    print(f"Methylation status (1 = methylated, 0 = not methylated): {methylation_status}")

    # Print positions with their methylation status
    for pos, status in zip(sites, methylation_status):
        print(f"Position: {pos}, Methylation status: {status}")

    # Group methylation status into 8-bit chunks
    group_size = 8
    grouped_strings = []

    for i in range(0, len(methylation_status), group_size):
        chunk = methylation_status[i:i + group_size]
        chunk_str = ''.join(str(x) for x in chunk)
        grouped_strings.append(chunk_str)

    print("Grouped strings (8-bit chunks):", grouped_strings)

    # Convert chunks to ASCII
    ascii_chars = []
    for s in grouped_strings:
        if len(s) == 8:
            num = int(s, 2)
            char = chr(num)
            ascii_chars.append(char)
    print("ASCII characters:", ascii_chars)

    return ascii_chars

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 meth_parse.py <methpos_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    process_methylation(file_path)
