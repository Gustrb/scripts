import sys
import json

def main():
    if len(sys.argv) != 3:
        print("Usage: pluck <file> <key>")
        return

    keys = sys.argv[2].split(".")
    filepath = sys.argv[1]
    with open(filepath, "r") as file:
        data = json.load(file)
        if isinstance(data, list):
            for k in data:
                tmp = k
                for key in keys:
                    tmp = tmp[key]

                print(tmp)
        else:
            tmp = data
            for key in keys:
                tmp = tmp[key]
            print(tmp)

if __name__ == "__main__":
    main()
