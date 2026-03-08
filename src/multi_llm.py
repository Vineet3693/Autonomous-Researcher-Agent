"""
Multi-LLM Provider Support Module
Supports: OpenAI, Gemini, Claude, Groq, Grok
Includes auto-detection of API key providers
"""

import os
import re
from typing import Optional, Any, Dict
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM provider (Groq only)."""
    GROQ = "groq"
    UNKNOWN = "unknown"


# API Key patterns for auto-detection (Groq only)
API_KEY_PATTERNS = {
    LLMProvider.GROQ: [r"^gsk_[a-zA-Z0-9]{52}$"],
}


def detect_provider_from_key(api_key: str) -> LLMProvider:
    """
    Auto-detect LLM provider based on API key format.
    
    Args:
        api_key: The API key string to analyze
        
    Returns:
        Detected LLMProvider enum value
    """
    if not api_key or not isinstance(api_key, str):
        return LLMProvider.UNKNOWN
    
    api_key = api_key.strip()
    
    for provider, patterns in API_KEY_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, api_key):
                return provider
    
    # Fallback: check Groq prefix
    if api_key.startswith("gsk_"):
        return LLMProvider.GROQ
    
    return LLMProvider.UNKNOWN


def get_llm_client(provider: LLMProvider, api_key: str) -> Optional[Any]:
    """
    Create Groq LLM client.
    
    Args:
        provider: LLM provider enum (should be GROQ)
        api_key: API key for Groq
        
    Returns:
        Groq LLM client instance or None if unavailable
    """
    if provider != LLMProvider.GROQ:
        return None
    
    try:
        from langchain_groq import ChatGroq
        return ChatGroq(model="llama-3.1-70b-versatile", api_key=api_key)
    except ImportError as e:
        print(f"Warning: langchain_groq not installed: {e}")
        return None
    except Exception as e:
        print(f"Error creating Groq client: {e}")
        return None


def validate_api_key(api_key: str, provider: Optional[LLMProvider] = None) -> bool:
    """
    Validate API key format for a given provider.
    
    Args:
        api_key: API key to validate
        provider: Optional provider to validate against
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key or len(api_key) < 10:
        return False
    
    if provider and provider != LLMProvider.UNKNOWN:
        detected = detect_provider_from_key(api_key)
        return detected == provider
    
    return detect_provider_from_key(api_key) != LLMProvider.UNKNOWN


def get_provider_display_name(provider: LLMProvider) -> str:
    """Get human-readable provider name."""
    names = {
        LLMProvider.GROQ: "Groq (Llama)",
        LLMProvider.UNKNOWN: "Unknown Provider"
    }
    return names.get(provider, provider.value)


def get_available_providers() -> Dict[str, str]:
    """
    Get dictionary of available providers with their display names.
    
    Returns:
        Dict mapping provider values to display names
    """
    return {
        provider.value: get_provider_display_name(provider)
        for provider in LLMProvider
        if provider != LLMProvider.UNKNOWN
    }


def invoke_llm(client: Any, provider: LLMProvider, prompt: str, **kwargs) -> str:
    """
    Invoke Groq LLM with prompt and return response.
    
    Args:
        client: Groq LLM client instance
        provider: LLM provider enum (should be GROQ)
        prompt: Input prompt
        **kwargs: Additional arguments
        
    Returns:
        LLM response text
    """
    if provider != LLMProvider.GROQ:
        raise ValueError(f"Only Groq provider is supported")
    
    try:
        response = client.invoke(prompt)
        return response.content
    except Exception as e:
        raise Exception(f"LLM invocation failed for Groq: {str(e)}")


class MultiLLMManager:
    """
    Manager for handling multiple LLM providers and API keys.
    Supports switching between providers and caching clients.
    """
    
    def __init__(self):
        self._clients: Dict[LLMProvider, Any] = {}
        self._api_keys: Dict[LLMProvider, str] = {}
        self._current_provider: Optional[LLMProvider] = None
    
    def add_api_key(self, api_key: str, provider: Optional[LLMProvider] = None) -> LLMProvider:
        """
        Add API key and auto-detect or use specified provider.
        
        Args:
            api_key: API key string
            provider: Optional explicit provider
            
        Returns:
            Detected or specified provider
        """
        if provider is None:
            provider = detect_provider_from_key(api_key)
        
        if provider == LLMProvider.UNKNOWN:
            raise ValueError("Could not detect API key provider")
        
        self._api_keys[provider] = api_key
        self._clients[provider] = get_llm_client(provider, api_key)
        
        if self._current_provider is None:
            self._current_provider = provider
        
        return provider
    
    def set_current_provider(self, provider: LLMProvider) -> bool:
        """Set current active provider."""
        if provider in self._clients:
            self._current_provider = provider
            return True
        return False
    
    def get_current_client(self) -> Optional[Any]:
        """Get current LLM client."""
        if self._current_provider:
            return self._clients.get(self._current_provider)
        return None
    
    def get_current_provider(self) -> Optional[LLMProvider]:
        """Get current provider enum."""
        return self._current_provider
    
    def list_configured_providers(self) -> list:
        """List all configured providers."""
        return list(self._api_keys.keys())
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Invoke current LLM with prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional arguments
            
        Returns:
            LLM response
        """
        if not self._current_provider or self._current_provider not in self._clients:
            raise ValueError("No LLM provider configured")
        
        client = self._clients[self._current_provider]
        return invoke_llm(client, self._current_provider, prompt, **kwargs)


# Convenience functions for Streamlit
def initialize_multi_llm_session_state():
    """Initialize session state variables for multi-LLM support."""
    import streamlit as st
    
    if 'llm_manager' not in st.session_state:
        st.session_state.llm_manager = MultiLLMManager()
    if 'selected_provider' not in st.session_state:
        st.session_state.selected_provider = None
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {}


def render_api_configuration_sidebar():
    """
    Render API configuration UI in sidebar for Groq only.
    Returns selected provider and API key.
    """
    import streamlit as st
    
    with st.sidebar:
        st.markdown("### 🔑 API Configuration")
        
        # Mode selection
        config_mode = st.radio(
            "Configuration Mode",
            ["Environment Variables (Local)", "Manual Entry (Cloud)"],
            help="Use environment variables for local development or manually enter API key for cloud deployment"
        )
        
        selected_provider = LLMProvider.GROQ
        api_key = None
        
        if config_mode == "Environment Variables (Local)":
            st.info("💡 Set API key in your .env file or environment variable")
            st.code("GROQ_API_KEY=gsk_...", language="bash")
            
            # Check for Groq env var
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                st.success("✅ Groq API key found in environment")
            else:
                st.warning("⚠️ GROQ_API_KEY not set in environment")
                    
        else:  # Manual Entry
            st.info("💡 Enter your Groq API key below")
            
            # API key input
            api_key = st.text_input(
                "Groq API Key",
                type="password",
                help="Your API key will be used for this session only. Get one at https://console.groq.com"
            )
            
            # Validate key format
            if api_key:
                if validate_api_key(api_key):
                    st.success("✅ Valid Groq API key format")
                else:
                    st.error("❌ Invalid API key format. Groq keys start with 'gsk_'")
        
        st.divider()
        
        # Display configured providers
        if 'llm_manager' in st.session_state:
            configured = st.session_state.llm_manager.list_configured_providers()
            if configured:
                st.markdown("#### Configured Provider")
                for provider in configured:
                    st.caption(f"✅ {get_provider_display_name(provider)}")
        
        return selected_provider, api_key, config_mode
