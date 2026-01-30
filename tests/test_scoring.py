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

def test_persona_matching():
    """Test that description matching personas boosts the score."""
    dna = {
        'spending_power': {'premium_score': 50, 'budget_score': 50},
        'tech_literacy': {'expert_score': 50, 'casual_score': 50},
        'personas': {'personas': [{'name': 'Gamer', 'percentage': 40}]}
    }
    brand = {'brand_orbit': [], 'dominant_tier': 'mid'}
    health = {'trust': {'score_numeric': 50}}
    
    # CASE 1: No Description
    context_no_desc = {'price': 25000, 'name': 'Mid Headphones', 'category': 'Tech', 'tier': 'mid'}
    res_no_desc = calculate_creator_fit(dna, brand, health, product_context=context_no_desc)
    base_category_score = res_no_desc['breakdown']['category_fit']
    
    # CASE 2: Description matches "Gamer"
    context_gamer = {'price': 25000, 'name': 'Mid Headphones', 'category': 'Tech', 'tier': 'mid', 'description': 'Perfect for any serious gamer'}
    res_gamer = calculate_creator_fit(dna, brand, health, product_context=context_gamer)
    boosted_category_score = res_gamer['breakdown']['category_fit']
    
    # Boost Logic: 40% / 2 = 20 points
    # Start (Tech) = 50 (expert_score)
    # Boosted = 50 + 20 = 70
    
    assert boosted_category_score > base_category_score
    assert boosted_category_score == base_category_score + 20
    assert 'persona_boost' in res_gamer['breakdown']
