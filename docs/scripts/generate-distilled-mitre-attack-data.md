# generate_distilled_mitre_attack_data.py

`generate_distilled_mitre_attack_data.py` downloads the official MITRE ATT&CK dataset and
distills it into a compact JSON file the server uses to describe techniques. It exists so
the repository does not have to vendor the large upstream STIX bundle: run the script to
(re)generate the local data file when you need it or when you want to refresh it against
the latest upstream data.

## Running the script

Run it from the repository root. It fetches data over the network, so an internet
connection is required:

```
uv run python scripts/generate_distilled_mitre_attack_data.py
```

## What it does

1. Fetches the Enterprise ATT&CK STIX 2.1 bundle from the MITRE `cti` GitHub repository.
2. Walks every non-deprecated `attack-pattern` (technique) object and keeps only the
   fields the server needs: the MITRE ID (for example `T1005`), name, the first paragraph
   of the description, associated tactics, the reference URL, and supported platforms.
3. Writes the distilled result to `data/server/mitre_attack_data.json`, creating the
   `data/server/` directory if it does not already exist.

On success it prints the number of techniques written. If the download fails (for example
a non-200 response from GitHub), it reports the failure and writes nothing.
