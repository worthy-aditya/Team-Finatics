"""
Nmap scanner wrapper for SentinelAI
"""


class Scanner:
    """Base scanner class"""
    
    def __init__(self, target):
        self.target = target
        self.results = None
    
    def scan(self):
        """Execute scan"""
        raise NotImplementedError
    
    def get_results(self):
        """Return scan results"""
        return self.results


class NmapScanner(Scanner):
    """Nmap-based security scanner"""
    
    def __init__(self, target):
        super().__init__(target)
        self.nm = None
    
    def scan(self, args=""):
        """Execute Nmap scan"""
        raise NotImplementedError("Will implement in Day 3")
    
    def parse_results(self):
        """Parse and return Nmap output"""
        raise NotImplementedError("Will implement in Day 4-5")
