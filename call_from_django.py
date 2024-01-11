import json
import sys

from Dynamic import assign_patients


def call_from_django(file, last_day):
    """
    Helper function for retrieving a patient assignment from
    an external source, e.g. django.

    :param file: filename without extension or path prefixes
    :type file: str
    :param last_day: last day for which to find an assignment
    :type last_day: int
    """
    with open(f"{file}.json") as f:
        input_data = json.load(f)

    rooms = input_data["rooms"]
    patients = input_data["patients"]
    current_assignment = input_data["currentPatientAssignment"]

    result = assign_patients(patients, 0, last_day, rooms, current_assignment)

    with open(f"Results/{file}_out.json", "w", encoding="utf-8") as out:
        out.write(json.dumps(result, indent=4))


if __name__ == "__main__":
    file = sys.argv[1] if len(sys.argv) > 1 else "0"
    last_day = int(sys.argv[2]) if len(sys.argv) > 2 else 364

    call_from_django(f"instances/{file}", last_day)
