import logging, threading, requests, colorama, pytz, sys, json, random, traceback
from classes.logger import logger
from discord_webhook import DiscordEmbed, DiscordWebhook
from datetime import datetime
from harvester import Harvester, fetch
from time import sleep
colorama.init()
log = logger().log


logging.getLogger('harvester').setLevel(logging.CRITICAL)

getOrgID = {
    'audiologytouring':'dc62e804-96fa-4fff-bf26-6ca4c6fbd1d9',
    'trademark':'9155f056-71bf-4ee0-b3c1-206bccd012ff',
    'limitlesstouring':'9a9f2bb1-ae02-4f79-9d80-4012e50e0400',
    'soundsplash':'15c612eb-725c-456a-a1b0-f3ab49ec2fb4',
    'higher-grnd':'15159d11-1e9b-4622-8f98-0a32ffe58d27',
    'teamevent':'71a9e5bc-642f-4443-9082-8c259f8de67c',
    'summittouring':'9d4b73bf-a7ae-4909-9f5d-e208cce91414'
}


def start_captcha(x):
    try: 
        harvester = Harvester('localhost', 7777, 750)
        harvester.intercept_recaptcha_v3(domain=captchaURL, sitekey='6LcS8M0eAAAAAOMFWJ3xLU3pwNMnZqZTgIGDHygq')
        (threading.Thread(target=harvester.serve, daemon=True)).start()
        harvester.launch_browser()
        print('Successfully started captcha harvester '+str(x+1))
        print()
    except Exception as e:
        print('Failed to open captcha harvester '+str(x+1))
        input()


usedCaptchas = []

def getCaptcha(slug):
    while True:
        log(slug+'Getting captcha...')
        try:
            captchaToken = fetch.token(captchaURL, port=7777)
            if captchaToken not in usedCaptchas:
                usedCaptchas.append(captchaToken)
                log(slug+'Got captcha')
                break
        except:
            log(slug+'Failed to get captcha')
            sleep(3)

    return captchaToken


def sendWebhook(reserveID, expiry, name, slug):
    try:   
        webhook = DiscordWebhook(url=config['webhook'], username='Swine Scripts', avatar_url = 'https://cdn.discordapp.com/attachments/694012581555470396/779083760943366174/swine.jpg')
        embed = DiscordEmbed(title = ':pig: Successfully reserved ticket! :pig:', description=eventInfo['title']+'\n'+eventInfo['venue'],color=16761035)
        embed.url = baseURL+'/checkout/'+reserveID
        embed.add_embed_field(name = 'Company', value = "Flicket", inline = True) 
        embed.add_embed_field(name = 'Ticket', value = name, inline = True) 
        embed.add_embed_field(name = 'Quantity', value = quantity, inline = True) 
        embed.add_embed_field(name = 'Expires', value = '<t:'+str(int(str(expiry).split('.')[0])-60)+':R>', inline = True) 
        embed.set_footer(text='Swine Scripts', icon_url='https://cdn.discordapp.com/attachments/694012581555470396/779083760943366174/swine.jpg')
        embed.set_timestamp()
        webhook.add_embed(embed)
        webhook.execute()
    except Exception as e:
        print(e)
        log(slug+'Failed to send webhook')



