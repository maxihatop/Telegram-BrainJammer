# **Telegram BrainJammer: README**

Scammers using profiles with photos of beautiful Asian women are crawling out of every corner of the internet. Blocking them is the best thing you can do *for them*—it simply allows them to move on to their next victim immediately. However, "jamming" their brains by forcing them to waste days chatting with an AI bot is not only entertaining but also saves innocent people by keeping the scammers occupied.

**Note:** This project and its documentation intentionally promote a lack of sympathy toward the social group known as "crypto-scammers."

## ---

**Features**

* **Automated Engagement:** Automatically responds to incoming messages.
* **AI-Powered Persona:** Uses OpenAI to maintain a consistent, cautious, and slightly eccentric persona (e.g., "Oleg Ivanovich," a retired engineer).
* **Human-like Delays:** Implements random delays to mimic human typing speeds and frustrate automated scam scripts.
* **Brain-Jamming Logic:** Specifically designed to lead scammers into technical dead-ends and psychological frustration.

## **Installation**

### **1\. Clone the repository**

Ensure you have telegram-brainjammer.py and config.py in your project folder.

### **2\. Set up a Virtual Environment (venv)**

It is highly recommended to use a virtual environment to keep your global Python installation clean.
`# Create the virtual environment`

`python3 -m venv venv`

`# Activate the virtual environment`

`# On Linux/macOS:`

`source venv/bin/activate`

`# On Windows:`

`.\\venv\\Scripts\\activate`

### **3\. Install Dependencies**

Install the required libraries using pip:
`pip install telethon openai`

## **Configuration**

The script expects a file named config.py in the same directory.

### **config.py Format**

Create a file named config.py and populate it with your credentials:
`# config.py`

`API_ID = 1234567          # Your Telegram API ID`

`API_HASH = 'your_hash'    # Your Telegram API HASH`

`OPENAI_API_KEY = 'sk-...' # Your OpenAI API Key`

### **How to obtain the keys:**

1. **Telegram API\_ID and API\_HASH:**
   * Go to [https://my.telegram.org](https://my.telegram.org).
   * Log in with your phone number.
   * Click on **"API development tools"**.
   * Create a new application.
   * Copy your App api\_id and App api\_hash.
2. **OPENAI\_API\_KEY:**
   * Log in to your [OpenAI Platform](https://platform.openai.com/) account.
   * Navigate to the **"API Keys"** section.
   * Click **"Create new secret key"**.

## **Usage**

Once configured and the venv is active, run the script:
`python3 telegram-brainjammer.py`

The script will prompt you for your phone number on the first run to authorize the Telegram session. After that, it will stay active and "jam" any scammer who tries their luck.

## **Required Libraries**

* **Telethon:** For interacting with the Telegram API as a user client.
* **OpenAI:** For generating intelligent, context-aware responses.
* **Asyncio:** For handling concurrent events.

## **Real-World "Brain-Jamming" Example**

The repository includes log files (e.g., *Maggie-Lee.txt*) that demonstrate a typical two-day scam cycle. You can observe how the scammer adopts a persona of a successful, attractive woman, building rapport by discussing Thai beaches, Vietnamese cuisine, and daily routines. The "social engineering" phase is extensive, designed to establish a false sense of intimacy. However, once the conversation shifts to pitching "AI smart plans" or "on-chain wallets," the AI bot maintains its cautious, technical persona. The transition from friendly banter to aggressive gaslighting and eventual insults (when the scammer realizes the "retired engineer" won't bite) is a classic example of why this tool is necessary—it turns their own psychological tactics against them, wasting their most valuable resource: time.

