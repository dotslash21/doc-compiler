### 1. Initialization & Setup

- **Inputs:**  
  - Entry point URL (e.g., `https://spark.apache.org/docs/latest/`)
  - Maximum crawling depth

- **Python Libraries:**  
  - **HTTP & Parsing:** `requests`, `BeautifulSoup` (from `bs4`), `urllib.parse`  
  - **Dynamic Content:** `Selenium` (or similar, e.g., `Playwright`)  
  - **LLM API:** `openai` (or LM Studio’s compatible package)  
  - **Logging & Error Handling:** Python’s `logging` module

---

### 2. Web Crawling

- **Synchronous Crawler:**  
  - Start from the entry URL and restrict crawling to URLs with the same prefix.  
  - Use a recursive or iterative approach with a maximum depth parameter.

- **URL Processing:**  
  - Utilize `urllib.parse` to normalize and check URL prefixes.

- **Error Handling:**  
  - Catch HTTP errors, timeouts, and invalid URLs with proper logging.

---

### 3. Content Extraction & Cleaning

- **HTML Parsing:**  
  - Use BeautifulSoup to extract all text from each page.

- **Filtering Non-essential Elements:**  
  - Remove elements like navbars and footers using known HTML selectors (e.g., `<nav>`, `<footer>`, or specific class/id names).

- **Metadata Collection:**  
  - Extract and store page title, URL, and any other relevant metadata alongside the cleaned text.

---

### 4. Content Consolidation via LLM

- **Prompt Construction:**  
  - Build a short, precise prompt for the LLM that instructs it to consolidate the collected texts into a single markdown file.  
  - Ensure the prompt includes page titles and metadata as context.

- **Token Management:**  
  - Check total content tokens against the 8096 limit. If exceeded, summarize or partition the content before final consolidation.

- **API Call:**  
  - Use the OpenAI-compatible API to send the prompt and receive markdown-formatted output.

---

### 5. Output

- **File Generation:**  
  - Save the final markdown output to a file for downstream LLM consumption.
  
- **Logging & Final Checks:**  
  - Log the completion of tasks and handle any errors that arise during the API call or file write process.

---

### 6. Future Enhancements

- **Asynchronous Crawling:**  
  - Consider asynchronous methods if performance becomes an issue.
  
- **Enhanced Dynamic Content Handling:**  
  - Expand dynamic content support beyond basic Selenium usage if needed.

- **Modularity:**  
  - Keep components (crawling, extraction, summarization, and output) modular to ease future modifications.
