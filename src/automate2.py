# goal is to summarize the page
# get all user interactive elements and get json of id, name, label, description, element type

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional

from openai import OpenAI
from playwright.async_api import async_playwright, BrowserContext, Page, Locator
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

client = OpenAI(api_key=openai_api_key)


async def summarize_page(page: Page) -> str:
    """Summarizes the page content using OpenAI."""

    text_content = await page.evaluate("() => document.body.innerText")  # Extract all text
    prompt = f"""
    Summarize the following text content of a webpage concisely.

    ```
    {text_content[:4000]}  # Limit to avoid exceeding token limits
    ```
    """

    try:
        response = client.chat.completions.create(  # No await here
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant summarizing webpage content."},
                {"role": "user", "content": prompt},
            ],
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        logger.error(f"OpenAI API error during summarization: {e}")
        return "Error summarizing page."


async def extract_interactive_elements(page: Page) -> List[Dict]:
    """Extracts and describes interactive elements."""

    elements = []
    locators = await page.locator("a, button, input, [role='button']").all() # Target specific elements

    for i, locator in enumerate(locators):
        try:
            bounding_box = await locator.bounding_box()
            if bounding_box: # skip hidden elements
                element_info = {}
                element_info["element_id"] = await locator.get_attribute("id") or f"element_{i}" # Provide an id
                element_info["name"] = await locator.get_attribute("name")
                element_info["label"] = await locator.inner_text() # or get attribute aria-label
                element_info["element_type"] = await locator.evaluate("el => el.tagName.toLowerCase()")

                element_html = await locator.inner_html()
                prompt = f"""Describe the functionality of the following HTML element: ```html {element_html} ```"""
                try:
                    response = client.chat.completions.create( # No await here
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant describing HTML elements."},
                            {"role": "user", "content": prompt},
                        ],
                    )
                    element_info["description"] = response.choices[0].message.content.strip()
                except Exception as e:
                    logger.error(f"OpenAI API error during description: {e}")
                    element_info["description"] = "Error describing element."

                elements.append(element_info)
        except Exception as e:
            logger.error(f"Error extracting element {i}: {e}")

    return elements


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://parabank.parasoft.com/parabank/index.htm")

        page_summary = await summarize_page(page)
        print("Page Summary:\n", page_summary)

        interactive_elements = await extract_interactive_elements(page)
        print("\nInteractive Elements:\n", json.dumps(interactive_elements, indent=2))

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())