import json

import requests

# The official raw STIX data from MITRE's GitHub
MITRE_STIX_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"


def main():
    print("[*] Fetching MITRE ATT&CK data...")
    response = requests.get(MITRE_STIX_URL)
    data = response.json()

    distilled = {}

    # Assume data is in STIX 2.1 JSON format
    for obj in data.get("objects", []):
        # We only care about actual 'attack-pattern' objects (Techniques)
        if obj.get("type") == "attack-pattern" and not obj.get("x_mitre_deprecated"):
            # Find the actual MITRE ID (e.g., T1005)
            external_refs = obj.get("external_references", [])
            mitre_id = next(
                (
                    ref["external_id"]
                    for ref in external_refs
                    if ref.get("source_name") == "mitre-attack"
                ),
                None,
            )

            if mitre_id:
                distilled[mitre_id] = {
                    "name": obj.get("name"),
                    "description": obj.get("description", "").split("\n")[
                        0
                    ],  # Only first paragraph
                    "tactics": [
                        phase.get("phase_name")
                        for phase in obj.get("kill_chain_phases", [])
                    ],
                    "url": next(
                        (
                            ref.get("url")
                            for ref in external_refs
                            if ref.get("source_name") == "mitre-attack"
                        ),
                        "",
                    ),
                    "platforms": obj.get("x_mitre_platforms", []),
                }

    with open("../data/server/mitre_attack_data.json", "w") as f:
        json.dump(distilled, f, indent=4)
    print(
        f"[+] Done! Created distilled MITRE ATT&CK data JSON file for {len(distilled)} techniques at data/server/mitre_attack_data.json."
    )


if __name__ == "__main__":
    main()
