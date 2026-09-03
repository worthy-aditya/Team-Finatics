"""
LLM Prompt Engine for SentinelAI
Handles integration with AI/LLM services for security analysis
"""

from typing import Dict, Optional, List
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def analyze_scan(self, scan_data: Dict) -> Dict:
        """
        Analyze Nmap scan results using LLM
        
        Args:
            scan_data (Dict): LLM-ready formatted scan output
        
        Returns:
            Dict: Analysis results with insights and recommendations
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4o provider - TO BE IMPLEMENTED BY ADITYA"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model = "gpt-4o"
    
    def analyze_scan(self, scan_data: Dict) -> Dict:
        """
        Analyze scan using OpenAI GPT-4o
        
        Args:
            scan_data (Dict): Scan data from NmapScanner.get_llm_ready_format()
        
        Returns:
            Dict: LLM analysis with security insights
        """
        # TODO: Implement OpenAI API call
        return {
            "provider": "openai",
            "model": self.model,
            "status": "not_implemented",
            "message": "OpenAI provider implementation pending"
        }


class ClaudeProvider(LLMProvider):
    """Claude provider - TO BE IMPLEMENTED BY ADITYA"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model = "claude-3-opus"
    
    def analyze_scan(self, scan_data: Dict) -> Dict:
        """
        Analyze scan using Claude
        
        Args:
            scan_data (Dict): Scan data from NmapScanner.get_llm_ready_format()
        
        Returns:
            Dict: LLM analysis with security insights
        """
        # TODO: Implement Claude API call
        return {
            "provider": "claude",
            "model": self.model,
            "status": "not_implemented",
            "message": "Claude provider implementation pending"
        }


class OllamaProvider(LLMProvider):
    """Local Ollama provider - TO BE IMPLEMENTED BY ADITYA"""
    
    def __init__(self, model: str = "mistral"):
        self.model = model
        self.endpoint = "http://localhost:11434"
    
    def analyze_scan(self, scan_data: Dict) -> Dict:
        """
        Analyze scan using local Ollama
        
        Args:
            scan_data (Dict): Scan data from NmapScanner.get_llm_ready_format()
        
        Returns:
            Dict: LLM analysis with security insights
        """
        # TODO: Implement Ollama API call
        return {
            "provider": "ollama",
            "model": self.model,
            "status": "not_implemented",
            "message": "Ollama provider implementation pending"
        }


class PromptEngine:
    """
    Main prompt engine for coordinating LLM analysis
    """
    
    # Security analysis prompt template
    SECURITY_ANALYSIS_PROMPT = """
    Analyze the following network scan results and provide security insights:
    
    SCAN DATA:
    {scan_data}
    
    Please provide:
    1. Summary of findings
    2. Identified vulnerabilities and risks
    3. Critical issues requiring immediate attention
    4. Recommendations for remediation
    5. Compliance implications (OWASP Top 10, MITRE ATT&CK)
    
    Format your response as a structured analysis with clear sections.
    """
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        Initialize PromptEngine with specified provider
        
        Args:
            provider (str): LLM provider to use ("openai", "claude", "ollama")
            api_key (Optional[str]): API key for the provider
        """
        self.provider_name = provider
        self.api_key = api_key
        self.llm_provider: Optional[LLMProvider] = None
        
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the appropriate LLM provider"""
        if self.provider_name.lower() == "openai":
            self.llm_provider = OpenAIProvider(self.api_key)
        elif self.provider_name.lower() == "claude":
            self.llm_provider = ClaudeProvider(self.api_key)
        elif self.provider_name.lower() == "ollama":
            self.llm_provider = OllamaProvider()
        else:
            raise ValueError(f"Unknown provider: {self.provider_name}")
    
    def analyze_scan_results(self, scan_data: Dict) -> Dict:
        """
        Analyze Nmap scan results using configured LLM
        
        Args:
            scan_data (Dict): Output from NmapScanner.get_llm_ready_format()
        
        Returns:
            Dict: Analysis result with security insights
        """
        if not self.llm_provider:
            return {"error": "No LLM provider initialized"}
        
        analysis = self.llm_provider.analyze_scan(scan_data)
        
        # Ensure response has expected structure
        return {
            "scan_target": scan_data.get("scan_metadata", {}).get("target"),
            "provider": self.provider_name,
            "analysis": analysis,
            "scan_statistics": scan_data.get("scan_statistics", {}),
            "timestamp": scan_data.get("scan_metadata", {}).get("scan_time")
        }

    def analyze_event_logs(self, events: List[Dict], event_analysis: Dict) -> Dict:
        """Create an LLM-ready threat assessment for parsed event logs.

        Provider implementations can replace this deterministic adapter later;
        keeping the result structured makes the CLI useful without credentials.
        """
        assessment = get_mock_event_analysis(events, event_analysis)
        return {
            "provider": self.provider_name,
            "status": "mock",
            "analysis": assessment,
        }
    
    def get_available_providers(self) -> List[str]:
        """Get list of available LLM providers"""
        return ["openai", "claude", "ollama"]
    
    def switch_provider(self, provider: str, api_key: Optional[str] = None):
        """
        Switch to a different LLM provider
        
        Args:
            provider (str): Provider name
            api_key (Optional[str]): API key for new provider
        """
        self.provider_name = provider
        self.api_key = api_key
        self._initialize_provider()


# Mock analysis for testing (TO BE REPLACED BY ACTUAL LLM RESPONSE)
def get_mock_analysis(scan_data: Dict) -> Dict:
    """
    Get mock analysis for testing without LLM
    
    Args:
        scan_data (Dict): Scan data from NmapScanner.get_llm_ready_format()
    
    Returns:
        Dict: Mock analysis result
    """
    stats = scan_data.get("scan_statistics", {})
    risk = scan_data.get("risk_assessment", {})
    
    return {
        "analysis_type": "security_assessment",
        "target": scan_data.get("scan_metadata", {}).get("target"),
        "findings_summary": f"Security scan detected {stats.get('open_ports')} open ports with risk level: {risk.get('risk_level', 'UNKNOWN')}",
        "vulnerabilities": [
            {
                "id": f"PORT_{port['port']}",
                "severity": "HIGH",
                "description": f"Service '{port['service_name']}' running on port {port['port']}",
                "remediation": "Review service necessity and apply access controls"
            }
            for port in scan_data.get("open_ports_detail", [])[:3]
        ],
        "recommendations": risk.get("recommendation", ""),
        "critical_issues": len(risk.get("critical_services", [])),
        "compliance_mapping": {
            "owasp_top_10": ["A02:2021 – Cryptographic Failures"],
            "mitre_attack": ["T1046 - Network Service Discovery"]
        }
    }


def get_mock_event_analysis(events: List[Dict], event_analysis: Dict) -> Dict:
    """Return a structured event-log assessment without a remote LLM."""
    return {
        "analysis_type": "event_log_analysis",
        "events_analyzed": len(events),
        "critical_events": event_analysis.get("critical_events_found", len(events)),
        "threat_level": event_analysis.get("threat_level", "UNKNOWN"),
        "threat_summary": (
            "Review the generated alerts and validate each action with an operator."
            if event_analysis.get("alerts")
            else "No suspicious patterns were identified in the supplied events."
        ),
        "findings": event_analysis.get("alerts", []),
        "recommendations": event_analysis.get("recommendations", []),
        "actions_recommended": [
            "Review event details and confirm whether each alert is authorized",
            "Preserve relevant logs before taking remediation action",
        ] if event_analysis.get("alerts") else [],
    }
