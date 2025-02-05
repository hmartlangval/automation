#autoamting with tabbable option

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional
import logging
import pprint
logging.basicConfig(level=logging.INFO)


from openai import OpenAI
from playwright.async_api import async_playwright, BrowserContext, Page, Locator
from dotenv import load_dotenv

from libs.find_elements_v1 import find_element_by_task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

client = OpenAI(api_key=openai_api_key)


# async def find_element_by_task(page: Page, task: str) -> Optional[Dict]:
#     """Finds an interactive element related to the given task, using unique identifiers."""

#     interactive_elements = page.locator("a").or_locator(page.locator("button")).or_locator(page.locator("input")).or_locator(page.locator("[role='button']"))
#     locators = await interactive_elements.all()
#     num_elements = len(locators)

#     if num_elements == 0:
#         return None

#     current_index = 0
#     await locators[current_index].focus()

#     for _ in range(num_elements):
#         locator = locators[current_index]
#         label = await locator.inner_text()

#         if label:
#             unique_identifier = f"{current_index}"
#             element_id = await locator.get_attribute("id")
#             if element_id:
#                 unique_identifier += f"-{element_id}"
#             name = await locator.get_attribute("name")
#             if name:
#                 unique_identifier += f"-{name}"
#             if label:  # Include label in unique identifier
#                 unique_identifier += f"-{label}"

#             element_type = await locator.evaluate("el => el.tagName.toLowerCase()")
#             print(f"element type: '{element_type}'")

#             prompt = f"""Is the label "{label}" or element type "{element_type}" relevant to the task: "{task}"? Answer with "yes" or "no"."""
#             try:
#                 response = client.chat.completions.create(
#                     model="gpt-3.5-turbo",
#                     messages=[
#                         {"role": "system", "content": "You are a helpful assistant determining the relevance of text to a task."},
#                         {"role": "user", "content": prompt},
#                     ],
#                 )
#                 relevance = response.choices[0].message.content.strip().lower()

#                 if relevance == "yes":
#                     element_info = {
#                         "unique_identifier": unique_identifier,  # Store unique identifier
#                         "label": label,
#                         "element_type": await locator.evaluate("el => el.tagName.toLowerCase()"),
#                     }
#                     return element_info  # Return the element info including unique identifier
#             except Exception as e:
#                 logger.error(f"OpenAI API error during relevance check: {e}")

#         current_index = (current_index + 1) % num_elements
#         await locators[current_index].focus()

#     return None  # No matching element found


async def perform_action(page: Page, element_info: Dict):
    """Performs a click action on the given element, handling missing IDs."""

    try:
        if "locator" in element_info:  # Check if the locator is present
            locator = element_info["locator"]  # Retrieve the locator
            try:
                await locator.click(timeout=5000)  # Use the locator directly
                logger.info(f"Clicked on element: {element_info.get('label', 'N/A')}")
            except Exception as e:
                logger.error(f"Error clicking element: {e}")
        else:
            logger.warning("Element information is missing locator. Cannot perform action.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during click: {e}")


    # try:
    #     if "element_id" in element_info and element_info["element_id"]:  # Check if ID exists and is not empty
    #         locator = page.locator(f"[id='{element_info['element_id']}']")
    #         try: # try to click it
    #             await locator.click(timeout=5000) # click with timeout
    #             logger.info(f"Clicked on element (by ID): {element_info['label']}")
    #         except Exception as e:
    #             logger.error(f"Error clicking element (by ID): {e}")
    #     elif "label" in element_info and element_info["label"]: # Fallback to label if ID is missing
    #         locator = page.locator(f"text={element_info['label']}") # Robust to handle different cases
    #         try:
    #             await locator.click(timeout=5000) # click with timeout
    #             logger.info(f"Clicked on element (by label): {element_info['label']}")
    #         except Exception as e:
    #             logger.error(f"Error clicking element (by label): {e}")
    #     else:
    #         logger.warning("Element information is missing ID and label. Cannot perform action.")

    # except Exception as e: # Catch all exceptions
    #     logger.error(f"An unexpected error occurred during click: {e}") # Log error


async def findAndClickThisTask(page:Page, task: str):

    matching_element = await find_element_by_task(page, task)
    if matching_element:
        print("found matching element")
        logging.info(pprint.pformat(matching_element))
        # print(f"Found matching element:\n{json.dumps(matching_element, indent=2)}")
        await perform_action(page, matching_element) # click on the element
    else:
        print(f"No element found matching the task: {task}")

