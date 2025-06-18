import re
import json
import pythunder.types
import pythunder.sfit
import pythunder.enums
import pythunder.system as s
import pythunder.instrument


if __name__ == "__main__":
    pattern = re.compile("sfit\\.future\\.([a-zA-z]+)\\d+$")
    names = set()
    instruments = s.load_instrument_information_from_file("/thunder-data/instruments.config")
    for name in instruments.keys():
        m = pattern.match(name)
        if m:
            names.add(m[1])
    config = []
    for n in names:
        if n is not None:
            config.append({"enable":0,"sfit":n})
    print(json.dumps(config, indent=4))

    