def checkJob(slug, name, jobID):
    errorSlug = f"Error reserving ticket {name} x {str(quantity)}"
    while True:
        log(slug+'Checking reservation...')

        headers['g-recaptcha-response'] = getCaptcha(slug)

        json_data = {
            'query': '''
            query getOrderJobStatus($jobId: String!) {
            getOrderJobStatus(jobId: $jobId) {
                jobId
                order {
                id
                expiryDate
                }
                createOrderError {
                ... on TicketNotAvailableError {
                    message
                }
                ... on CreateOrderError {
                    message
                }
                }
            }
            }
            ''',
            'variables': {
                'jobId': jobID,
            },
        }


        try:
            if usingProxies:
                r = requests.post('https://api.flicket.co.nz/graphql', headers=headers, json=json_data, timeout=3, proxies=random.choice(proxies))
            else:
                r = requests.post('https://api.flicket.co.nz/graphql', headers=headers, json=json_data, timeout=3)
        except:
            log(slug+'Failed to connect to Flicket')
            sleep(delay)
            continue


        if r.status_code == 200:
            try:
                data = r.json()['data']['getOrderJobStatus']
                if data['createOrderError'] == None:
                    try:
                        reserveID = data['order']['id']
                        timestamp_iso = data['order']['expiryDate']
                        dt_object = datetime.fromisoformat(timestamp_iso[:-1])  
                        utc_timezone = pytz.timezone('UTC')
                        dt_object_utc = utc_timezone.localize(dt_object)
                        unix_timestamp = dt_object_utc.timestamp()
                        log(slug+f'Successfully reserved  {name} x {str(quantity)}: {baseURL}/checkout/{reserveID}')
                        sendWebhook(reserveID, unix_timestamp, name, slug)
                        return True
                    except Exception as e:
                        if len(data) == 3:
                            continue
                        else:
                            log(slug+f'{errorSlug}')
                            print(r.text)
                else:
                    try:
                        log(slug+f"{errorSlug}. Error: {data['createOrderError'][0]['message']}")
                    except:
                        log(slug+f'{errorSlug}')
                
            except Exception as e:
                try:
                    log(slug+f'{errorSlug}. Error: '+r.json()['errors'][0]['message'])
                except:
                    log(slug+f'{errorSlug}. Error: {str(e)}')
                    print(r.text)
                    log('Traceback: {}'.format(traceback.format_exc())) 

            break
        else:
            log(slug+'Failed to request page. Status Code: '+str(r.status_code))
            print(r.text)

        sleep(delay)

    return False




def getTickets(tickets, slug, zone):
    errorSlug = f'Error initialising reservation for {i["name"]} x {str(quantity)}'
    while True:
        for i in tickets:
            
            log(slug+'Initialising reservation for ticket type: '+i['name']+ ' x '+str(quantity))

            headers['g-recaptcha-response'] = getCaptcha(slug)

            json_data = {
                'query': '''
                mutation createOrder($input: CreateOrderInput!) {
                createOrder(input: $input) {
                    jobId
                    createOrderError {
                    ... on TicketNotAvailableError {
                        message
                    }
                    ... on CreateOrderError {
                        message
                    }
                    }
                }
                }
                ''',
                'variables': {
                    'input': {
                        'lineItems': [
                            {
                                'quantity': quantity,
                                'ticketTypeId': i['id'],
                                'type': 'Ticket',
                                'seatZone': zone,
                            },
                        ],
                        'referralId': None,
                        'releaseId': eventInfo['id'],
                    },
                },
            }

            try:
                if usingProxies:
                    r = requests.post('https://api.flicket.co.nz/graphql', headers=headers, json=json_data, timeout=3, proxies=random.choice(proxies))
                else:
                    r = requests.post('https://api.flicket.co.nz/graphql', headers=headers, json=json_data, timeout=3)
            except:
                log(slug+'Failed to connect to Flicket')
                sleep(delay)
                continue

            if r.status_code == 200:
                try:
                    data = r.json()['data']['createOrder']
                    if data['createOrderError'] == None:
                        try:
                            jobID = r.json()['data']['createOrder']['jobId']
                            log(slug+f'Succesfully initialised reservation for {i["name"]} x {str(quantity)}')
                            if checkJob(slug, i['name'], jobID):
                                return True
                        except:
                            log(slug+f"{errorSlug}")
                    else:
                        try:
                            log(slug+f"{errorSlug}. Error: {data['createOrderError'][0]['message']}")
                        except:
                            log(slug+f'{errorSlug}')
                except Exception as e:
                    try:
                        log(slug+f'{errorSlug}. Error: '+r.json()['errors'][0]['message'])
                    except:
                        log(slug+f'{errorSlug}. Error: {str(e)}')
                        print(r.text)

            else:
                log(slug+'Failed to request page. Status Code: '+str(r.status_code))
                print(r.text)

            sleep(delay)

            

            


