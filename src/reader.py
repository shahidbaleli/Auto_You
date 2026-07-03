import json
import sys

SCRIPTS_FILE = "scripts/scripts.json"


class ScriptReader:
    def get_next(self) -> dict:
        with open(SCRIPTS_FILE, "r") as f:
            scripts = json.load(f)

        for script in scripts:
            if not script.get("used", False):
                script["used"] = True
                with open(SCRIPTS_FILE, "w") as f:
                    json.dump(scripts, f, indent=2)
                return script

        total = len(scripts)
        print(f"All {total} scripts used. Generate fresh ones in {SCRIPTS_FILE}")
        sys.exit(0)
