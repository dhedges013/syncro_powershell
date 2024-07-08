import requests
from requests.auth import HTTPBasicAuth
import pprint
from pprint import pprint
import json

import logging
import os
from datetime import datetime

####################################################################################################
# Section 0
#### Logging Configuration and API
####################################################################################################

log_dir = r'c:\temp\logs'


if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Create the log file name with the current date
log_filename = os.path.join(log_dir, f'freshdesk_import_{datetime.now().strftime("%Y-%m-%d")}.txt')


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_filename,
    filemode='a'
)

print(f"Log File Path: {log_dir} ")
syncro_domain = 'hedgesmsp'
syncro_api_key = "Tab3d28f3d8b9f53f4-889ad9baeaeba0084af02dc1a1bf6989"

fd_domain = 'hedgesmsp'
fd_api_key = 'yxHUamXLkqwZUwcL1Wlg'


####################################################################################################
####### Section 1
#   create List of Companies that match or dont match between Freshdesk and Syncro
#   
#   get_fd_companies
#   find_next_link -----> This is used in get_fd_companies and get_fd_tickets
#   get_syncro_companies
#
#   match_companies -----> Returns 3 lists: combined_companies, unmatched_fd_companies, unmatched_syncro_companies
#
#   End Result of Section 1 is you have 3 lists of combined and unmatched_fd and unmatched_syncro companies
####################################################################################################

def get_fd_companies(fd_domain, fd_api_key):
    """
    Retrieves all companies from Freshdesk and creates a dictionary with company names as keys and company IDs as values.
    
    Args:
        fd_domain (str): Your Freshdesk domain.
        fd_api_key (str): Your Freshdesk API key.

    Returns:
        dict: A dictionary containing company names as keys and their corresponding IDs as values.
    """


    logging.info("Starting to retrieve companies from Freshdesk.")

    company_dict = {}
    base_url = f'https://{fd_domain}.freshdesk.com/api/v2/companies'
    url = base_url
    headers = {
        'Content-Type': 'application/json'
    }
    total_companies_retrieved = 0
    while url:
        try:
            logging.info(f"Requesting URL: {url}")
            response = requests.get(url, headers=headers, auth=HTTPBasicAuth(fd_api_key, 'X'))
            response.raise_for_status()

            companies = response.json()
            total_companies_retrieved += len(companies)
            logging.info(f"Retrieved {len(companies)} companies, total retrieved so far: {total_companies_retrieved}.")


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
        
    logging.info(f"Total companies retrieved: {total_companies_retrieved}")
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
    logging.info("Starting to retrieve companies from Syncro.")

    url = f"https://{syncro_domain}.syncromsp.com/api/v1/customers"
    headers = {
        "accept": "application/json",
        "Authorization": syncro_api_key
    }
    page = 1
    customers_dict = {}
    total_companies_retrieved = 0

    while True:
        try:
            logging.info(f"Requesting customers page {page} from Syncro. Total retrieved so far: {total_companies_retrieved}.")
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
    logging.info(f"Successfully retrieved {total_companies_retrieved} companies from Syncro.")
    return customers_dict


