try:
    from ddgs import DDGS
    HAS_DDG = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        HAS_DDG = True
    except ImportError:
        HAS_DDG = False

def web_search(query, max_results=3):
    if not HAS_DDG:
        return "Web search unavailable."
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                body = r.get('body', '')
                title = r.get('title', '')
                if body:
                    results.append(f"Info ({title}): {body}")
        return "\n".join(results) if results else "No info found."
    except Exception as e:
        return f"Search error: {str(e)}"