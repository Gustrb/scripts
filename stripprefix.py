import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 stripprefix.py <file> <prefix>")
        return

    filepath = sys.argv[1]
    prefix = sys.argv[2]

    with open(filepath, "r") as file:
        for line in file:
            print(line.replace(prefix, "").strip())

if __name__ == "__main__":
    main()
