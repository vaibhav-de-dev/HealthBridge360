import random
from datetime import datetime, timedelta, timezone

from api.services.event_source_loader import load_event_sources


EVENT_DISTRIBUTION = {
    "LAB_RESULT": 2500,
    "PRESCRIPTION": 2000,
    "OUTPATIENT_VISIT": 1500,
    "PROCEDURE": 1200,
    "EMERGENCY_VISIT": 1000,
    "CARE_MANAGEMENT": 800,
    "ADMISSION": 500,
    "DISCHARGE": 500,
}


def generate_event_id(event_number):
    return f"EVT{event_number:012d}"


def generate_timestamps():
    start_date = datetime(
        2026, 1, 1, tzinfo=timezone.utc
    )

    event_timestamp = start_date + timedelta(
        seconds=random.randint(
            0,
            int(
                (
                    datetime(2026, 12, 31, tzinfo=timezone.utc)
                    - start_date
                ).total_seconds()
            )
        )
    )

    event_received_timestamp = event_timestamp + timedelta(
        seconds=random.randint(30, 3600)
    )

    return event_timestamp, event_received_timestamp


def choose_relationships(member_id, sources):
    policies = sources["member_to_policies"].get(member_id, [])
    claims = sources["member_to_claims"].get(member_id, [])

    policy_id = random.choice(policies) if policies else None
    claim = random.choice(claims) if claims else None

    claim_id = claim["claim_id"] if claim else None

    if claim and claim.get("policy_id"):
        policy_id = claim["policy_id"]

    return policy_id, claim_id


def generate_payload(event_type, policy_id, claim_id):
    if event_type == "LAB_RESULT":
        return {
            "lab_result": {
                "test_code": "LAB83036",
                "result_value": "7.2",
                "result_unit": "%",
                "facility_id": "FAC00237",
                "provider_id": "PRV005421",
                "diagnosis_code": "E11.9"
            },
            "claim": {
                "claim_id": claim_id
            },
            "policy": {
                "policy_id": policy_id
            }
        }

    if event_type == "PRESCRIPTION":
        return {
            "prescription": {
                "medication_code": "RX10452",
                "provider_id": "PRV007214",
                "facility_id": None,
                "diagnosis_code": "I10"
            },
            "claim": {
                "claim_id": claim_id
            },
            "policy": {
                "policy_id": policy_id
            }
        }

    if event_type == "OUTPATIENT_VISIT":
        return {
            "outpatient_visit": {
                "visit_type": "OUTPATIENT",
                "facility_id": "FAC00318",
                "provider_id": "PRV006532",
                "diagnosis_code": "E11.9",
                "procedure_code": "PROC1182"
            },
            "claim": {
                "claim_id": claim_id
            },
            "policy": {
                "policy_id": policy_id
            }
        }

    if event_type == "PROCEDURE":
        return {
            "procedure": {
                "procedure_code": "PROC4721",
                "facility_id": "FAC00182",
                "provider_id": "PRV003847",
                "diagnosis_code": "K21.9"
            },
            "claim": {
                "claim_id": claim_id
            },
            "policy": {
                "policy_id": policy_id
            }
        }

    if event_type == "EMERGENCY_VISIT":
        return {
            "emergency_visit": {
                "visit_type": "EMERGENCY",
                "facility_id": "FAC00109",
                "provider_id": "PRV004218",
                "diagnosis_code": "R07.9",
                "procedure_code": None
            },
            "claim": {
                "claim_id": claim_id
            },
            "policy": {
                "policy_id": policy_id
            }
        }

    if event_type == "CARE_MANAGEMENT":
        return {
            "care_management": {
                "interaction_type": "CARE_COORDINATION",
                "provider_id": "PRV002918",
                "facility_id": None,
                "diagnosis_code": "E11.9",
                "medication_code": "RX20841"
            },
            "claim": {
                "claim_id": None
            },
            "policy": {
                "policy_id": policy_id
            }
        }

    if event_type == "ADMISSION":
        return {
            "admission": {
                "admission_type": "INPATIENT",
                "facility_id": "FAC00214",
                "provider_id": "PRV008721",
                "diagnosis_code": "I10"
            },
            "claim": {
                "claim_id": claim_id
            },
            "policy": {
                "policy_id": policy_id
            }
        }

    return {
        "discharge": {
            "discharge_type": "INPATIENT",
            "facility_id": "FAC00214",
            "provider_id": "PRV008721",
            "diagnosis_code": "I10",
            "procedure_code": "PROC2045"
        },
        "claim": {
            "claim_id": claim_id
        },
        "policy": {
            "policy_id": policy_id
        }
    }


def generate_batch(start_event_number, batch_size=10000):
    sources = load_event_sources()

    event_types = []

    for event_type, count in EVENT_DISTRIBUTION.items():
        event_types.extend([event_type] * count)

    if batch_size != 10000:
        event_types = random.choices(
            list(EVENT_DISTRIBUTION.keys()),
            weights=list(EVENT_DISTRIBUTION.values()),
            k=batch_size
        )

    random.shuffle(event_types)

    events = []

    for offset, event_type in enumerate(event_types):
        event_number = start_event_number + offset

        member_id = random.choice(sources["member_ids"])

        policy_id, claim_id = choose_relationships(
            member_id,
            sources
        )

        event_timestamp, event_received_timestamp = (
            generate_timestamps()
        )

        events.append({
            "event_id": generate_event_id(event_number),
            "member_id": member_id,
            "event_type": event_type,
            "event_timestamp": event_timestamp,
            "event_received_timestamp": event_received_timestamp,
            "event_status": random.choice(
                ["REPORTED", "PROCESSED", "CORRECTED"]
            ),
            "payload": generate_payload(
                event_type,
                policy_id,
                claim_id
            ),
            "event_source": "HEALTHCARE_EVENTS_API",
            "api_version": "v1"
        })

    return events


def inject_whitespace_issues(events, injection_rate=0.015):
    total_injections = 0

    for event in events:
        if random.random() < injection_rate:
            event["member_id"] = f" {event['member_id']} "
            total_injections += 1

        if random.random() < injection_rate:
            event["event_type"] = f" {event['event_type']} "
            total_injections += 1

        if random.random() < injection_rate:
            event["event_status"] = f" {event['event_status']} "
            total_injections += 1

    return events, total_injections