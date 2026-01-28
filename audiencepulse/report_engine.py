"""
Strategy Deck Generator - PDF Report Engine

Generates agency-ready PDF reports from Creator Audit data.
Uses reportlab for pixel-perfect positioning.

Pages:
1. Executive Summary (Grade, Fit Score, Recommendation)
2. Audience DNA (Wallet Depth, Tech Level, Brand Orbit)
3. Trust & Risk (Trust Score, Safety, Strategist Notes)
"""

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
import datetime


# ============================================
# CONSTANTS
# ============================================

DARK_BG = colors.HexColor("#1E1E2E")
ACCENT_GREEN = colors.HexColor("#10B981")
ACCENT_BLUE = colors.HexColor("#3B82F6")
ACCENT_RED = colors.HexColor("#EF4444")
ACCENT_YELLOW = colors.HexColor("#F59E0B")
LIGHT_BG = colors.HexColor("#F8FAFC")


# ============================================
# HELPER FUNCTIONS
# ============================================

def draw_header(c, client_name, page_num):
    """Draw consistent header on each page."""
    width, height = LETTER
    
    # Dark header bar
    c.setFillColor(DARK_BG)
    c.rect(0, height - 1*inch, width, 1*inch, fill=1, stroke=0)
    
    # Title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(0.5*inch, height - 0.55*inch, "AUDIENCEPULSE | STRATEGY DECK")
    
    # Subtitle
    c.setFont("Helvetica", 10)
    c.drawString(0.5*inch, height - 0.8*inch, f"Prepared for: {client_name} | {datetime.date.today().strftime('%B %d, %Y')}")
    
    # Page number
    c.drawRightString(width - 0.5*inch, height - 0.8*inch, f"Page {page_num}")


def draw_progress_bar(c, x, y, width, height, percentage, fill_color):
    """Draw a progress bar with percentage fill."""
    # Background
    c.setFillColor(colors.HexColor("#E5E7EB"))
    c.roundRect(x, y, width, height, 5, fill=1, stroke=0)
    
    # Fill
    fill_width = width * (percentage / 100)
    if fill_width > 5:
        c.setFillColor(fill_color)
        c.roundRect(x, y, fill_width, height, 5, fill=1, stroke=0)


def get_grade_color(grade: str):
    """Get color based on grade."""
    if grade in ['A+', 'A']:
        return ACCENT_GREEN
    elif grade in ['B+', 'B']:
        return ACCENT_BLUE
    elif grade == 'C':
        return ACCENT_YELLOW
    else:
        return ACCENT_RED


# ============================================
# PAGE 1: EXECUTIVE SUMMARY
# ============================================

def draw_page_1(c, data, client_name):
    """Draw Executive Summary page."""
    width, height = LETTER
    draw_header(c, client_name, 1)
    
    grade = data.get('grade', 'N/A')
    fit_score = data.get('fit_score', 0)
    grade_color = get_grade_color(grade)
    
    # Grade Badge - Large centered box
    badge_y = height - 3.5*inch
    c.setFillColor(grade_color)
    c.roundRect(0.5*inch, badge_y, width - 1*inch, 1.8*inch, 15, fill=1, stroke=0)
    
    # Grade text
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 60)
    c.drawCentredString(width/2, badge_y + 1.1*inch, f"GRADE: {grade}")
    
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, badge_y + 0.5*inch, f"FIT SCORE: {fit_score}%")
    
    # Verdict
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(0.5*inch, badge_y - 0.5*inch, "RECOMMENDATION")
    
    c.setFont("Helvetica", 12)
    verdict = data.get('verdict', 'Analysis complete')
    c.drawString(0.5*inch, badge_y - 0.8*inch, verdict[:80])
    
    # Failure Reason (if any)
    failure_reason = data.get('failure_reason', '')
    if failure_reason:
        c.setFillColor(ACCENT_RED)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.5*inch, badge_y - 1.2*inch, "KEY ISSUE:")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 11)
        c.drawString(0.5*inch, badge_y - 1.5*inch, failure_reason[:80])
    
    # Key Metrics Summary
    y_pos = height - 6*inch
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(0.5*inch, y_pos, "KEY METRICS SUMMARY")
    
    metrics = [
        ("Wallet Depth", data.get('wallet_depth', {}).get('verdict', 'N/A')),
        ("Tech Savviness", data.get('tech_level', {}).get('verdict', 'N/A')),
        ("Trust Score", data.get('trust', {}).get('score', 'N/A')),
        ("Dominant Brand Tier", data.get('brand_tier', 'N/A').title()),
    ]
    
    y_pos -= 0.4*inch
    c.setFont("Helvetica", 11)
    for label, value in metrics:
        c.drawString(0.7*inch, y_pos, f"• {label}: {value}")
        y_pos -= 0.3*inch
    
    # Strategist Notes Box
    notes = data.get('strategist_notes', '')
    if notes:
        c.setFillColor(LIGHT_BG)
        c.roundRect(0.5*inch, 1.5*inch, width - 1*inch, 1.8*inch, 10, fill=1, stroke=0)
        
        c.setFillColor(DARK_BG)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.7*inch, 3*inch, "STRATEGIST NOTES")
        
        c.setFont("Helvetica", 10)
        # Simple text wrapping
        lines = [notes[i:i+80] for i in range(0, len(notes), 80)]
        y = 2.7*inch
        for line in lines[:4]:
            c.drawString(0.7*inch, y, line)
            y -= 0.25*inch


