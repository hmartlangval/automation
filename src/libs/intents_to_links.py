import asyncio
import json
import logging
from typing import Dict, List, Optional

from sentence_transformers import SentenceTransformer, util
from playwright.async_api import Page

logging.getLogger('sentence_transformers').setLevel(logging.ERROR)  # Suppress INFO and DEBUG messages

# Configure logging (if not already configured globally)
logging.basicConfig(level=logging.error)
logger = logging.getLogger(__name__)

# Load a suitable sentence transformer model
model = SentenceTransformer('all-mpnet-base-v2')  # Or try 'multi-qa-mpnet-base-dot-v1' or 'all-MiniLM-L6-v2'


async def map_intent_to_link(page: Page, user_intent: str, similarity_threshold: float = 0.4) -> Optional[Dict]:
    """Maps a user intent to a clickable link on the page.

    Args:
        page: The Playwright Page object.
        user_intent: The user's intent as a string.
        similarity_threshold: The minimum cosine similarity for a match.

    Returns:
        A dictionary containing information about the best matching link (or None if no match is found).
        The dictionary will include "label", "href" (if available), "locator", and other info.
    """

    try:
        links = await page.locator("a, button, input, [role='button']").all()  # Get all links on the page
        num_links = len(links)

        if num_links == 0:
            return None

        best_match = None
        highest_similarity = 0

        intent_embedding = model.encode(user_intent)

        for i, link_locator in enumerate(links):
            link_text = await link_locator.text_content() or ""
            href = await link_locator.get_attribute("href") or ""

            # Create a combined text representation for the link, including text and href
            link_representation = f"{link_text} {href}" # Combine link text and href

            link_embedding = model.encode(link_representation)
            similarity = util.cos_sim(intent_embedding, link_embedding)[0][0] # Extract similarity value


            # logger.info(f"Similarity between intent '{user_intent}' and link '{link_text}': {similarity}")
            logger.info(f"Similarity check: '{link_text}': {similarity}")

            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = {
                    "label": link_text,
                    "href": href,
                    "locator": link_locator,  # Store the locator for easy clicking later
                    "similarity": similarity,
                    "index": i # Store the index
                }

        if best_match and best_match["similarity"] >= similarity_threshold:
            return best_match
        else:
            return None  # No match found above the threshold

    except Exception as e:
        logger.error(f"Error mapping intent to link: {e}")
        return None
