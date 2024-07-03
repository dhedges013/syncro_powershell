import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

syncro_domain = 'hedgesmsp'
syncro_api_key = "Tab3d28f3d8b9f53f4-889ad9baeaeba0084af02dc1a1bf6989"

fd_domain = 'hedgesmsp'
fd_api_key = 'yxHUamXLkqwZUwcL1Wlg'


def get_fd_companies(fd_domain, fd_api_key):
    """
    Retrieves all companies from Freshdesk and creates a dictionary with company names as keys and company IDs as values.
    
    Args:
        fd_domain (str): Your Freshdesk domain.
        fd_api_key (str): Your Freshdesk API key.

    Returns:
        dict: A dictionary containing company names as keys and their corresponding IDs as values.
    """
    company_dict = {}
    base_url = f'https://{fd_domain}.freshdesk.com/api/v2/companies'
    url = base_url
    headers = {
        'Content-Type': 'application/json'
    }

    while url:
        try:
            response = requests.get(url, headers=headers, auth=HTTPBasicAuth(fd_api_key, 'X'))
            response.raise_for_status()

            companies = response.json()
            for company in companies:
                company_dict[company['name']] = company['id']

            links = response.headers.get('Link')
            if links:
                url = find_next_link(links)
            else:
                url = None
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to retrieve companies from Freshdesk: {e}")
            return None

    return company_dict


def find_next_link(links):
    """
    Helper function to find the next page URL from the 'Link' header in the response.
    
    Args:
        links (str): The 'Link' header content from the HTTP response.

    Returns:
        str: The URL for the next page of results, or None if not found.
    """
    parts = links.split(',')
    for part in parts:
        section = part.split(';')
        if 'rel="next"' in section[1]:
            return section[0].strip('<>')
    return None


def get_syncro_companies(syncro_domain, syncro_api_key):
    """
    Retrieves all companies from Syncro and creates a dictionary with company names as keys and company IDs as values.
    
    Args:
        syncro_domain (str): Your Syncro domain.
        syncro_api_key (str): Your Syncro API key.

    Returns:
        dict: A dictionary containing company names as keys and their corresponding IDs as values.
    """
    url = f"https://{syncro_domain}.syncromsp.com/api/v1/customers"
    headers = {
        "accept": "application/json",
        "Authorization": syncro_api_key
    }
    page = 1
    customers_dict = {}

    while True:
        try:
            response = requests.get(url, headers=headers, params={"page": page})
            response.raise_for_status()
            data = response.json()

            customers = data["customers"]
            meta = data["meta"]

            for customer in customers:
                business_name = customer["business_name"]
                customer_id = customer["id"]
                customers_dict[business_name] = customer_id

            if page >= meta["total_pages"]:
                break
            page += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to retrieve companies from Syncro: {e}")
            return None

    return customers_dict


# Retrieve companies from both Freshdesk and Syncro
syncro_companies = get_syncro_companies(syncro_domain, syncro_api_key)
fd_companies = get_fd_companies(fd_domain, fd_api_key)

# Combine matching companies and find unmatched companies
combined_companies = {}
unmatched_fd_companies = {}
unmatched_syncro_companies = {}

for company_name, fd_id in fd_companies.items():
    if company_name in syncro_companies:
        syncro_id = syncro_companies[company_name]
        combined_companies[company_name] = [fd_id, syncro_id]
    else:
        unmatched_fd_companies[company_name] = fd_id

for company_name, syncro_id in syncro_companies.items():
    if company_name not in combined_companies:
        unmatched_syncro_companies[company_name] = syncro_id

logging.info("Combined Companies")
pprint(combined_companies)
#logging.info("Unmatched Freshdesk Companies")
#pprint(unmatched_fd_companies)
#logging.info("Unmatched Syncro Companies")
#pprint(unmatched_syncro_companies)



"""

Next I want to Build Ticket List for FD and a Ticket List for Syncro
Remove duplicates based on Subject Line + FD Ticket ID
add what remains


"""

