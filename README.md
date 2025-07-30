# Automated Ticket Reservation Script

This Python script automates the process of monitoring and reserving tickets for high-demand events hosted on a GraphQL-based ticketing platform. It includes integrated support for CAPTCHA harvesting, multi-threaded monitoring, and automated reservation confirmation with Discord webhook notifications.

## Features

- Multi-threaded monitoring and ticket reservation
- CAPTCHA harvester using local port intercepts
- GraphQL mutation and query support for:
  - Monitoring ticket availability
  - Creating reservation jobs
  - Polling reservation job statuses
- Discord webhook support for real-time notifications
- Proxy support for request rotation
- Automatic release and event data resolution
- Support for both release ID and slug resolution
- Bypasses third-party queueing system used during major releases (e.g., recent FISHER concert), as the queue cookie is not enforced during backend reservation requests

## How It Works

1. **CAPTCHA Harvesting**: Opens browser windows locally to solve reCAPTCHA v3 tokens, which are injected into GraphQL requests.
2. **Ticket Monitoring**: Periodically polls the event's GraphQL endpoint to detect newly released or unsold tickets.
3. **Reservation Flow**:
   - Sends a reservation request when a valid ticket is found.
   - Checks the job status to confirm the reservation was successful.
   - Sends a Discord notification with reservation details and expiration timestamp.

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`
- Localhost setup for CAPTCHA harvester (port 7777)
- A Discord webhook URL (for notifications)
- Optional: proxies file (`proxies.txt`) to enable proxy rotation

## Configuration

Create a `release.json` file with the following structure:

```json
{
  "webhook": "YOUR_DISCORD_WEBHOOK_URL",
  "delay": 3
}
```

## Usage

1. Run the script in a terminal or command prompt using Python 3.
2. When prompted, enter the event URL. This can include a release slug or release ID.
3. Specify the number of concurrent tasks (threads) to run.
4. Enter the number of tickets you want to reserve per task.
5. Provide the seat zone name (e.g., "General Admission") or press Enter to use the default.
6. Indicate how many CAPTCHA harvester windows you want to open (if any).
7. If CAPTCHA harvesters are used, wait for them to launch before continuing.
8. Confirm the start of the monitoring process when prompted.
9. The script will begin polling for available tickets, reserve them when found, and send a webhook notification upon success.

## Proxy Support

- To use proxies, create a file named `proxies.txt` in the root directory.
- Each line should be formatted as one of the following:
  - `ip:port`
  - `ip:port:username:password`
- If the file is not found or is empty, the script defaults to using localhost connections.

## Queue Bypass Note

This script bypasses the third-party queue system commonly used during high-traffic events (such as the recent FISHER concert). The platform's backend does not enforce queue validation at the reservation layer, allowing direct access to reservation endpoints without passing the queue gate.

## Disclaimer

This script is intended for educational use only. It highlights architectural weaknesses in ticketing flows where client-side queue mechanisms are not validated server-side. Use this responsibly, and do not deploy it in violation of any terms of service or platform rules.

## License

This project is made available for non-commercial, research, and educational purposes only. No warranty or guarantees are provided.
