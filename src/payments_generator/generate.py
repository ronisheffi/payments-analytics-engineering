from datetime import datetime, timezone, timedelta
import csv



def generate():
    business_names = [
    "Madrid Wellness Studio",
    "Barcelona Fitness Club",
    "Valencia Beauty Salon",
    "Sevilla Yoga Center",
    "Bilbao Coffee House",
    "Malaga Dance Academy",
    "Granada Hair Studio",
    "Alicante Language School",
    "Toledo Photography Studio",
    "Zaragoza Pilates Club",
]
    business_categories = [
    ("WELLNESS", "Health and wellness services"),
    ("FITNESS", "Fitness and sports"),
    ("BEAUTY", "Beauty services"),
    ("WELLNESS", "Health and wellness services"),
    ("FOOD", "Food and beverages"),
    ("EDUCATION", "Dance education"),
    ("BEAUTY", "Beauty services"),
    ("EDUCATION", "Language education"),
    ("CREATIVE", "Photography services"),
    ("FITNESS", "Fitness and sports"),
]
    # Generate businesses

    businesses = []

    for i in range(1, 11):
        created_at = datetime(2024, 1, 15, tzinfo=timezone.utc) + timedelta(days=i * 7)
        category_code, category_description = business_categories[i - 1]

        business = {
            "business_id": f"BIZ_{i:04d}",
            "business_name": business_names[i - 1],
            "country_code": "ES",
            "identity_group_code": category_code,
            "identity_group_description": category_description,
            "status": "active",
            "create_at": created_at,
            "update_at": created_at,
            "delete_at": None,
        }

        businesses.append(business)

    # Generate clients

        clients = []

    for business in businesses:
        for i in range(1, 6):
            client = {
                "client_id": f"CLI_{len(clients) + 1:04d}",
                "business_id": business["business_id"],
                "client_name": f"Client {i} of {business['business_name']}",
                "country_code": "ES",
                "identity_group_code": "INDIVIDUAL",
                "identity_group_description": "Individual",
                "status": "active",
                "create_at": business["create_at"] + timedelta(days=i),
                "update_at": business["create_at"] + timedelta(days=i),
                "delete_at": None,
            }
            clients.append(client)

    # Generate meetings
    meetings = []

    meeting_names = [
        "Personal Consultation",
        "Wellness Appointment",
        "Private Coaching",
        "Photography Session",
        "Business Strategy Meeting",
    ]

    for i in range(20):
        client = clients[i]
        business_id = client["business_id"]

        created_at = client["create_at"] + timedelta(days=5)

        meeting = {
            "meeting_id": f"MTG_{i + 1:04d}",
            "business_id": business_id,
            "client_id": client["client_id"],
            "meeting_name": meeting_names[i % len(meeting_names)],
            "description": "Private appointment with a client",
            "scheduled_at": created_at + timedelta(days=7),
            "create_at": created_at,
            "update_at": created_at,
            "delete_at": None,
        }

        meetings.append(meeting)

    # Generate events
    events = []

    event_names = [
        "Summer Wellness Retreat",
        "Business Networking Evening",
        "Photography Masterclass",
        "Community Fitness Day",
        "Creative Workshop",
        "Yoga Weekend",
        "Entrepreneurship Conference",
        "Music & Art Festival",
        "Personal Development Seminar",
        "Healthy Living Workshop",
    ]

    for i, business in enumerate(businesses):
        created_at = business["create_at"] + timedelta(days=15)

        event = {
            "event_id": f"EVT_{i + 1:04d}",
            "business_id": business["business_id"],
            "event_name": event_names[i],
            "description": f"Group event: {event_names[i]}",
            "event_at": created_at + timedelta(days=30),
            "create_at": created_at,
            "update_at": created_at,
            "delete_at": None,
        }

        events.append(event)

       # Generate products
    products = []

    product_names = [
        "Wellness Starter Kit",
        "Premium Skincare Set",
        "Photography Print",
        "Fitness Accessories Pack",
        "Handmade Gift Box",
        "Yoga Equipment Set",
        "Business Planner",
        "Art Print Collection",
        "Natural Body Lotion",
        "Healthy Snack Box",
    ]

    for i in range(20):
        business = businesses[i % len(businesses)]

        created_at = business["create_at"] + timedelta(days=3)

        product = {
            "product_id": f"PROD_{i + 1:04d}",
            "business_id": business["business_id"],
            "product_name": product_names[i % len(product_names)],
            "description": f"Product: {product_names[i % len(product_names)]}",
            "price": 25 + (i % 5) * 15,
            "currency": "EUR",
            "create_at": created_at,
            "update_at": created_at,
            "delete_at": None,
        }

        products.append(product)

 # Generate services
    services = []

    service_names = [
        "Personal Training",
        "Business Consultation",
        "Photography Session",
        "Yoga Private Lesson",
        "Skin Care Treatment",
        "Career Coaching",
        "Graphic Design",
        "Nutrition Consultation",
        "Massage Therapy",
        "Language Lesson",
    ]

    for i in range(20):
        business = businesses[i % len(businesses)]

        created_at = business["create_at"] + timedelta(days=4)

        service = {
            "service_id": f"SRV_{i + 1:04d}",
            "business_id": business["business_id"],
            "service_name": service_names[i % len(service_names)],
            "description": f"Service: {service_names[i % len(service_names)]}",
            "price": 60 + (i % 5) * 20,
            "currency": "EUR",
            "create_at": created_at,
            "update_at": created_at,
            "delete_at": None,
        }

        services.append(service)

    # Generate POS carts
    carts = []

    for i in range(2):
        business = businesses[i]

        created_at = datetime(
            2025, 3, 1, tzinfo=timezone.utc
        ) + timedelta(days=i * 7)

        cart = {
            "cart_id": f"CART_{i + 1:04d}",
            "business_id": business["business_id"],
            "is_sale": 1,
            "create_at": created_at,
            "update_at": created_at,
            "delete_at": None,
        }

        carts.append(cart)

    print(f"Carts created: {len(carts)}")

    # Generate POS order items
    order_items = []

    for cart in carts:

        # Find a product belonging to the cart's business
        product = None

        for p in products:
            if p["business_id"] == cart["business_id"]:
                product = p
                break

        # Find a service belonging to the cart's business
        service = None

        for s in services:
            if s["business_id"] == cart["business_id"]:
                service = s
                break

        # Create one order item for the product
        product_item = {
            "order_item_id": f"OI_{len(order_items) + 1:04d}",
            "cart_id": cart["cart_id"],
            "business_id": cart["business_id"],
            "item_type": "s",
            "entity_type": "product",
            "entity_id": product["product_id"],
            "amount": product["price"],
            "currency": product["currency"],
            "create_at": cart["create_at"],
            "update_at": cart["create_at"],
            "delete_at": None,
        }

        order_items.append(product_item)

        # Create one order item for the service
        service_item = {
            "order_item_id": f"OI_{len(order_items) + 1:04d}",
            "cart_id": cart["cart_id"],
            "business_id": cart["business_id"],
            "item_type": "s",
            "entity_type": "service",
            "entity_id": service["service_id"],
            "amount": service["price"],
            "currency": service["currency"],
            "create_at": cart["create_at"],
            "update_at": cart["create_at"],
            "delete_at": None,
        }

        order_items.append(service_item)

    print(f"Order items created: {len(order_items)}")

    # Generate direct payment requests
    payment_requests = []

    # Each meeting gets at most one payment request
    # Each event gets at most one payment request
    # Products and services can be requested multiple times

    request_entities = []

    for meeting in meetings:
        request_entities.append(("meeting", meeting))

    for event in events:
        request_entities.append(("event", event))

    for product in products[:10]:
        request_entities.append(("product", product))

    for service in services[:10]:
        request_entities.append(("service", service))

    for i, (entity_type, entity) in enumerate(request_entities):

        if entity_type == "meeting":
            entity_id = entity["meeting_id"]

        elif entity_type == "event":
            entity_id = entity["event_id"]

        elif entity_type == "product":
            entity_id = entity["product_id"]

        else:
            entity_id = entity["service_id"]

        # Find the matching client
        client = None

        for c in clients:
            if entity_type == "meeting":
                if c["client_id"] == entity["client_id"]:
                    client = c
                    break
            else:
                if c["business_id"] == entity["business_id"]:
                    client = c
                    break

        # Request must be created after the entity and client
        created_at = max(
            entity["create_at"],
            client["create_at"]
        ) + timedelta(days=2)

        # Direct product/service requests start in 2025
        if entity_type in ("product", "service"):
            created_at = max(
                created_at,
                datetime(2025, 1, 1, tzinfo=timezone.utc)
            )

        request = {
            "payment_request_id": f"PR_{i + 1:04d}",
            "business_id": entity["business_id"],
            "client_id": client["client_id"],
            "entity_type": entity_type,
            "entity_id": entity_id,
            "requested_amount": 100 + i * 10,
            "currency": "EUR",
            "request_status": "unpaid",
            "create_at": created_at,
            "update_at": created_at,
            "delete_at": None,
        }

        payment_requests.append(request)

    # Generate POS payment requests
    for cart in carts:

        # Calculate the total amount of the cart
        total_amount = 0

        for item in order_items:
            if item["cart_id"] == cart["cart_id"]:
                total_amount += item["amount"]

        # Find a client from the same business
        client = None

        for c in clients:
            if c["business_id"] == cart["business_id"]:
                client = c
                break

        created_at = cart["create_at"] + timedelta(minutes=5)

        request = {
            "payment_request_id": f"PR_{len(payment_requests) + 1:04d}",
            "business_id": cart["business_id"],
            "client_id": client["client_id"],
            "entity_type": "cart",
            "entity_id": cart["cart_id"],
            "requested_amount": total_amount,
            "currency": "EUR",
            "request_status": "unpaid",
            "create_at": created_at,
            "update_at": created_at,
            "delete_at": None,
        }

        payment_requests.append(request)

    print(f"Payment requests created: {len(payment_requests)}")


    payments = []

    # Payments linked to payment requests
    for i, request in enumerate(payment_requests):

        # Some requests have no payment attempts
        if i % 4 == 0 and request["entity_type"] != "cart":
            continue

        created_at = request["create_at"] + timedelta(days=2)


        paid_at = created_at + timedelta(minutes=5)

        payment = {
            "payment_id": f"PAY_{i + 1:04d}",
            "payment_request_id": request["payment_request_id"],
            "business_id": request["business_id"],
            "amount": request["requested_amount"],
            "currency": request["currency"],
            "payment_status": "paid",
            "selected_item_name": None,
            "create_at": created_at,
            "update_at": paid_at,
            "delete_at": None,
            "paid_at": paid_at,
        }

        payments.append(payment)

        # Update the payment request status
        request["request_status"] = "paid"

        request["update_at"] = payment["update_at"]

    # Legacy payments without payment requests
    legacy_items = [
        "Yoga Session",
        "Hair Treatment",
        "Photography Package",
        "Language Course",
        "Fitness Training",
    ]

    for i, item_name in enumerate(legacy_items):

        created_at = datetime(
            2024, 6, 1, tzinfo=timezone.utc
        ) + timedelta(days=i * 14)

        paid_at = created_at + timedelta(minutes=5)

        payment = {
            "payment_id": f"LEG_{i + 1:04d}",
            "payment_request_id": None,
            "business_id": businesses[i]["business_id"],
            "amount": 80 + i * 20,
            "currency": "EUR",
            "payment_status": "paid",
            "selected_item_name": item_name,
            "create_at": created_at,
            "update_at": paid_at,
            "delete_at": None,
            "paid_at": paid_at,
        }

        payments.append(payment)



    
    with open("data/businesses.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=businesses[0].keys())
        writer.writeheader()
        writer.writerows(businesses)
    with open("data/clients.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=clients[0].keys())
        writer.writeheader()
        writer.writerows(clients)
    with open("data/payment_requests.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=payment_requests[0].keys())
        writer.writeheader()
        writer.writerows(payment_requests)
    with open("data/payments.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=payments[0].keys())
        writer.writeheader()
        writer.writerows(payments)
    with open("data/meetings.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=meetings[0].keys())
        writer.writeheader()
        writer.writerows(meetings)
    with open("data/events.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=events[0].keys())
        writer.writeheader()
        writer.writerows(events)
    with open("data/products.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=products[0].keys())
        writer.writeheader()
        writer.writerows(products)
    with open("data/services.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=services[0].keys())
        writer.writeheader()
        writer.writerows(services)
    with open("data/carts.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=carts[0].keys())
        writer.writeheader()
        writer.writerows(carts)
    with open("data/order_items.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=order_items[0].keys())
        writer.writeheader()
        writer.writerows(order_items)


if __name__ == "__main__":
    generate()