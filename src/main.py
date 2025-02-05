import asyncio
import json
import logging
import os
from typing import Dict, List, Optional

from openai import OpenAI
from playwright.async_api import async_playwright, BrowserContext, Page, Locator
from dotenv import load_dotenv

from automate3 import find_element_by_task, findAndClickThisTask
from libs.intents_to_links import map_intent_to_link

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://parabank.parasoft.com/parabank/index.htm")

        while True:

            print("\nChoose an action:")
            # print("1. Summarize Page")
            # print("2. Extract Interactive Elements")
            print("3. Find Element by Task and Click (Example Task)")
            print("4. Map intents to links")
            print("99. Exit")

            choice = input("Enter your choice (1-4): ")

            try:
                choice = int(choice)
                if choice == 1:
                    # summary = await summarize_page(page)
                    # print("Page Summary:\n", summary)
                    print("no action")
                elif choice == 2:
                    # elements = await extract_interactive_elements(page)
                    # print("Interactive Elements:\n", json.dumps(elements, indent=2))
                    print("no action")
                elif choice == 3:
                    target_task = input("Enter the target task: ")
                    await findAndClickThisTask(page, target_task)
                elif choice == 4:
                    target_task = input("Enter your intent: ")
                    matching_link = await map_intent_to_link(page, target_task)
                    if matching_link:
                        print(f"Best matching link: {matching_link['label']} (href: {matching_link['href']})")
                        await matching_link["locator"].click()  # Click the link!
                    else:
                        print(f"No link found matching the intent: {target_task}")

                elif choice == 99:
                    break
                else:
                    print("Invalid choice. Please enter a number between 1 and 4.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())