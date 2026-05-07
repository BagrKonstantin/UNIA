import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from langchain_core.tools import tool

def fetch_page_content(url: str) -> str:
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            # Extract text and remove excessive whitespace
            text = soup.get_text(separator=' ', strip=True)
            return text
    except Exception as e:
        return f"Could not fetch content from {url}: {e}"
    return ""

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

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

def summarize_content(content: str, query: str) -> str:
    if len(content) < 50:
        return content
    # Using the same model as in main.py
    llm = ChatOllama(model="gemma4:e4b", temperature=0)
    prompt = f"You are a summarization assistant. Extract all information relevant to the user's query: '{query}'. Focus especially on specific details like deadlines, application procedures, or contact info. If the information is not present, just say 'Not found'.\n\nText:\n{content[:6000]}"
    try:
        res = llm.invoke([HumanMessage(content=prompt)])
        return res.content
    except Exception as e:
         return f"Failed to summarize: {e}"

@tool
def deep_search_unilu(query: str) -> str:
    """
    Perform a deep search on the University of Luxembourg (uni.lu) website.
    This tool reads the full text of the top 3 search results and uses AI to summarize the contents to precisely answer the query.
    Use this when the user asks about deep details, complex requirements, or application deadlines that might be hidden inside the program's webpage.
    """
    modified_query = f"site:uni.lu {query}"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(modified_query, max_results=3))
        
        if not results:
            return "No results found on uni.lu for your query."

        import re
        full_content = []
        visited_links = set()
        
        for res in results:
            link = res.get('href')
            if link in visited_links:
                continue
            visited_links.add(link)
            print(f"Deep scraping: {link}")
            title = res.get('title')
            
            content_raw = fetch_page_content(link)[:4000]
            
            # # Sub-page heuristic: If it's a study program, also fetch the admissions page just in case
            # match = re.search(r"(https?://(?:www\.)?uni\.lu/[^/]+/study-programs/[^/]+)", link)
            # if match:
            #     admission_link = match.group(1) + "/admissions/"
            #     if admission_link not in visited_links and admission_link != link:
            #         visited_links.add(admission_link)
            #         print(f"Also scraping admissions page: {admission_link}")
            #         adm_content = fetch_page_content(admission_link)
            #         if adm_content:
            #             content_raw += f"\n\n--- ADMISSIONS PAGE ({admission_link}) ---\n\n" + adm_content

            if not content_raw:
                continue
                
            summary = summarize_content(content_raw, query)
            
            entry = f"=== Source: {title} ({link}) ===\n{summary}"
            full_content.append(entry)
            
        return "\n\n".join(full_content)
    except Exception as e:
        return f"Error executing deep search: {str(e)}"
