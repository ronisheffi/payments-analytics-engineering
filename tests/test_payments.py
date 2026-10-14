import csv
from datetime import datetime
from pathlib import Path


# Location of the generated CSV files
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_csv(filename):
    """Load a CSV file as a list of dictionaries."""
    with open(DATA_DIR / filename, newline="") as file:
        return list(csv.DictReader(file))


def parse_date(value):
    """Convert a date string into a datetime object."""
    return datetime.fromisoformat(value)


def test_payment_request_relationships():
    """Verify that linked payments reference existing requests."""
    requests = load_csv("payment_requests.csv")
    payments = load_csv("payments.csv")

    request_ids = {
        request["payment_request_id"]
        for request in requests
    }

    for payment in payments:
        request_id = payment["payment_request_id"]

        # Legacy payments are allowed to have no request
        if request_id:
            assert request_id in request_ids, (
                f"Payment {payment['payment_id']} references "
                f"missing request {request_id}"
            )


def test_payment_dates():
    """Verify payment dates and their chronological order."""
    requests = load_csv("payment_requests.csv")
    payments = load_csv("payments.csv")

    requests_by_id = {
        request["payment_request_id"]: request
        for request in requests
    }

    for payment in payments:
        payment_id = payment["payment_id"]
        created_at = parse_date(payment["create_at"])
        updated_at = parse_date(payment["update_at"])

        # A payment cannot be updated before it was created
        assert updated_at >= created_at, (
            f"Payment {payment_id}: update_at is before create_at"
        )

        # Only successful payments should have paid_at
        if payment["paid_at"]:
            paid_at = parse_date(payment["paid_at"])

            assert paid_at >= created_at, (
                f"Payment {payment_id}: paid_at is before create_at"
            )

            assert updated_at >= paid_at, (
                f"Payment {payment_id}: update_at is before paid_at"
            )

            assert payment["payment_status"] == "paid", (
                f"Payment {payment_id}: paid_at exists but status is not paid"
            )
        else:
            assert payment["payment_status"] != "paid", (
                f"Payment {payment_id}: paid payment has no paid_at"
            )

        # A linked payment must be created after its request
        request_id = payment["payment_request_id"]

        if request_id:
            assert request_id in requests_by_id, (
                f"Payment {payment_id}: request {request_id} not found"
            )

            request = requests_by_id[request_id]
            request_created_at = parse_date(request["create_at"])

            assert created_at >= request_created_at, (
                f"Payment {payment_id} was created before "
                f"request {request_id}"
            )


def test_legacy_payments():
    """Verify that legacy payments have no request and predate 2025."""
    payments = load_csv("payments.csv")

    legacy_payments = [
        payment
        for payment in payments
        if not payment["payment_request_id"]
    ]

    assert len(legacy_payments) > 0, (
        "No legacy payments were generated"
    )

    for payment in legacy_payments:
        payment_id = payment["payment_id"]

        assert parse_date(payment["create_at"]).year < 2025, (
            f"Legacy payment {payment_id} was created in 2025 or later"
        )

        assert payment["selected_item_name"], (
            f"Legacy payment {payment_id} has no selected item name"
        )


def test_payment_business_relationships():
    """Verify that payments belong to existing businesses."""
    businesses = load_csv("businesses.csv")
    payments = load_csv("payments.csv")

    businesses_by_id = {
        business["business_id"]: business
        for business in businesses
    }

    for payment in payments:
        payment_id = payment["payment_id"]
        business_id = payment["business_id"]

        assert business_id in businesses_by_id, (
            f"Payment {payment_id}: business {business_id} not found"
        )

        business = businesses_by_id[business_id]

        # The business must exist before the payment
        assert parse_date(payment["create_at"]) >= parse_date(
            business["create_at"]
        ), (
            f"Payment {payment_id} was created before "
            f"business {business_id}"
        )

def test_payment_request_entities():
    """Verify that payment requests reference valid business entities."""
    requests = load_csv("payment_requests.csv")
    meetings = load_csv("meetings.csv")
    events = load_csv("events.csv")
    clients = load_csv("clients.csv")
    products = load_csv("products.csv")
    services = load_csv("services.csv")

    for request in requests:
        request_id = request["payment_request_id"]
        entity_type = request["entity_type"]
        entity_id = request["entity_id"]

        # Find the referenced meeting or event
        entity = None

        if entity_type == "meeting":
            for meeting in meetings:
                if meeting["meeting_id"] == entity_id:
                    entity = meeting
                    break

        elif entity_type == "event":
            for event in events:
                if event["event_id"] == entity_id:
                    entity = event
                    break

        elif entity_type == "product":
            for product in products:
                if product["product_id"] == entity_id:
                    entity = product
                    break

        elif entity_type == "service":
            for service in services:
                if service["service_id"] == entity_id:
                    entity = service
                    break            

        else:
            raise AssertionError(
                f"Request {request_id}: unknown entity type {entity_type}"
            )

        assert entity is not None, (
            f"Request {request_id}: entity {entity_id} not found"
        )

        assert request["business_id"] == entity["business_id"], (
            f"Request {request_id}: business does not match entity"
        )

        # Find the client linked to the request
        client = None

        for c in clients:
            if c["client_id"] == request["client_id"]:
                client = c
                break

        assert client is not None, (
            f"Request {request_id}: client not found"
        )

        assert client["business_id"] == request["business_id"], (
            f"Request {request_id}: client belongs to another business"
        )

        # Meetings must reference their own client
        if entity_type == "meeting":
            assert entity["client_id"] == request["client_id"], (
                f"Request {request_id}: meeting client does not match"
            )

        # Request must be created after its entity and client
        request_date = parse_date(request["create_at"])

        assert request_date >= parse_date(entity["create_at"]), (
            f"Request {request_id}: created before entity"
        )

        assert request_date >= parse_date(client["create_at"]), (
            f"Request {request_id}: created before client"
        )
        if entity_type == "product" or entity_type == "service":
            assert request_date >= parse_date("2025-01-01T00:00:00+00:00"), (
                f"Request {request_id}: product/service request before 2025"
            )


def test_no_duplicate_meeting_or_event_requests():
    requests = load_csv("payment_requests.csv")

    used_entities = set()

    for request in requests:
        entity_type = request["entity_type"]

        if entity_type == "meeting" or entity_type == "event":
            entity_key = (
                entity_type,
                request["entity_id"]
            )

            assert entity_key not in used_entities, (
                f"Duplicate payment request for {entity_key}"
            )

            used_entities.add(entity_key)