def get_fd_tickets_per_company_id(fd_domain, fd_api_key, company_id):
    """
    Retrieves all tickets for a specific CompanyID since 2019.
    
    Args:
        domain (str): Your Freshdesk domain.
        api_key (str): Your Freshdesk API key.
        company_id (str): The CompanyID to filter tickets by.

    Returns:
        list: A list of dictionaries containing all the tickets.
    """
    base_url = f'https://{fd_domain}.freshdesk.com/api/v2/tickets'
    updated_since = '2019-01-01T00:00:00Z'
    url = f'{base_url}?include=description&company_id={company_id}&updated_since={updated_since}'
    headers = {
        'Content-Type': 'application/json'
    }
    tickets = []
    
    while url:
        try:
            response = requests.get(url, headers=headers, auth=HTTPBasicAuth(fd_api_key, 'X'))
            response.raise_for_status()

            page_tickets = response.json()
            tickets.extend(page_tickets)

            # Check if there is another page of tickets
            links = response.headers.get('Link')
            if links:
                url = find_next_link(links)
            else:
                url = None
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to retrieve tickets: {e}")
            return None

    return tickets

company_id = "153001209190"
fd_tickets = get_fd_tickets_per_company_id(fd_domain, fd_api_key, company_id)
#pprint(fd_tickets) # This returns a list object with the individual entries each ticket's data


def get_syncro_ticket_links(syncro_customer_id):
    url = f"https://hedgesmsp.syncromsp.com/api/v1/customers/{syncro_customer_id}"
    headers = {
        "accept": "application/json",
        "Authorization": "Tab3d28f3d8b9f53f4-889ad9baeaeba0084af02dc1a1bf6989"
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        ticket_links = data.get('customer', {}).get('ticket_links', [])
        return ticket_links
    else:
        print(f"Error: Unable to fetch data (Status code: {response.status_code})")
        return None

# Example usage
syncro_customer_id = "30510882"
syncro_ticket_links = get_syncro_ticket_links(syncro_customer_id)
#pprint(ticket_links)

'''
each ticket in fd

foreach ticket in fd_tickets():
    ticket_subject = ticket['subject']
    initial_issue = ticket['description_text']
    created_date = ticket['created_at']
    priority = ticket['priority']
    fd_ticket_id = ticket['id']
    ticket_subject = str(ticket_subject) + " " + str(fd_ticket_id)

    check for matching syncro ticket in ticket_link dictionary items that are in the list, see if you can find matching ticket_subject to ticket_link subject

'''


def find_matching_and_unmatched_tickets(syncro_ticket_links, fd_tickets):
    matching_tickets = []
    unmatched_tickets = []

    for ticket in fd_tickets:
        ticket_subject = ticket['subject']
        fd_ticket_id = ticket['id']
        ticket_subject_with_id = f"{ticket_subject} {fd_ticket_id}"

        match_found = False

        for syncro_ticket in syncro_ticket_links:
            syncro_subject = syncro_ticket['subject']
            if ticket_subject_with_id == syncro_subject:
                matching_tickets.append({
                    "fd_ticket_id": fd_ticket_id,
                    "fd_subject": ticket_subject,
                    "syncro_ticket_id": syncro_ticket['id'],
                    "syncro_subject": syncro_ticket['subject']
                })
                match_found = True
                break

        if not match_found:
            unmatched_tickets.append({
                "fd_ticket_id": fd_ticket_id,
                "ticket_subject": ticket_subject,
                "initial_issue": ticket['description_text'],
                "created_date": ticket['created_at'],
                "priority": ticket['priority']
            })

    return matching_tickets, unmatched_tickets

if fd_tickets and syncro_ticket_links:
    matching_tickets, unmatched_tickets = find_matching_and_unmatched_tickets(syncro_ticket_links, fd_tickets)
    print("Matching Tickets:")
    pprint(matching_tickets)
    print("\nUnmatched Tickets:")
    pprint(unmatched_tickets)
