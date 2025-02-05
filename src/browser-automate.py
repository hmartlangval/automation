import asyncio
import json
import logging
import os
from typing import Dict, List, Optional

# import openai
from openai import OpenAI
from playwright.async_api import async_playwright, BrowserContext, Page, Locator
from dotenv import load_dotenv


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Set your OpenAI API key
# openai.api_key = 

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable not set. Create a .env file with OPENAI_API_KEY=\"your_actual_key\"")

client = OpenAI(api_key=openai_api_key)


# Define a function to get element descriptions using OpenAI
async def describe_elements(page: Page) -> Dict[str, str]:
    """Uses OpenAI to describe the functionality of elements on a page."""

    elements = {}
    locators = await page.locator("*").all()  # Await the locator retrieval

    for i, locator in enumerate(locators):
        try:
            bounding_box = await locator.bounding_box()
            if bounding_box:  # Skip elements without visible bounding boxes
                try:
                    element_html = await locator.inner_html()
                except Exception as e:
                    logger.error(f"Error getting inner HTML for element {i}: {e}")
                    element_html = ""  # or handle it as you see fit.

                prompt = f"""
                Describe the functionality of the following HTML element in a web page context. 
                Be concise and focus on what the user would expect to happen when interacting with it (e.g., clicking, hovering, etc.).  If the element is purely decorative or serves no interactive purpose, say "Decorative".

                ```html
                {element_html}
                ```
                """

                try:  # Correct try block placement
                    response = client.chat.completions.create(  # Await here
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant describing HTML elements."},
                            {"role": "user", "content": prompt},
                        ],
                    )
                    description = response.choices[0].message.content.strip()
                    elements[f"element_{i}"] = description
                    logger.info(f"Element {i}: {description}")
                except Exception as e:  # Catch exceptions related to OpenAI API
                    logger.error(f"OpenAI API error: {e}")
                    elements[f"element_{i}"] = "Error with OpenAI API"
            else:
                logger.info(f"Skipping invisible element {i}")  # Log skipped elements
        except Exception as e:
            logger.error(f"Error describing element {i}: {e}")
            elements[f"element_{i}"] = "Error describing element"  # Handle errors gracefully

    return elements

async def perform_task(page: Page, task: str):
    """Performs a task on the page based on natural language instructions."""

    elements = await describe_elements(page)

    # Use OpenAI to identify the correct element to interact with
    prompt = f"""
    Given the following element descriptions and a user task, identify the key of the element that best corresponds to the task. If no suitable element is found, return "None".

    Elements:
    {json.dumps(elements, indent=2)}

    Task: {task}
    """

    try: # Correct try block placement
        response = client.chat.ChatCompletion.create(  # Await here
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that identifies elements on a webpage based on their description and a user task."},
                {"role": "user", "content": prompt},
            ],
        )

        element_key = response.choices[0].message.content.strip()

        
        if element_key != "None" and element_key in elements:
            try:

                element_index = int(element_key.split("_")[1]) # extract index
                locator = page.locator("*").nth(element_index) # locate using nth index
                await locator.click()
                logger.info(f"Performed task: {task} by clicking on {element_key}")
            except Exception as e:
                logger.error(f"Error performing task: {e}")
        else:
            logger.warning(f"No suitable element found for task: {task}")


    except Exception as e:  # Catch exceptions related to OpenAI API
        logger.error(f"OpenAI API error: {e}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set headless=True for production
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://parabank.parasoft.com/parabank/index.htm")  # Replace with your target URL

        await perform_task(page, "Click on the more information link.")  # Example task
        await perform_task(page, "Click the link.")  # Example task

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())