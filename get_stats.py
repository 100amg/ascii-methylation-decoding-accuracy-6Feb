import statistics
import sys

def compute_stats(mfile):
    meth_values = []

    with open(mfile) as f:
        for line in f:
            pos, frac = line.split()
            pos = int(pos)
            frac = float(frac)

            if pos >= 60 and pos % 12 == 0 and frac > 15.5:
                meth_values.append(frac)

    if not meth_values:
        raise ValueError("No values passed the filters!")

    print(statistics.mean(meth_values), statistics.median(meth_values))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: get_stats.py <methylation_M.txt>")

    compute_stats(sys.argv[1])