def match_companies():
    logging.info("Starting company matching process.")

    # Retrieve companies from both Freshdesk and Syncro
    logging.info("From match_companies function: Retrieving companies from Syncro.")
    syncro_companies = get_syncro_companies(syncro_domain, syncro_api_key)
    logging.info("From match_companies function: Retrieving companies from Freshdesk.")
    fd_companies = get_fd_companies(fd_domain, fd_api_key)

    # Combine matching companies and find unmatched companies
    combined_companies = {}
    unmatched_fd_companies = {}
    unmatched_syncro_companies = {}


    for company_name, fd_id in fd_companies.items():
        logging.debug(f"Processing Freshdesk company: {company_name}")        
        if company_name in syncro_companies:
            
            syncro_id = syncro_companies[company_name]
            combined_companies[company_name] = [fd_id, syncro_id]
        else:
            unmatched_fd_companies[company_name] = fd_id

    for company_name, syncro_id in syncro_companies.items():
        logging.debug(f"Checking Syncro company: {company_name}")
        if company_name not in combined_companies:
            unmatched_syncro_companies[company_name] = syncro_id

    logging.info("Matching process completed.")
    # File paths for the output files
    combined_companies_file_path = os.path.join(log_dir, 'combined_companies.txt')
    unmatched_fd_file_path = os.path.join(log_dir, 'unmatched_fd_companies.txt')
    unmatched_syncro_file_path = os.path.join(log_dir, 'unmatched_syncro_companies.txt')

    # Dump combined companies into a file
    with open(combined_companies_file_path, 'w') as combined_file:
        json.dump(combined_companies, combined_file, indent=4)
    
    # Dump unmatched Freshdesk companies into a file
    with open(unmatched_fd_file_path, 'w') as fd_file:
        json.dump(unmatched_fd_companies, fd_file, indent=4)
    
    # Dump unmatched Syncro companies into a file
    with open(unmatched_syncro_file_path, 'w') as syncro_file:
        json.dump(unmatched_syncro_companies, syncro_file, indent=4)

    logging.info("Combined Companies, Unmatched Freshdesk Companies, and Unmatched Syncro Companies written to respective files.")

    return combined_companies, unmatched_fd_companies, unmatched_syncro_companies


