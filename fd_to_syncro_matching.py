import requests
from requests.auth import HTTPBasicAuth
import pprint
from pprint import pprint
import json
import time
import logging
import os
from datetime import datetime

###################################################################################################
# API Variables
###################################################################################################
API_CALL_SLEEP = 0.75

syncro_domain = 'syncro-subdomain'
syncro_api_key = "syncro-apikey"

fd_domain = 'freshdeskdomain'
fd_api_key = 'freshdesk apikey'


####################################################################################################
# Section 0
#### Logging Configuration and API
####################################################################################################

base_log_dir = r'c:\temp\logs'

# Create a unique directory for each run based on the current timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_dir = os.path.join(base_log_dir, f'run_{timestamp}')

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

####################################################################################################
####### Section 1a
#   create List of Companies that match or dont match between Freshdesk and Syncro
#   
#   get_fd_companies
#   find_next_link -----> This is used in get_fd_companies and get_fd_tickets
#   get_syncro_companies
#
#   match_companies -----> Returns 3 lists: combined_companies, unmatched_fd_companies, unmatched_syncro_companies
#
#   End Result of Section 1 is you have 3 lists of combined and unmatched_fd and unmatched_syncro companies
#   There will be log files of matched and unmatched companies
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
            time.sleep(API_CALL_SLEEP)
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
            time.sleep(API_CALL_SLEEP)
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

# Compares the Companies Names in Freshdesk to Syncro's and creates a list of matched and unmatched companies.
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
        #logging.debug(f"Processing Freshdesk company: {company_name}")        
        if company_name in syncro_companies:
            
            syncro_id = syncro_companies[company_name]
            combined_companies[company_name] = [fd_id, syncro_id]
        else:
            unmatched_fd_companies[company_name] = fd_id

    for company_name, syncro_id in syncro_companies.items():
        #logging.debug(f"Checking Syncro company: {company_name}")
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

####################################################################################################
####### Section 1b
#  Functions to gather Freshdesk comments and create syncro comments
#   
#   The create_syncro_comment function is a helper for get_ticket_comments function
#   get_ticket_comments is only called if a new ticket is found missing in Syncro
#   Meaning the new ticket and comment is created at the same time

####################################################################################################

