import requests
from requests.auth import HTTPBasicAuth

domain = 'hedgesmsp'
api_key = 'yxHUamXLkqwZUwcL1Wlg'
syncro_api_key = 'Tab3d28f3d8b9f53f4-889ad9baeaeba0084af02dc1a1bf6989'

# Helper functions

def get_priority_value(priority):
    priority_map = {
        0: "0 Urgent",
        1: "1 High",
        2: "2 Normal",
        3: "3 Low"
    }
    return priority_map.get(priority, "Invalid Priority")

def create_syncro_ticket(customer_id, ticket_subject, priority, initial_issue, created_date):
    syncro_priority = get_priority_value(priority)
    ticket_url = f"https://{domain}.syncromsp.com/api/v1/tickets"

    ticket_data = {
        "customer_id": customer_id,
        "subject": ticket_subject,
        "created_at": created_date,
        "status": "Resolved",
        "priority": syncro_priority,
        "comments_attributes": [
            {
                "subject": "API Import Notes",
                "created_at": created_date,
                "body": initial_issue,
                "hidden": True,
                "do_not_email": True
            }
        ]
    }

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {syncro_api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(ticket_url, headers=headers, json=ticket_data)
        response.raise_for_status()  # Raise an exception for bad responses (4xx or 5xx)
        print(f"Ticket created successfully in Syncro MSP. Subject: {ticket_subject}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to create ticket in Syncro MSP: {e}")

def get_freshdesk_tickets(customer_id):
    base_url = f'https://{domain}.freshdesk.com/api/v2/tickets'
    updated_since = '2019-01-01T00:00:00Z'
    url = f'{base_url}?include=description&company_id={customer_id}&updated_since={updated_since}'

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers, auth=HTTPBasicAuth(api_key, 'X'))
        response.raise_for_status()  # Raise an exception for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Failed to retrieve Freshdesk tickets: {e}')
        return None

def find_syncro_customer_id(query):
    url = f"https://{domain}.syncromsp.com/api/v1/customers/autocomplete"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {syncro_api_key}"
    }
    params = {
        "query": query
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for bad responses (4xx or 5xx)
        data = response.json()
        
        if "customers" in data and len(data["customers"]) > 0:
            return data["customers"][0]["id"]
        else:
            print("No customers found.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching customer data from Syncro: {e}")
        return None

# Main execution

def main():
    customer_id = "153001209190"
    query = "John Smith Smithing"

    syncro_customer_id = find_syncro_customer_id(query)
    if syncro_customer_id:
        tickets = get_freshdesk_tickets(customer_id)
        if tickets:
            for ticket in tickets:
                ticket_subject = ticket['subject']
                initial_issue = ticket['description_text']
                created_date = ticket['created_at']
                priority = ticket['priority']
                fd_ticket_id = ticket['id']

                create_syncro_ticket(syncro_customer_id, ticket_subject, priority, initial_issue, created_date)

                print(f"Ticket Subject: {ticket_subject}")
                print(f"Initial Issue: {initial_issue}")
                print(f"Created Date: {created_date}")
                print(f"Priority: {priority}")
                print(f"Freshdesk Ticket ID: {fd_ticket_id}")
                print("-" * 20)  # Separator between tickets
    else:
        print("Failed to find Syncro customer ID.")

if __name__ == "__main__":
    main()