# ============================================
# PAGE 2: AUDIENCE DNA
# ============================================

def draw_page_2(c, data, client_name):
    """Draw Audience DNA page."""
    width, height = LETTER
    draw_header(c, client_name, 2)
    
    # Title
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(0.5*inch, height - 1.5*inch, "AUDIENCE PSYCHOGRAPHICS")
    
    # Wallet Depth Section
    y_pos = height - 2.2*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(0.5*inch, y_pos, "WALLET DEPTH")
    c.setFont("Helvetica", 10)
    c.drawString(0.5*inch, y_pos - 0.25*inch, "Budget-Conscious ←→ Premium Buyers")
    
    premium_pct = data.get('wallet_depth', {}).get('premium', 50)
    draw_progress_bar(c, 0.5*inch, y_pos - 0.7*inch, 5*inch, 0.35*inch, premium_pct, ACCENT_GREEN)
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(6*inch, y_pos - 0.55*inch, f"{premium_pct}% Premium")
    c.setFont("Helvetica", 10)
    c.drawString(6*inch, y_pos - 0.8*inch, data.get('wallet_depth', {}).get('verdict', 'N/A'))
    
    # Tech Level Section
    y_pos = height - 4*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(0.5*inch, y_pos, "TECHNICAL LITERACY")
    c.setFont("Helvetica", 10)
    c.drawString(0.5*inch, y_pos - 0.25*inch, "Casual Users ←→ Pro/Expert")
    
    expert_pct = data.get('tech_level', {}).get('expert', 50)
    draw_progress_bar(c, 0.5*inch, y_pos - 0.7*inch, 5*inch, 0.35*inch, expert_pct, ACCENT_BLUE)
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(6*inch, y_pos - 0.55*inch, f"{expert_pct}% Expert")
    c.setFont("Helvetica", 10)
    c.drawString(6*inch, y_pos - 0.8*inch, data.get('tech_level', {}).get('verdict', 'N/A'))
    
    # Brand Orbit Section
    y_pos = height - 5.8*inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(0.5*inch, y_pos, "BRAND AFFINITY ORBIT")
    
    c.setFont("Helvetica", 10)
    c.drawString(0.5*inch, y_pos - 0.3*inch, f"Dominant Tier: {data.get('brand_tier', 'Unknown').title()}")
    
    # Brand list
    brands = data.get('brand_orbit', [])
    y = y_pos - 0.7*inch
    c.setFont("Helvetica", 11)
    for brand in brands[:8]:
        if isinstance(brand, dict):
            name = brand.get('brand', 'Unknown')
            pct = brand.get('positive_pct', 50)
            sentiment_color = ACCENT_GREEN if pct >= 50 else ACCENT_YELLOW if pct >= 30 else ACCENT_RED
            c.setFillColor(colors.black)
            c.drawString(0.7*inch, y, f"• {name}")
            c.setFillColor(sentiment_color)
            c.drawString(3*inch, y, f"{pct}% positive")
        else:
            c.setFillColor(colors.black)
            c.drawString(0.7*inch, y, f"• {brand}")
        y -= 0.3*inch
    
    # Buyer Personas
    y_pos = height - 9*inch
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(0.5*inch, y_pos, "TOP BUYER PERSONAS")
    
    personas = data.get('personas', [])
    y = y_pos - 0.5*inch
    for persona in personas[:3]:
        if isinstance(persona, dict):
            name = persona.get('name', 'Unknown')
            pct = persona.get('percentage', 0)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(0.7*inch, y, f"{name}")
            c.setFont("Helvetica", 10)
            c.drawString(3*inch, y, f"{pct}%")
        y -= 0.3*inch


# ============================================
# PAGE 3: TRUST & RISK
# ============================================

