import pytest
from audiencepulse.creator_audit import calculate_creator_fit

def test_price_mismatch():
    """Test that a Budget Audience fails for a High Ticket Product."""
    dna = {'spending_power': {'premium_score': 10, 'budget_score': 90}} # Poor audience
    brand = {'brand_orbit': [], 'dominant_tier': 'budget'}
    health = {'trust': {'score_numeric': 80}} # High Trust
    
    # Product: ₹60,000 (Premium)
    context = {'price': 60000, 'name': 'Rolex', 'category': 'Fashion', 'tier': 'premium'}
    
    result = calculate_creator_fit(dna, brand, health, product_context=context)
    
    # Evaluation
    # Price Fit (30% weight) -> matches premium_score (10) -> component score 3.0
    # Brand Fit (30% weight) -> Mismatch (Prem vs Budget) -> 40 -> component score 12.0
    # Category (20%) -> 60 -> 12.0
    # Trust (20%) -> 80 -> 16.0
    # Total ~ 43.0
    
    assert result['score'] < 50
    assert "Price Mismatch" in result['failure_reason']

def test_brand_veto():
    """Test that Negative Brand Sentiment vetoes the score."""
    dna = {'spending_power': {'premium_score': 80}} # Rich audience
    # Audience HATES Sony
    brand = {'brand_orbit': [{'name': 'Sony', 'positive_pct': 10}], 'dominant_tier': 'premium'}
    health = {'trust': {'score_numeric': 90}} # High Trust
    
    context = {'price': 20000, 'name': 'Sony Headphones', 'category': 'Tech', 'tier': 'mid'}
    
    result = calculate_creator_fit(dna, brand, health, product_context=context)
    
    # Brand Fit -> 0 (Veto)
    # Even if Price Fit is 100, Trust is 100...
    # Score = 30(Price) + 0(Brand) + 20(Cat) + 20(Trust) = 70? 
    # Wait, my logic sets brand_fit=0. It doesn't force the *Total* to 0.
    # But 0/30 is a heavy penalty.
    
    # Actually, let's check my implementation:
    # "if positive_pct < 40: brand_fit = 0"
    # It doesn't cap the FINAL score.
    # So 70 is still a "Good Fit".
    # The user wanted a VETO.
    # I should refine the logic to cap the final score if Brand Fit is 0.
    
    # Brand Fit -> 0 (Veto)
    # The new logic caps final score at 35.
    
    assert result['score'] <= 35
    assert "hostile" in result['failure_reason']
