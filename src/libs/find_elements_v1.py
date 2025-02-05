from sentence_transformers import SentenceTransformer, util
import json
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, BrowserContext, Page, Locator

model = SentenceTransformer('all-mpnet-base-v2')  # Or a suitable model

async def find_element_by_task(page: Page, task: str) -> Optional[Dict]:
    interactive_elements = page.locator("a, button, input, [role='button']")
    locators = await interactive_elements.all()
    num_elements = len(locators)
    if num_elements == 0:
        return None

    task_embedding = model.encode(task)

    for i, locator in enumerate(locators):
        element_info = {
            "unique_identifier": str(i),
            "element_type": await locator.evaluate("el => el.tagName.toLowerCase()"),
            "label": await locator.text_content() or "", # Get label, handle missing labels
            "attributes": await locator.evaluate("el => {let attrs = {}; for (let {name, value} of el.attributes) {attrs[name] = value;} return attrs;}")
        }

        element_text = json.dumps(element_info, ensure_ascii=False)  # Use all info as text

        element_embedding = model.encode(element_text)
        similarity = util.cos_sim(task_embedding, element_embedding)

        print(f"similarity is '{similarity }'")

        if similarity > 0.2:  # Adjust threshold as needed
            element_info["locator"] = locator # add the locator info
            return element_info

    return None