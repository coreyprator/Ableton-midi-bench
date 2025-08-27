import argparse
import json
import os
from .midi_bench_gui import DEFAULT_CONFIG

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../../midi_bench_gui_config.json')
CONFIG_PATH = os.path.abspath(CONFIG_PATH)

def print_config():
    print(f"Config path: {CONFIG_PATH}")
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            print(json.dumps(json.load(f), indent=2))
    else:
        print("No config file found.")

def reset_config():
    with open(CONFIG_PATH, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    print(f"Restored defaults to {CONFIG_PATH}")

def main():
    parser = argparse.ArgumentParser(description="MIDI Bench Config Tool")
    parser.add_argument('--print', action='store_true', help='Show config path and JSON')
    parser.add_argument('--reset', action='store_true', help='Restore defaults and overwrite config file')
    args = parser.parse_args()
    if args.print:
        print_config()
    elif args.reset:
        reset_config()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
