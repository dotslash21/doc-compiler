import logging
from typing import Dict, List

import openai

from config import OPENAI_API_BASE_URL


class ContentConsolidator:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """Initialize the consolidator with OpenAI API key and model."""
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key
        if OPENAI_API_BASE_URL:
            openai.api_base = OPENAI_API_BASE_URL
        self.logger = logging.getLogger(__name__)

    def _build_prompt(self, pages: List[Dict[str, str]]) -> str:
        """
        Build a prompt for the LLM that includes context about the pages
        and instructions for consolidation.
        """
        context = "\n\n".join(
            [
                f"Title: {page['title']}\n"
                f"URL: {page['url']}\n"
                f"Content: {page['content'][:500]}..."
                for page in pages
            ]
        )

        prompt = f"""
        You are tasked with consolidating documentation from multiple web pages into
        a single, well-organized markdown document. Below are excerpts from various
        pages, including their titles and URLs. Create a cohesive document that:

        1. Maintains the key information from each source
        2. Organizes content logically
        3. Includes relevant section headers
        4. Preserves important technical details
        5. Cites source URLs where appropriate

        Here are the source pages:

        {context}

        Please provide the consolidated documentation in markdown format.
        """
        return prompt

    def consolidate(self, pages: List[Dict[str, str]]) -> str:
        """
        Consolidate the content from multiple pages into a single markdown document
        using the OpenAI API.
        """
        try:
            prompt = self._build_prompt(pages)

            # Simple token count estimation (4 chars ~= 1 token)
            estimated_tokens = len(prompt) // 4
            if estimated_tokens > 8000:
                self.logger.warning("Content may exceed token limit. Truncating...")
                # Reduce pages until estimated tokens is under limit
                while estimated_tokens > 8000 and pages:
                    pages.pop()
                    prompt = self._build_prompt(pages)
                    estimated_tokens = len(prompt) // 4

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical documentation expert.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,  # Lower temperature for more focused output
            )

            markdown_content = response.choices[0].message.content
            return markdown_content

        except Exception as e:
            self.logger.error(f"Error during consolidation: {e}")
            raise
