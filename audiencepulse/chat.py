
import os
import streamlit as st
from groq import Groq
from typing import List, Dict

def get_chat_response(messages: List[Dict], analysis_context: Dict = None) -> str:
    """
    Get a response from the Groq LLM for the chat interface.
    
    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."}
        analysis_context: Optional dictionary containing creator audit results
    """
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "⚠️ Error: GROQ_API_KEY not found. Please set it in your .env file or environment variables."

    client = Groq(api_key=api_key)

    # Construct System Prompt with Context
    system_content = """You are the Senior Analyst for AudiencePulse, an elite agency vetting tool.
    Your goal is to help media buyers and brands understand if a creator is a good fit for their product.
    
    Focus on:
    - Audience Spending Power (Can they afford it?)
    - Brand Safety (Is the creator risky?)
    - Authentic Fit (Do they actually like the brand?)
    
    Be concise, professional, but insightful. Use data from the audit where possible.
    """
    
    if analysis_context:
        # Flatten context for prompt
        fit = analysis_context.get('creator_fit', {})
        dna = analysis_context.get('audience_dna', {})
        trust = analysis_context.get('community_health', {}).get('trust', {})
        
        context_str = f"""
        ACIVE AUDIT CONTEXT:
        - Creator Fit Score: {fit.get('score')}/100 ({fit.get('grade')})
        - Verdict: {fit.get('verdict')}
        - Spending Power: {dna.get('spending_power', {}).get('verdict')} ({dna.get('spending_power', {}).get('premium_score')}% Premium)
        - Dominant Persona: {dna.get('personas', {}).get('dominant')}
        - Trust Score: {trust.get('score')}
        - Key Failure Reasons: {fit.get('failure_reason', 'None')}
        """
        system_content += context_str

    # Prepare messages
    final_messages = [{"role": "system", "content": system_content}]
    
    # Add recent history (Limit to last 10 to save context)
    final_messages.extend(messages[-10:])
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=final_messages,
            temperature=0.7,
            max_tokens=400,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"