def draw_page_3(c, data, client_name):
    """Draw Trust & Risk page."""
    width, height = LETTER
    draw_header(c, client_name, 3)
    
    # Title
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(0.5*inch, height - 1.5*inch, "COMMUNITY HEALTH & RISK ASSESSMENT")
    
    # Trust Score Box
    trust = data.get('trust', {})
    trust_score = trust.get('score', 'N/A')
    trust_color = ACCENT_GREEN if trust_score in ['A+', 'A'] else ACCENT_YELLOW if trust_score in ['B', 'C'] else ACCENT_RED
    
    y_pos = height - 2.5*inch
    c.setFillColor(trust_color)
    c.roundRect(0.5*inch, y_pos - 0.5*inch, 2*inch, 1.2*inch, 10, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(1.5*inch, y_pos + 0.3*inch, trust_score)
    c.setFont("Helvetica", 10)
    c.drawCentredString(1.5*inch, y_pos - 0.1*inch, "TRUST SCORE")
    
    # Trust verdict
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 11)
    c.drawString(3*inch, y_pos + 0.3*inch, trust.get('verdict', 'N/A')[:50])
    
    # Toxicity Level
    toxicity = data.get('toxicity', {})
    tox_level = toxicity.get('level', 'LOW')
    tox_color = ACCENT_GREEN if tox_level == 'LOW' else ACCENT_YELLOW if tox_level == 'MEDIUM' else ACCENT_RED
    
    y_pos = height - 4.5*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(0.5*inch, y_pos, "TOXICITY LEVEL")
    
    c.setFillColor(tox_color)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2.5*inch, y_pos, tox_level)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    is_safe = toxicity.get('is_safe', True)
    c.drawString(0.5*inch, y_pos - 0.3*inch, f"Brand Safe: {'✔ Yes' if is_safe else '✖ No'}")
    
    # Sponsorship Recommendation
    y_pos = height - 5.5*inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(0.5*inch, y_pos, "SPONSORSHIP RECOMMENDATION")
    
    recommendation = data.get('sponsor_recommendation', '')
    c.setFont("Helvetica", 11)
    c.drawString(0.5*inch, y_pos - 0.4*inch, recommendation[:80])
    
    # Footer disclaimer
    c.setFillColor(colors.gray)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 0.5*inch, "Generated by AudiencePulse • Creator Vetting Platform • Confidential")


# ============================================
# MAIN GENERATOR
# ============================================

def generate_pdf_report(data: dict, client_name: str, strategist_notes: str = "") -> BytesIO:
    """
    Generate complete Strategy Deck PDF.
    
    Args:
        data: Audit results containing grade, fit_score, etc.
        client_name: Name for white-labeling
        strategist_notes: Custom notes from strategist
    
    Returns:
        BytesIO buffer containing PDF
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    
    # Add strategist notes to data
    data['strategist_notes'] = strategist_notes
    
    # Page 1: Executive Summary
    draw_page_1(c, data, client_name)
    c.showPage()
    
    # Page 2: Audience DNA
    draw_page_2(c, data, client_name)
    c.showPage()
    
    # Page 3: Trust & Risk
    draw_page_3(c, data, client_name)
    c.showPage()
    
    c.save()
    buffer.seek(0)
    return buffer


def package_audit_for_pdf(audit_results: dict) -> dict:
    """
    Transform audit results into PDF-friendly format.
    """
    fit = audit_results.get('creator_fit', {})
    dna = audit_results.get('audience_dna', {})
    brand = audit_results.get('brand_affinity', {})
    health = audit_results.get('community_health', {})
    
    return {
        'grade': fit.get('grade', 'N/A'),
        'fit_score': fit.get('score', 0),
        'verdict': fit.get('verdict', ''),
        'failure_reason': fit.get('failure_reason', ''),
        'wallet_depth': {
            'premium': dna.get('spending_power', {}).get('premium_score', 50),
            'verdict': dna.get('spending_power', {}).get('verdict', 'N/A')
        },
        'tech_level': {
            'expert': dna.get('tech_literacy', {}).get('expert_score', 50),
            'verdict': dna.get('tech_literacy', {}).get('verdict', 'N/A')
        },
        'brand_tier': brand.get('dominant_tier', 'unknown'),
        'brand_orbit': brand.get('brand_orbit', []),
        'personas': dna.get('personas', {}).get('personas', []),
        'trust': {
            'score': health.get('trust', {}).get('score', 'N/A'),
            'verdict': health.get('trust', {}).get('verdict', '')
        },
        'toxicity': {
            'level': health.get('toxicity', {}).get('toxicity_level', 'LOW'),
            'is_safe': health.get('toxicity', {}).get('is_safe', True)
        },
        'sponsor_recommendation': health.get('sponsor_recommendation', '')
    }


if __name__ == "__main__":
    # Test
    test_data = {
        'grade': 'D',
        'fit_score': 35,
        'verdict': 'Poor Fit - Not recommended for this product',
        'failure_reason': 'Low Spending Power (18% premium buyers)',
        'wallet_depth': {'premium': 18, 'verdict': 'LOW'},
        'tech_level': {'expert': 25, 'verdict': 'CASUAL'},
        'brand_tier': 'budget',
        'brand_orbit': [
            {'brand': 'Pixel', 'positive_pct': 17},
            {'brand': 'OnePlus', 'positive_pct': 24},
        ],
        'personas': [
            {'name': 'Budget Hunter', 'percentage': 45},
            {'name': 'Skeptic', 'percentage': 30},
        ],
        'trust': {'score': 'C', 'verdict': 'Skeptical audience'},
        'toxicity': {'level': 'LOW', 'is_safe': True},
        'sponsor_recommendation': 'Proceed with caution'
    }
    
    pdf = generate_pdf_report(test_data, "Samsung", "Test notes here")
    with open("test_deck.pdf", "wb") as f:
        f.write(pdf.read())
    print("Test PDF generated: test_deck.pdf")
