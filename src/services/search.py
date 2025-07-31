class SearchEngine:
    """Base class for search engines"""
    def __init__(self):
        self.name = "Search Engine"
    
    def search(self, query: str) -> list:
        """Placeholder search method"""
        return [f"{self.name} result for '{query}'"]


class BingSearch(SearchEngine):
    """Bing search implementation"""
    def __init__(self):
        super().__init__()
        self.name = "Bing"


class GoogleSearch(SearchEngine):
    """Google search implementation"""
    def __init__(self):
        super().__init__()
        self.name = "Google"


class DuckDuckGoSearch(SearchEngine):
    """DuckDuckGo search implementation"""
    def __init__(self):
        super().__init__()
        self.name = "DuckDuckGo"