def monitorTickets(slug, zone):
    while True:
        log(slug+'Monitoring for tickets...')

        query = """
        query getEventAndReleaseForCustomer($input: EventsWithAccessControlInput!) {
        getEventAndReleaseForCustomer(input: $input) {
            event {
            id
            title
            ticketTypes {
                name
                id
                soldOut
                isResaleTicket
            }
            }
        }
        }
        """

        json_data = {
            'query': query, 
            'variables': {
                'input': {
                    'eventId': eventID,
                },
            },
            'operationName': 'getEventAndReleaseForCustomer',
        }

        if releaseSlug is not None:
            json_data['variables']['input']['releaseSlug'] = releaseSlug

        try:
            if usingProxies:
                r = requests.post('https://api.flicket.co.nz/graphql', headers=headers, json=json_data, timeout=3, proxies=random.choice(proxies))
            else:
                r = requests.post('https://api.flicket.co.nz/graphql', headers=headers, json=json_data, timeout=3)
        except:
            log(slug+'Failed to connect to Flicket')
            sleep(delay)
            continue


        if r.status_code == 200:
            try:
                data = r.json()['data']['getEventAndReleaseForCustomer']['event']
                tickets = []
                for i in data['ticketTypes']:
                    ticket = {}
                    if i['soldOut'] == False and i['isResaleTicket'] == False and 'bus' not in i['name'].lower() and 'comp' not in i['name'].lower():
                        ticket['id'] = i['id']
                        ticket['name'] = i['name']
                        tickets.append(ticket)

                if len(tickets) != 0:
                    log(slug+f'Found {str(len(tickets))} available ticket(s)')
                    if getTickets(tickets, slug, zone):
                        break
            except Exception as e:
                print(e)
                log(slug+'Failed to check for tickets')
        else:
            log(slug+'Failed to request page. Status Code: '+str(r.status_code))
            print(r.text)

        sleep(delay)

    return



def getEvent():
    while True:
        log('Getting event and release info...')

        query = """
        query getEventAndReleaseForCustomer($input: EventsWithAccessControlInput!) {
        getEventAndReleaseForCustomer(input: $input) {
            event {
            id
            title
            venue {
                name
            }
            }
            release {
                id
                name
            }
        }
        }
        """

        json_data = {
            'query': query,
            'variables': {
                'input': {
                    'eventId': eventID,
                },
            },
            'operationName': 'getEventAndReleaseForCustomer',
        }

        if releaseSlug is not None:
            json_data['variables']['input']['releaseSlug'] = releaseSlug

        if releaseId is not None:
            json_data['variables']['input']['releaseId'] = releaseId

 
        try:
            if usingProxies:
                r = requests.post('https://api.flicket.co.nz/graphql', headers=headers, json=json_data, timeout=3, proxies=random.choice(proxies))
            else:
                r = requests.post('https://api.flicket.co.nz/graphql', headers=headers, json=json_data, timeout=3)
        except Exception as e:
            print(e)
            log('Failed to connect to Flicket')
            sleep(delay)
            continue

        eventInfo = {}  

        if r.status_code == 200:
            try:
                data = r.json()['data']['getEventAndReleaseForCustomer']['event']
                eventInfo['title'] = data['title']
                eventInfo['venue'] = data['venue']['name']
                if r.json()['data']['getEventAndReleaseForCustomer']['release'] == None:
                    log('Release not live yet')
                else:
                    eventInfo['id'] = r.json()['data']['getEventAndReleaseForCustomer']['release']['id']
                    log(f'Successfully got event data and release info for {eventInfo['title']}. Release id: {eventInfo['id']}')
                    log('Release id: '+eventInfo['id'])
                    return eventInfo
            except Exception as e:
                print(e)
                log('Failed to scrape event data')
                print(r.text)
        else:
            log('Failed to request page. Status Code: '+str(r.status_code))
            print(r.text)

        sleep(delay)


