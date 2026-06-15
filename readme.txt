# ZILLOW SCRAPER AUTOMATION

## Overview

This project automates Zillow data extraction using:

* Python
* Playwright
* LangChain
* NVIDIA LLM APIs

The scraper connects to an existing Chrome browser session to help reduce bot detection and automate Zillow interactions.

## Prerequisites

1. Google Chrome installed.
2. Python virtual environment configured.
3. Google Sheets API credentials.
4. NVIDIA API access for LLM functionality.

## Configuration

## Google Sheets API

Replace the provided token.json with your own Google Sheets API credentials and authorization token.

File required:

token.json

## NVIDIA LLM API

Update the project configuration with your own NVIDIA API key before running the application.

## Important Notes

## Anti-Bot Detection

Zillow anti-bot detection handling is enabled at startup.

If a verification popup appears:

1. Complete the verification manually.
2. Click through any anti-bot challenge presented.
3. Once verified, the automation will continue.

## Browser Profile

The automation uses a persistent Chrome profile located at:

%USERPROFILE%\Documents\ZScraperAutomationProfile

Keeping the same profile between sessions may help maintain login state and reduce verification prompts.

## Technology Stack

* Python
* Playwright
* LangChain
* NVIDIA LLM
* Google Sheets API

## Project Entry Point

main.py

## Startup

1. Launch Chrome with Remote Debugging

Open Command Prompt and run:

start "C:\Program Files\Google\Chrome\Application\chrome.exe" "https://www.zillow.com" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\Documents\ZScraperAutomationProfile"

This creates a dedicated browser profile and enables Playwright to attach to the Chrome session.

2. Run the Scraper

Execute:

.venv\Scripts\python.exe .\main.py

