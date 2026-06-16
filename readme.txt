# Zillow Scraper Automation

## Overview

This is an automation that scrape Zillow property data using:

* Python
* Playwright
* LangChain
* NVIDIA LLM APIs
* Google Sheets API

The scraper connects to an existing Chrome browser session to reduce bot-detection triggers and automate Zillow interactions more reliably.

---

## Prerequisites

Before running the application, ensure the following are installed and configured:

1. Google Chrome
2. Python 
3. Google Sheets API 
4. NVIDIA API

---

## How to launch.

### 1. Launch Chrome with Remote Debugging

To help minimize Zillow anti-bot warnings, start Chrome using remote debugging mode.

Open Command Prompt and run:

```cmd
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" "https://www.zillow.com" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\Documents\ZScraperAutomationProfile"
```

This command:

* Creates a dedicated Chrome profile for the scraper
* Enables Playwright to attach to the existing browser session
* Helps preserve cookies, login state, and browser fingerprints between runs

### 2. Run the Scraper

Execute the following command:

```cmd
C:\GIT\ZScraper.venv\Scripts\python.exe C:\GIT\ZScraper\main.py
```

---

## Configuration

### Google Sheets API

The scraper uses the Google Sheets API to store and manage extracted data.

#### Required Files

* `credentials.json` — OAuth client credentials downloaded from your Google Cloud project
* `token.json` — Automatically generated after the first successful authentication and reused for future sessions

#### Setup Steps

1. Create or select a Google Cloud project.
2. Enable the Google Sheets API.
3. Configure the OAuth Consent Screen.
4. Create an **OAuth Client ID** and select **Desktop Application** as the application type.
5. Download the OAuth credentials file and save it as `credentials.json` in the project directory.
6. Run the scraper.
7. Sign in with your Google account and grant the requested permissions when prompted.

After successful authentication, a `token.json` file will be generated automatically and reused for subsequent runs.

### NVIDIA LLM API

Add your NVIDIA API key to the project's configuration before running the scraper.

```env
NVIDIA_API_KEY=your_api_key_here
```

---

## Agentic Workflow

The scraper uses an agent-driven workflow powered by LangChain and NVIDIA LLMs to:

1. Analyze Zillow search results
2. Navigate listing pages intelligently
3. Extract relevant property information
4. Handle page variations and dynamic content
5. Structure extracted data for export to Google Sheets

This approach provides greater flexibility than traditional rule-based scraping and improves resilience to minor UI changes.

---

## Anti-Bot Detection Handling

The scraper connects to an existing Chrome browser session to reduce Zillow anti-bot triggers and maintain a consistent browser identity.

If a verification challenge appears:

1. Complete the verification manually.
2. Finish any CAPTCHA or security checks presented.
3. Return to the browser window.

Once verification is completed, the automation will continue processing.

---

## Browser Profile

The scraper uses a persistent Chrome profile located at:

```text
%USERPROFILE%\Documents\ZScraperAutomationProfile
```

Using the same profile across sessions helps:

* Maintain login state
* Preserve cookies and preferences
* Reduce repeated verification prompts

---

## Technology Stack

| Component         | Purpose                                   |
| ----------------- | ----------------------------------------- |
| Python            | Core application logic                    |
| Playwright        | Browser automation                        |
| LangChain         | Agent orchestration                       |
| NVIDIA LLM APIs   | AI-powered navigation and data extraction |
| Google Sheets API | Data storage and reporting                |

---

## Project Structure

```text
ZScraper/
├── main.py
├── credentials.json
├── token.json
├── requirements.txt
└── ...
```

---

## Entry Point

```text
main.py
```
