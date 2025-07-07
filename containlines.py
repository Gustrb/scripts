import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 containlines.py <file1> <line2>")
        return

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    lines = set()

    with open(file1, "r") as f1:
        lines.update([line.strip() for line in f1])

    with open(file2, "r") as f2:
        for line in f2:
            line = line.strip()
            if line in lines:
                print(line)

if __name__ == "__main__":
    main()