def start():
    print('Please wait for the captcha harvester(s) to start')
    print()
    for i in range(harvesterNumber):
        start_captcha(i)
        sleep(3)
    sleep(10)



print()
print()
print('Welcome to Swine AIO - Flicket!')
print()
print()


def load_config():
    print('Loading config...')
    try:
        file = open('release.json')
        config = json.loads(file.read())
        print('Loaded config')
        print()
        file.close()
        return config
    except Exception as e:
        print('Failed to load config. Error: '+str(e))
        input()
        sys.exit()



def load_proxies():
    directory = 'proxies.txt'
    usingProxies = False
    proxies = []

    try:
        with open(directory) as k:
            initProxies = k.read().splitlines()

        try:
            for proxy in initProxies:
                proxy = proxy.split(':')
                ip = proxy [0]
                port = proxy[1]
                try:
                    user = proxy[2]
                    password = proxy[3]
                    finProxy = {'http':'http://'+user+':'+password+'@'+ip+':'+port, 'https':'http://'+user+':'+password+'@'+ip+':'+port}
                except:
                    finProxy = {'http':'http://'+ip+':'+port, 'https':'http://'+ip+':'+port}
                proxies.append(finProxy)
        except Exception as e:
            pass
    except Exception as e:
        log('Error: '+str(e))

    if len(proxies) != 0:
        log('Loaded '+str(len(proxies))+' proxies from '+str(directory))
        usingProxies = True
    else:
        log('Loaded 0 proxies. Running localhost')
        proxies = 'Local Host'

    return proxies, usingProxies



def getDetails():
    while True:
        eventURL = input('Enter event url: ')
        tasks = input('How many tasks?: ')
        tasks = int(tasks)
        quantity = input('How many tickets per task?: ')
        quantity = int(quantity)
        zone = input('Enter zone name (default: General Admission): ')
        harvesterNumber = int(input('How many captcha harvesters?: '))
        if len(zone) == 0:
            zone = 'General Admission'
        print()
        print()
        break

    try:
        releaseSlug= eventURL.split('slug=')[1].split('&')[0]
    except:
        releaseSlug = None

    try:
        releaseId= eventURL.split('release=')[1].split('&')[0]
    except:
        releaseId = None

    
    organisation = eventURL.split('https://')[1].split('.')[0].lower()
    eventID = eventURL.split('/events/')[1]
    if '?' in eventID:
        eventID = eventID.split('?')[0]
    if '/' in eventID:
        eventID = eventID.split('/')[0]
    
    orgID = getOrgID[organisation]
    baseURL = 'https://{}.flicket.co.nz'.format(organisation)
    originHeader = baseURL
    captchaURL = baseURL.split('//')[1]
    refererHeader = originHeader +'/'

    return eventURL, tasks, quantity, organisation, eventID, orgID, baseURL, originHeader, captchaURL, refererHeader, zone, harvesterNumber, releaseSlug, releaseId


proxies, usingProxies = load_proxies()
config = load_config()

delay = config['delay']

eventURL, tasks, quantity, organisation, eventID, orgID, baseURL, originHeader, captchaURL, refererHeader, zone, harvesterNumber, releaseSlug, releaseId = getDetails()

if harvesterNumber != 0:
    start()

headers = {
    'authority': 'api.flicket.co.nz',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'flicket-org-id': orgID,
    'origin': originHeader,
    'pragma': 'no-cache',
    'referer': refererHeader,
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'user-token': 'PLACEHOLDER',
}

eventInfo = getEvent()


while True:
    print()
    print()
    s = input('Do you want to start? (y/n): ')
    if s.lower() == 'y':
        break
    else:
        sleep(1)

print()


for x in range(tasks):
    (threading.Thread(target=monitorTickets, args=(f"[{organisation.upper()}] [{eventInfo['title']}] [TASK {str(x+1)}] : ", zone))).start()


input()




