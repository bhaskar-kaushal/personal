"""
EPAM DIAL API Client for OpenAI access.

This module provides a simple interface to interact with OpenAI models
through EPAM's DIAL service.
"""

import os
from openai import AzureOpenAI
from typing import List, Dict, Any, Optional


class DIALClient:
    """
    Client for interacting with EPAM DIAL API.
    
    Example usage:
        client = DIALClient()
        response = client.get_completion([
            {"role": "user", "content": "Hello, how can I help you?"}
        ])
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize DIAL client.
        
        Args:
            api_key: DIAL API key (will use DIAL_API_KEY env var if not provided)
            model: Model name to use (default: gpt-4)
        """
        self.api_key = api_key or os.getenv("DIAL_API_KEY", "<YOUR_API_KEY_HERE>")
        self.model = model
        self.azure_endpoint = "https://ai-proxy.lab.epam.com"
        self.api_version = "2024-02-01"
        
        # Initialize Azure OpenAI client
        try:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.azure_endpoint
            )
            
            if not self.api_key or self.api_key == "<YOUR_API_KEY_HERE>":
                print("🚨 DIAL API Key not found. Please set the DIAL_API_KEY environment variable.")
                self.client = None
            else:
                print("✅ DIAL Client initialized successfully!")
                
        except Exception as e:
            print(f"🔥 Error initializing DIAL client: {e}")
            self.client = None
    
    def get_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        """
        Get completion from DIAL API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Override default model for this request
            
        Returns:
            Response content from the model
        """
        if not self.client:
            return "❌ DIAL client not properly initialized. Please check your API key."
        
        try:
            response = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=float(os.getenv("DIAL_TEMPERATURE", "0.7"))
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error calling DIAL API: {e}"
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis result
        """
        messages = [
            {
                "role": "system",
                "content": "You are a sentiment analysis expert. Analyze the sentiment of the given text and respond with: POSITIVE, NEGATIVE, or NEUTRAL, followed by a brief explanation."
            },
            {
                "role": "user",
                "content": f"Analyze the sentiment of this text: '{text}'"
            }
        ]
        return self.get_completion(messages)
    
    def generate_response(self, context: str, customer_query: str) -> str:
        """
        Generate customer service response based on context.
        
        Args:
            context: Hotel context information
            customer_query: Customer's question or request
            
        Returns:
            Generated response
        """
        messages = [
            {
                "role": "system",
                "content": "You are a helpful hotel customer service agent. Provide friendly, professional responses to customer queries based on the given context."
            },
            {
                "role": "user",
                "content": f"Context: {context}\n\nCustomer Query: {customer_query}\n\nProvide a helpful response:"
            }
        ]
        return self.get_completion(messages)


# Test function to verify DIAL connectivity
def test_dial_connection():
    """Test DIAL API connection and basic functionality."""
    print("🧪 Testing DIAL API connection...")
    
    client = DIALClient()
    
    if not client.client:
        print("❌ DIAL client initialization failed")
        return False
    
    # Test basic completion
    test_messages = [
        {"role": "user", "content": "Explain the concept of 'technical debt' in one sentence."}
    ]
    
    response = client.get_completion(test_messages)
    print(f"📝 Test Response: {response}")
    
    if "Error" not in response:
        print("✅ DIAL API test successful!")
        return True
    else:
        print("❌ DIAL API test failed")
        return False


if __name__ == "__main__":
    # Run connection test
    test_dial_connection()