# error_stats.py
import sys

def load_methpositions(path):
    """Read first column (positions) from methpos file.""" #methpos_file
    methpositions = []
    try:
        with open(path) as f:
            for line in f:
                parts = line.split()
                if not parts:
                    continue
                try:
                    pos = int(parts[0])
                    methpositions.append(pos)
                except ValueError:
                    # ignore malformed lines
                    continue
    except FileNotFoundError:
        print(f"ERROR: methylation positions file '{path}' not found.")
        sys.exit(1)
    return methpositions


def ascii_to_binary(text, bitwidth):
    """Convert ASCII text to binary with given bitwidth (7 or 8)."""
    fmt = f"0{bitwidth}b"
    binary_representation = ' '.join(format(ord(char), fmt) for char in text)
    no_space = ''.join(format(ord(char), fmt) for char in text)
    return binary_representation, no_space


if __name__ == "__main__":
    # Called as: python3 error_stats.py <methpos_file> <bitwidth>
    if len(sys.argv) != 3:
        print("Usage: python3 error_stats.py <methpos_file> <bitwidth 7|8>")
        sys.exit(1)

    methpos_file = sys.argv[1]
    bitwidth = int(sys.argv[2])

    if bitwidth not in (7, 8):
        print("Error: bitwidth must be 7 or 8")
        sys.exit(1)

    # 1) Load actual methylation positions from file
    mpos = load_methpositions(methpos_file)


    # 2) Get desired word from user
    x = input("Please enter your word \n")

    # 3) Convert word to binary using the chosen bitwidth
    y, z = ascii_to_binary(x, bitwidth)

    print("\nEach letter in binary:\n", y)
    print("\nDesired word in binary (no spaces):\n", z, "\n")

    # 4) Build CG sites grid (must match meth_analysis.py)
    start, end, step = 60, 912, 24
    sites = list(range(start, end + 1, step))

    # 5) Actual bits from methylation data (one per CG site)

    filtered_mpos = []     # actual methylation sites that match brick sites
    actual_bits = []       # 1 or 0 for each brick site

    for i in sites:  # goes through 60, 84, 108, ..., 900
        bit_value = 0    # default is 0 (unmethylated)

    # Check if this brick matches any methylated position
        for mp in mpos:
            if mp == i:
                bit_value = 1
                filtered_mpos.append(i)
                break

        actual_bits.append(bit_value)

    # 6) Desired bits from the word
    desired_bits = [int(b) for b in z]

    # Align lengths: we can only compare up to the shorter of the two
    n_compare = min(len(desired_bits), len(actual_bits))

    if len(desired_bits) > len(actual_bits):
        print(f"Warning: desired pattern ({len(desired_bits)} bits) "
              f"is longer than available CG sites ({len(actual_bits)}). "
              f"Only comparing first {n_compare} bits.\n")

    # 7) Compute matches and flips
    matches = 0
    flips_1_to_0 = []  # list of (index, cg_position)
    flips_0_to_1 = []  # list of (index, cg_position)

    for i in range(n_compare):
        d = desired_bits[i]
        a = actual_bits[i]
        cg_pos = sites[i]

        if d == a:
            matches += 1
        elif d == 1 and a == 0:
            flips_1_to_0.append((i, cg_pos))
        elif d == 0 and a == 1:
            flips_0_to_1.append((i, cg_pos))
        # if somehow other values appear, we ignore them (shouldn't happen)

    # 8) Brick numbers for desired pattern (like your original code)
    j = 2
    blist = []
    for bit in z:
        if bit == '1':
            blist.append(j)
        j += 1

    cg_sites_desired = []
    for idx in blist:
        cg_pos = 60 + (24 * (idx - 2))
        cg_sites_desired.append(cg_pos)

    print("Desired methylated brick numbers are:", blist, "\n")
    print("Desired methylated CG sites are:", cg_sites_desired, "\n")
    print("Actual methylated CG sites are: ",filtered_mpos,"\n")

    total_bits = len(desired_bits)
    percent_ones = (len(blist) / total_bits) * 100 if total_bits > 0 else 0.0
    print(f"Desired percentage of 1's: {percent_ones}\n")

    # 9) Report error stats
    print(f"Total positions compared: {n_compare}")
    print(f"Matches (desired == actual): {matches}")

    print(f"\n1 -> 0 flips (desired 1, actual 0): {len(flips_1_to_0)}")
    print("Positions (index, CG site):")
    for idx, pos in flips_1_to_0:
        print(f"  Bit/Brick number= {idx+1}, CG_site= {pos}")

    print(f"\n0 -> 1 flips (desired 0, actual 1): {len(flips_0_to_1)}")
    print("Positions (index, CG site):")

    for idx, pos in flips_0_to_1:
        print(f"  Bit/Brick number= {idx+1}, CG_site= {pos}")
    errorp= (((total_bits)-(matches))/total_bits)*100
    print("Error Percentage:",errorp)