def create_syncro_comment(syncro_ticket_id, body, private_public, created, inbound):
    url = f"https://{syncro_domain}.syncromsp.com/api/v1/tickets/{syncro_ticket_id}/comment"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {syncro_api_key}",
        "accept": "application/json"
    }

    hidden = True if private_public else False
    subject = "Inbound Comment" if inbound else "Outbound Comment"
    
    data = {
        "created_at": created,
        "subject": subject,        
        "body": body,
        "hidden": hidden,        
        "do_not_email": True
    }

    logging.info(f"Creating Syncro comment for ticket ID {syncro_ticket_id}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        time.sleep(API_CALL_SLEEP)
        response.raise_for_status()
        
        if response.status_code == 200:
            logging.info(f"Successfully created comment for Syncro ticket ID {syncro_ticket_id}")
        else:
            logging.warning(f"Failed to create comment for Syncro ticket ID {syncro_ticket_id}: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request Exception while creating Syncro comment for ticket ID {syncro_ticket_id}: {e}")

def get_ticket_comments(syncro_ticket_id, ticket_id):
    url = f"https://{fd_domain}.freshdesk.com/api/v2/tickets/{ticket_id}/conversations"
    headers = {
        "Content-Type": "application/json"
    }
    auth = (fd_api_key, "X")
    
    all_comments = []
    page = 1
    
    try:
        while True:
            response = requests.get(url, headers=headers, auth=auth, params={'page': page})
            time.sleep(API_CALL_SLEEP)
            if response.status_code == 200:
                ticket_data = response.json()
                
                if not ticket_data:
                    break
                
                all_comments.extend(ticket_data)
                page += 1
            else:
                logging.warning(f"Failed to retrieve data for ticket ID {ticket_id}: {response.status_code}, {response.text}")
                return None
        
        for ticket in all_comments:
            comment = ticket.get('body_text', '')
            inbound = ticket.get('incoming', '')
            from_email = ticket.get('from_email', '')
            to_email = ticket.get('to_emails', '')
            private_public = ticket.get('private', '')
            created = ticket.get('created_at', '')

            syncro_comment = (f"Email From {from_email} sent to {to_email} \n"
                              f" \n"
                              f"{comment}")
            
            create_syncro_comment(syncro_ticket_id, syncro_comment, private_public, created, inbound)
        
        logging.info(f"Successfully retrieved and processed comments for ticket ID {ticket_id}")
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Request Exception while retrieving comments for ticket ID {ticket_id}: {e}")
        return None


####################################################################################################
######## Section 2
# Next the goal is to loop through the combined_companies dictionary, which is formatted like:
#
# {
#     "John Smith Smithing": [
#         153001209190,
#         30510882
#     ],
#     "Web Networks": [
#         153001209535,
#         32172685
#     ]
# }
#
# for each key, It will build Ticket List for FD and a Ticket List for Syncro
# from that list, it remove duplicates based on Subject Line + FD Ticket ID
# create a new ticket in syncro for what is left in the list.
#
# Functions:
#
# get_fd_tickets_per_company_id(fd_domain, fd_api_key, company_id)
# def get_syncro_ticket_links_per_company_id(syncro_customer_id)
# find_duplicate_and_new_tickets(syncro_ticket_links, fd_tickets)
#
# get_priority_value(priority) #Function used to format the prioirty field for Syncro Ticket JSON creation
#
# def create_syncro_ticket(fd_ticket_id,customer_id, ticket_subject, priority, initial_issue, created_date) #Create a syncro ticket with a POST call, pass in the related information
####################################################################################################


# builds a list of freshdesk tickets per company id, since 2019
def get_fd_tickets_per_company_id(fd_company_id):
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
    url = f'{base_url}?include=description&company_id={fd_company_id}&updated_since={updated_since}'
    headers = {
        'Content-Type': 'application/json'
    }
    tickets = []
    
    while url:
        try:
            response = requests.get(url, headers=headers, auth=HTTPBasicAuth(fd_api_key, 'X'))
            time.sleep(API_CALL_SLEEP)
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

# Function Builds a list of syncro tickets ids and subjects per company id
def get_syncro_ticket_links_per_company_id(syncro_customer_id):
    url = f"https://{syncro_domain}.syncromsp.com/api/v1/customers/{syncro_customer_id}"
    headers = {
        "accept": "application/json",
        "Authorization": syncro_api_key
    }

    response = requests.get(url, headers=headers)
    time.sleep(API_CALL_SLEEP)
    
    if response.status_code == 200:
        data = response.json()
        
        ticket_links = data.get('customer', {}).get('ticket_links', [])
        return ticket_links
    else:
        print(f"Error: Unable to fetch data (Status code: {response.status_code})")
        return None

#Compares the Ticket List for Freshdesk and Syncro using the Ticket Number and Subject Line
def find_duplicate_and_new_tickets(company_name,syncro_ticket_links, fd_tickets):
    '''
    List of dictionaries that hold individual Ticket Data is passed into this function
    The Lists are from GET API calls against the company IDs

    The Ticket Number in Freshdesk will be used to look for duplicates either in the Syncro Ticket Number or in the Subject
    Example of data format at the bottom:    
    '''
    # Print number of matched and unmatched tickets
    logging.info("Starting Ticket Comparsion and Matching")
    logging.info(f"Total Number of Syncro Tickets: {len(syncro_ticket_links)}")
    logging.info(f"Total Number of Freshdesk Tickets: {len(fd_tickets)}")

    duplicated_tickets = []
    new_tickets = []

    for ticket in fd_tickets:
        logging.info(f"----------------------------------Next Freshdesk Ticket---------------------------------")
        ticket_subject = ticket['subject']
        fd_ticket_id = ticket['id']
        ticket_subject = f"{ticket_subject} {fd_ticket_id}"

        syncro_subjects = [ticket['subject'] for ticket in syncro_ticket_links]
        if ticket_subject in syncro_subjects:
            logging.info(f"Duplicate Ticket found for Freshdesk ticket {fd_ticket_id} - {ticket_subject}")
            duplicated_tickets.append({
                "fd_ticket_id": fd_ticket_id,
                "fd_subject": ticket_subject,                
                "syncro_subject": ticket_subject
            })
            
            
        else:            
            new_tickets.append({                  
                "fd_ticket_id": fd_ticket_id,
                "ticket_subject": ticket_subject,
                "initial_issue": ticket['description_text'],
                "created_date": ticket['created_at'],
                "priority": ticket['priority']
            })
            logging.info(f"New Ticket found for Freshdesk ticket {fd_ticket_id} - {ticket_subject}")
                   


    logging.info("Ticket comparison and matching completed.")
    
    # Dump matched and unmatched tickets into separate files
    with open(os.path.join(log_dir, f'{company_name}_duplicate_tickets.txt'), 'w') as match_file:
        json.dump(duplicated_tickets, match_file, indent=4)

    with open(os.path.join(log_dir, f'{company_name}_new_tickets.txt'), 'w') as unmatched_file:
        json.dump(new_tickets, unmatched_file, indent=4)

    return duplicated_tickets, new_tickets

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
                "subject": "Intial Notes - Freshdesk Imported Ticket ",
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
        time.sleep(API_CALL_SLEEP)
        response.raise_for_status()        
        logging.info(f"Syncro ticket created successfully for Freshdesk ticket ID: {fd_ticket_id}")
        response_data = response.json()
        syncro_ticket_id = response_data["ticket"]["id"]
        logging.info(f"Adding Comments to Syncro Ticket {syncro_ticket_id}")
        get_ticket_comments(syncro_ticket_id, fd_ticket_id)
        
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to create Syncro ticket for Freshdesk ticket ID {fd_ticket_id}: {e}")
        return False

# Freshdesk company ID and Syncro Company ID is passed in from the combined_companies dictionary created from the match_companies Function
def process_company_tickets(company_name, fd_id, syncro_id):
    logging.info(f"Processing company: {company_name}")
    logging.info(f"Freshdesk ID: {fd_id}, Syncro ID: {syncro_id}")
    
    fd_tickets = get_fd_tickets_per_company_id(fd_id)
    syncro_ticket_links = get_syncro_ticket_links_per_company_id(syncro_id)
    
    # If there are freshdesk tickets for this company, pass the tickets list into find_duplicate_and_new_tickets function
    if fd_tickets:
        duplicated_tickets, new_tickets = find_duplicate_and_new_tickets(company_name,syncro_ticket_links, fd_tickets)
        
        logging.info(f"Number of Duplicated Tickets for {company_name}: {len(duplicated_tickets)}")
        logging.info(f"Number of New Tickets for {company_name}: {len(new_tickets)}")
        
        for ticket in new_tickets:
            fd_ticket_id = ticket['fd_ticket_id']
            ticket_subject = ticket['ticket_subject']
            priority = ticket['priority']
            initial_issue = ticket['initial_issue']
            created_date = ticket['created_date']

            # Create Syncro ticket
            success = create_syncro_ticket(fd_ticket_id, syncro_id, ticket_subject, priority, initial_issue, created_date)
            if success:
                logging.info(f"Syncro ticket created successfully for Freshdesk ticket ID: {fd_ticket_id}")
            else:
                logging.warning(f"Failed to create Syncro ticket - process_company_tickets Function")

def main():

    # Calls match_companies() function 
    combined_companies, unmatched_fd_companies, unmatched_syncro_companies = match_companies()

    for company_name, values in combined_companies.items():
        fd_id, syncro_id = values
        process_company_tickets(company_name, fd_id, syncro_id)

if __name__ == "__main__":
    main()
