# Doc Compiler

A Python tool that crawls documentation pages and uses LLMs to consolidate them into a single markdown document.

## Features

- Crawls documentation pages starting from an entry URL with configurable depth
- Handles both static and dynamic (JavaScript-rendered) pages using requests and Selenium
- Removes non-essential elements like navigation bars and footers
- Uses OpenAI's GPT models to consolidate content into a well-organized markdown document
- Includes source URLs and maintains important technical details
- Handles token limits gracefully by truncating content when needed

## Requirements

- Python 3.12 or higher
- Chrome WebDriver (for Selenium)
- OpenAI API key

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd doc-compiler
   ```

2. Install dependencies:
   ```bash
   pip install .
   ```

3. Set up your OpenAI API key:
   ```bash
   # On Windows
   set OPENAI_API_KEY=your-api-key-here
   
   # On Linux/macOS
   export OPENAI_API_KEY=your-api-key-here
   ```

## Usage

Basic usage:
```bash
python main.py https://example.com/docs
```

With optional parameters:
```bash
python main.py https://example.com/docs --depth 3 --output custom_output.md --model gpt-4
```

### Parameters

- `url`: Entry point URL for crawling (required)
- `--depth`: Maximum crawling depth (default: 2)
- `--output`: Output markdown file path (default: output.md)
- `--model`: OpenAI model to use (default: gpt-3.5-turbo)

## Logging

The tool logs its progress to both the console and a `doc_compiler.log` file, including:
- Crawling progress and successful page fetches
- Warnings about skipped pages or content truncation
- Any errors that occur during execution

## Error Handling

- Invalid URLs are logged and skipped
- Pages that fail to load with requests are attempted with Selenium
- Content exceeding token limits is automatically truncated
- Missing OpenAI API key results in a clear error message
