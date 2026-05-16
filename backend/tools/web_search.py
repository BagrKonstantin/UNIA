import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from urllib.parse import urljoin
import re

def fetch_page_data(url: str) -> dict:
    """Fetch all text and links from a given URL."""
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Extract Links (before stripping tags for text)
        links = []
        for a in soup.find_all('a', href=True):
            link_text = a.get_text(strip=True)
            if not link_text:
                continue
            href = a['href']
            absolute_url = urljoin(url, href)
            if absolute_url.startswith('http'):
                links.append({"text": link_text, "url": absolute_url})
        
        # 2. Extract Text
        # remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        # remove redundant whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return {"text": text, "links": links}
    except Exception as e:
        return {"error": str(e)}

def fetch_page_content(url: str) -> str:
    """Old wrapper for text-only fetching, used by search_unilu."""
    data = fetch_page_data(url)
    return data.get("text", "")

@tool
def search_unilu(query: str) -> str:
    """
    Search the University of Luxembourg (uni.lu) website for answers to user's questions.
    Returns detailed content from the top official uni.lu search results, which is useful for finding specific details like application deadlines, requirements, and program overviews.
    """
    modified_query = f"site:uni.lu {query}"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(modified_query, max_results=3))
        
        if not results:
            return "No results found on uni.lu for your query."

        full_content = []
        for res in results:
            link = res.get('href')
            title = res.get('title')
            snippet = res.get('body')
            
            content = fetch_page_content(link)[:4000]
            
            entry = f"Title: {title}\nURL: {link}\nSnippet: {snippet}\nContent: {content}..."
            full_content.append(entry)
            
        return "\n\n---\n\n".join(full_content)
    except Exception as e:
        return f"Error executing search: {str(e)}"

@tool
def deep_search_unilu(query: str) -> str:
    """
    Perform a deep search on the University of Luxembourg (uni.lu) website.
    This tool fetches the top 3 results, scrapes the first page entirely (text & links), 
    and uses AI to answer the question or suggest specific follow-up links.
    """
    modified_query = f"site:uni.lu {query}"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(modified_query, max_results=3))
        
        if not results:
            return "No results found on uni.lu for your query."

        # As requested: take the first page from the 3 results
        first_res = results[0]
        link = first_res.get('href')
        title = first_res.get('title')
        
        # Fetch all text and links from the first page
        page_data = fetch_page_data(link)
        if "error" in page_data:
            return f"Failed to fetch {link}: {page_data['error']}"
        
        text = page_data["text"]
        links = page_data["links"]
        
        # Format unique links as markdown list
        seen_urls = set()
        formatted_links = []
        for l in links:
            if l['url'] not in seen_urls:
                formatted_links.append(f"- [{l['text']}]({l['url']})")
                seen_urls.add(l['url'])
        
        # Limit links to avoid overwhelming the model context
        links_str = "\n".join(formatted_links[:100])

        # Use the same model as in main.py
        llm = ChatOllama(model="gemma4:e4b", temperature=0)
        
        prompt = f"""You are a specialized Uni.lu assistant. 
User Question: {query}

Below is the full text content from the page "{title}" ({link}), followed by a list of links found on that page.

--- PAGE TEXT CONTENT ---
{text[:12000]}

--- LINKS ON THIS PAGE ---
{links_str}

--- INSTRUCTIONS ---
1. Determine if the user's question is answered by the "PAGE TEXT CONTENT" provided above.
2. If the answer is present, provide a clear and detailed answer.
3. If the answer is NOT present or incomplete, explicitly state "Information not fully found" and list the most relevant links from the "LINKS ON THIS PAGE" section that likely contain the answer.
4. Always conclude by mentioning the source: {link}
"""
        
        res = llm.invoke([HumanMessage(content=prompt)])
        return res.content

    except Exception as e:
        return f"Error executing deep search: {str(e)}"
