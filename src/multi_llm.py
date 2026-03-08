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
    """Supported LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    GROQ = "groq"
    GROK = "grok"
    UNKNOWN = "unknown"


# API Key patterns for auto-detection
API_KEY_PATTERNS = {
    LLMProvider.OPENAI: [r"^sk-[a-zA-Z0-9]{48}$", r"^sk-proj-[a-zA-Z0-9]{48}$"],
    LLMProvider.GEMINI: [r"^AIza[a-zA-Z0-9_-]{35}$"],
    LLMProvider.CLAUDE: [r"^sk-ant-[a-zA-Z0-9_-]{90,}$"],
    LLMProvider.GROQ: [r"^gsk_[a-zA-Z0-9]{52}$"],
    LLMProvider.GROK: [r"^xai-[a-zA-Z0-9]{64}$"],
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
    
    # Fallback: check prefixes
    if api_key.startswith("sk-") and not api_key.startswith("sk-ant"):
        return LLMProvider.OPENAI
    elif api_key.startswith("sk-ant"):
        return LLMProvider.CLAUDE
    elif api_key.startswith("AIza"):
        return LLMProvider.GEMINI
    elif api_key.startswith("gsk_"):
        return LLMProvider.GROQ
    elif api_key.startswith("xai-"):
        return LLMProvider.GROK
    
    return LLMProvider.UNKNOWN


def get_llm_client(provider: LLMProvider, api_key: str) -> Optional[Any]:
    """
    Create LLM client based on provider.
    
    Args:
        provider: LLM provider enum
        api_key: API key for the provider
        
    Returns:
        LLM client instance or None if unavailable
    """
    if provider == LLMProvider.UNKNOWN:
        return None
    
    try:
        if provider == LLMProvider.OPENAI:
            from openai import OpenAI
            return OpenAI(api_key=api_key)
        
        elif provider == LLMProvider.GEMINI:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-pro')
        
        elif provider == LLMProvider.CLAUDE:
            from anthropic import Anthropic
            return Anthropic(api_key=api_key)
        
        elif provider == LLMProvider.GROQ:
            from langchain_groq import ChatGroq
            return ChatGroq(model="llama-3.1-70b-versatile", api_key=api_key)
        
        elif provider == LLMProvider.GROK:
            from openai import OpenAI
            # Grok uses OpenAI-compatible API
            return OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
        
        else:
            return None
            
    except ImportError as e:
        print(f"Warning: Required package for {provider.value} not installed: {e}")
        return None
    except Exception as e:
        print(f"Error creating {provider.value} client: {e}")
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
        LLMProvider.OPENAI: "OpenAI (GPT)",
        LLMProvider.GEMINI: "Google Gemini",
        LLMProvider.CLAUDE: "Anthropic Claude",
        LLMProvider.GROQ: "Groq (Llama)",
        LLMProvider.GROK: "xAI Grok",
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
    Invoke LLM with prompt and return response.
    
    Args:
        client: LLM client instance
        provider: LLM provider enum
        prompt: Input prompt
        **kwargs: Additional provider-specific arguments
        
    Returns:
        LLM response text
    """
    temperature = kwargs.get('temperature', 0.1)
    max_tokens = kwargs.get('max_tokens', 4096)
    
    try:
        if provider == LLMProvider.OPENAI or provider == LLMProvider.GROK:
            response = client.chat.completions.create(
                model="gpt-4o-mini" if provider == LLMProvider.OPENAI else "grok-beta",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        elif provider == LLMProvider.GEMINI:
            response = client.generate_content(prompt)
            return response.text
        
        elif provider == LLMProvider.CLAUDE:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        elif provider == LLMProvider.GROQ:
            response = client.invoke(prompt)
            return response.content
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")
            
    except Exception as e:
        raise Exception(f"LLM invocation failed for {provider.value}: {str(e)}")


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
    Render API configuration UI in sidebar.
    Returns selected provider and API key.
    """
    import streamlit as st
    
    with st.sidebar:
        st.markdown("### 🔑 API Configuration")
        
        # Mode selection
        config_mode = st.radio(
            "Configuration Mode",
            ["Environment Variables (Local)", "Manual Entry (Cloud)"],
            help="Use environment variables for local development or manually enter API keys for cloud deployment"
        )
        
        selected_provider = None
        api_key = None
        
        if config_mode == "Environment Variables (Local)":
            st.info("💡 Set API keys in your .env file or environment variables")
            st.code("""
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
XAI_API_KEY=xai-...
            """, language="bash")
            
            # Check for existing env vars
            available_env_keys = []
            env_var_map = {
                LLMProvider.OPENAI: "OPENAI_API_KEY",
                LLMProvider.GEMINI: "GEMINI_API_KEY",
                LLMProvider.CLAUDE: "ANTHROPIC_API_KEY",
                LLMProvider.GROQ: "GROQ_API_KEY",
                LLMProvider.GROK: "XAI_API_KEY"
            }
            
            for provider, env_var in env_var_map.items():
                if os.getenv(env_var):
                    available_env_keys.append(provider)
            
            if available_env_keys:
                st.success(f"✅ Found {len(available_env_keys)} API key(s) in environment")
                for provider in available_env_keys:
                    st.caption(f"- {get_provider_display_name(provider)}")
            
            # Provider selection
            provider_options = get_available_providers()
            selected_provider_str = st.selectbox(
                "Select LLM Provider",
                options=list(provider_options.keys()),
                format_func=lambda x: provider_options[x],
                key="provider_select"
            )
            
            if selected_provider_str:
                selected_provider = LLMProvider(selected_provider_str)
                env_var = env_var_map.get(selected_provider)
                if env_var:
                    api_key = os.getenv(env_var)
                    
        else:  # Manual Entry
            st.info("💡 Enter your API key below for cloud deployment")
            
            # Provider selection
            provider_options = get_available_providers()
            selected_provider_str = st.selectbox(
                "Select LLM Provider",
                options=list(provider_options.keys()),
                format_func=lambda x: provider_options[x],
                key="provider_select_manual"
            )
            
            if selected_provider_str:
                selected_provider = LLMProvider(selected_provider_str)
                
                # API key input
                api_key = st.text_input(
                    f"{get_provider_display_name(selected_provider)} API Key",
                    type="password",
                    help="Your API key will be used for this session only"
                )
                
                # Auto-detect provider from entered key
                if api_key:
                    detected = detect_provider_from_key(api_key)
                    if detected != LLMProvider.UNKNOWN and detected != selected_provider:
                        st.warning(
                            f"⚠️ This key appears to be for {get_provider_display_name(detected)}, "
                            f"not {get_provider_display_name(selected_provider)}"
                        )
                    
                    if validate_api_key(api_key):
                        st.success("✅ Valid API key format")
                    else:
                        st.error("❌ Invalid API key format")
        
        st.divider()
        
        # Display configured providers
        if 'llm_manager' in st.session_state:
            configured = st.session_state.llm_manager.list_configured_providers()
            if configured:
                st.markdown("#### Configured Providers")
                for provider in configured:
                    st.caption(f"✅ {get_provider_display_name(provider)}")
        
        return selected_provider, api_key, config_mode
