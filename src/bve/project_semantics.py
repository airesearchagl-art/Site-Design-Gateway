"""Small v0.2 identity check, called only after the canonical Project schema."""


def unique_far_cap_ids(project: dict) -> bool:
    if project["schemaVersion"] == "0.1":
        return True
    ids = [entry["id"] for entry in project["zoning"]["additionalFloorAreaRatioCaps"]]
    return len(ids) == len(set(ids))
