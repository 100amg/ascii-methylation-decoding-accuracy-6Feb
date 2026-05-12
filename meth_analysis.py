import statistics
import sys

def process_methylation(file_path, bitwidth):

    methpositions = []
    # ------------------------------
    # Read methylation positions
    # ------------------------------
    with open(file_path, "r") as file:
        for line in file:
            parts = line.split()
            if len(parts) == 2:
                try:
                    end_position = int(parts[0])
                    methpositions.append(end_position)
                except ValueError:
                    print(f"Skipping invalid line: {line}")
            else:
                print(f"Skipping unexpected line format: {line}")

    # ------------------------------
    # Generate all CG sites which could be methylated 
    # ------------------------------
    start, end, step = 60, 912, 24
    sites = list(range(start, end + 1, step))
    print(f"CG sites: {sites}")

    # Determine methylation status
    methylation_status = [1 if pos in methpositions else 0 for pos in sites]
    print(f"Methylation status: {methylation_status}")

    # Print each site + status
    for pos, status in zip(sites, methylation_status):
        print(f"Position: {pos}, Bit Value: {status}")

    # ------------------------------
    # Group into chunks based on BITWIDTH
    # ------------------------------
    group_size = bitwidth  # 7 or 8
    grouped_strings = []

    for i in range(0, len(methylation_status), group_size):
        chunk = methylation_status[i:i + group_size]
        chunk_str = ''.join(str(x) for x in chunk)
        grouped_strings.append(chunk_str)

    print(f"Grouped strings ({bitwidth}-bit chunks):", grouped_strings)

    # ------------------------------
    # Convert binary chunks to ASCII
    # ------------------------------
    ascii_chars = []
    for s in grouped_strings:
        if len(s) == bitwidth:
            num = int(s, 2)
            ascii_chars.append(chr(num))

    print("ASCII characters:", ascii_chars)
    return ascii_chars


# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 pipe.py <methpos_file> <bitwidth 7|8>")
        sys.exit(1)

    file_path = sys.argv[1]
    bitwidth = int(sys.argv[2])

    if bitwidth not in (7, 8):
        print("Error: bitwidth must be 7 or 8")
        sys.exit(1)

    process_methylation(file_path, bitwidth)