"""
Section 2
Next I want to Build Ticket List for FD and a Ticket List for Syncro
Remove duplicates based on Subject Line + FD Ticket ID
add what remains

Functions:

get_fd_tickets_per_company_id
get_syncro_ticket_links_per_company_id
find_duplicate_and_new_tickets


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
            print(f"Failed to retrieve tickets: {e}")
            return None

    return tickets

def get_syncro_ticket_links_per_company_id(syncro_customer_id):
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

def find_duplicate_and_new_tickets(syncro_ticket_links, fd_tickets):
    '''
    List of dictionaries that hold individual Ticket Data is passed into this function
    The Lists are from GET API calls against the company IDs

    The Ticket Number in Freshdesk will be used to look for duplicates either in the Syncro Ticket Number or in the Subject
    
    the Syncro Ticket Data List looks like:
    
    "ticket_links": [
      {
        "id": 83450356,
        "number": 50,
        "status": "Resolved",
        "subject": "service Issue 50"
      },

    The Freshdesk Ticket Data List (example doesnt show all field) looks like:
    [
        {'associated_tickets_count': None,
        'company_id': 153001209190,
        'created_at': '2024-07-03T13:28:11Z',
        'description': '<div style="font-family:-apple-system, BlinkMacSystemFont, '
                        'Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif; '
                        'font-size:14px"><div dir="ltr">Printer is an HP Printer 401m '
                        'and it has stop working</div></div>',
        'description_text': 'Printer is an HP Printer 401m and it has stop working',
        'due_by': '2024-07-05T13:28:11Z',
        'priority': 2,
        'source': 3,
        'spam': False,
        'status': 2,
        'subject': 'Printer Jam',
        'type': 'Incident',
        'updated_at': '2024-07-05T16:12:30Z'}
    ]
    
    
    
    
    '''
    # Print number of matched and unmatched tickets
    logging.info("Starting Ticket Comparsion and Matching")
    logging.info(f"Total Number of Syncro Tickets: {len(syncro_ticket_links)}")
    logging.info(f"Total Number of Freshdesk Tickets: {len(fd_tickets)}")

    matching_tickets = []
    unmatched_tickets = []

    for ticket in fd_tickets:
        
        ticket_subject = ticket['subject']
        fd_ticket_id = ticket['id']
        ticket_subject = f"{ticket_subject} {fd_ticket_id}"

        match_found = False

        for syncro_ticket in syncro_ticket_links:
            syncro_subject = syncro_ticket['subject']
            if ticket_subject == syncro_subject:
                matching_tickets.append({
                    "fd_ticket_id": fd_ticket_id,
                    "fd_subject": ticket_subject,
                    "syncro_ticket_id": syncro_ticket['id'],
                    "syncro_subject": syncro_ticket['subject']
                })
                
                logging.info(f"Match found for Freshdesk ticket {fd_ticket_id} with Syncro ticket {syncro_ticket['id']}")
                break

        if not match_found:
            unmatched_tickets.append({
                
                "fd_ticket_id": fd_ticket_id,
                "ticket_subject": ticket_subject,
                "initial_issue": ticket['description_text'],
                "created_date": ticket['created_at'],
                "priority": ticket['priority']
            })
            logging.info(f"No match found for Freshdesk ticket {fd_ticket_id}")

    logging.info("Ticket comparison and matching completed.")
    return matching_tickets, unmatched_tickets

#Function used to format the prioirty field for Syncro Ticket JSON creation
def get_priority_value(priority):
    logging.info(f'Priority function called and passed in variable is {priority}')
    priority_map = {
        0: "0 Urgent",
        1: "1 High",
        2: "2 Normal",
        3: "3 Low"
    }

    # Return the corresponding priority string
    return priority_map.get(priority, "Invalid Priority")

#Create a syncro ticket with a POST call, pass in the related information
def create_syncro_ticket(fd_ticket_id,customer_id, ticket_subject, priority, initial_issue, created_date):
    """
    Creates a ticket in Syncro for the given customer ID with provided details.

    Args:
        customer_id (str): The customer ID in Syncro.
        ticket_subject (str): The subject of the ticket.
        priority (int): The priority level of the ticket.
        initial_issue (str): The initial issue description.
        created_date (str): The date the ticket was created.

    Returns:
        bool: True if the ticket was created successfully, False otherwise.
    """
    syncro_priority = str(get_priority_value(priority))
    ticket_url = f"https://{syncro_domain}.syncromsp.com/api/v1/tickets"
    headers = {
        "accept": "application/json",
        "Authorization": syncro_api_key
    }

    ticket_data = {
        "number": fd_ticket_id,
        "customer_id": customer_id,
        "subject": ticket_subject,
        "created_at": created_date,
        "status": "Resolved",
        "priority": syncro_priority,
        "comments_attributes": [
            {
                "subject": "Notes - Freshdesk Import ",
                "created_at": created_date,
                "body": initial_issue,
                "hidden": True,
                "do_not_email": True
            }
        ]
    }

    try:
        logging.info(f"Attempting to create Syncro ticket for Freshdesk ticket ID: {fd_ticket_id}")
        response = requests.post(ticket_url, headers=headers, json=ticket_data)
        response.raise_for_status()        
        logging.info(f"Syncro ticket created successfully for Freshdesk ticket ID: {fd_ticket_id}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to create Syncro ticket for Freshdesk ticket ID {fd_ticket_id}: {e}")
        return False


def main():
    combined_companies, unmatched_fd_companies, unmatched_syncro_companies = match_companies()
    
def main_old():
    company_id = "153001209190" #Provide the Freshdesk Company ID

    # Returns A list of dictionaries containing all the tickets For that One Company.
    fd_tickets = get_fd_tickets_per_company_id(fd_domain, fd_api_key, company_id)

    syncro_customer_id = "30510882"

    syncro_ticket_links = get_syncro_ticket_links_per_company_id(syncro_customer_id)

    if fd_tickets:
        matching_tickets, unmatched_tickets = find_duplicate_and_new_tickets(syncro_ticket_links, fd_tickets)
        # Print number of matched and unmatched tickets
        print(f"Number of Matched Tickets: {len(matching_tickets)}")
        print(f"Number of Unmatched Tickets: {len(unmatched_tickets)}")
        
        # Create Syncro tickets for unmatched Freshdesk tickets
        for ticket in unmatched_tickets:
            customer_id = syncro_customer_id  # Use a specific Syncro customer ID
            fd_ticket_id = ticket['fd_ticket_id']
            ticket_subject = ticket['ticket_subject']
            priority = ticket['priority']
            initial_issue = ticket['initial_issue']
            created_date = ticket['created_date']

            # Create Syncro ticket
            create_syncro_ticket(fd_ticket_id,customer_id, ticket_subject, priority, initial_issue, created_date)


if __name__ == "__main__":
    main()
