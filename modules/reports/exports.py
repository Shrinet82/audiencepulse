from fpdf import FPDF
import tempfile
import json

class AgencyBrief(FPDF):
    def header(self):
        # Agency Logo / Brand
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'AudiencePulse | Agency Brief', 0, 0, 'C')
        self.ln(20)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no()) + ' | Confidential Audit', 0, 0, 'C')

def generate_agency_brief(creator_name: str, product_name: str, score: int, analysis: dict) -> bytes:
    """
    Generates a professional PDF Brief for the audit.
    """
    pdf = AgencyBrief()
    pdf.add_page()
    
    # 1. Title Section
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 10, f"Creator Audit: {creator_name}", 0, 1)
    
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Campaign Target: {product_name}", 0, 1)
    pdf.ln(10)
    
    # 2. Executive Scorecard
    pdf.set_draw_color(200, 200, 200)
    pdf.set_fill_color(250, 250, 250)
    pdf.rect(10, 50, 190, 40, 'DF')
    
    pdf.set_y(55)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 10, "FIT SCORE", 0, 0, 'C')
    pdf.cell(60, 10, "RISK LEVEL", 0, 0, 'C')
    pdf.cell(60, 10, "BUYING POWER", 0, 1, 'C')
    
    # Values
    pdf.set_font('Arial', 'B', 20)
    
    # Color logic isn't easily possible with simple cell, so text only
    pdf.cell(60, 15, str(score) + "/100", 0, 0, 'C')
    
    # Extract Risk
    health = analysis.get('community_health', {})
    safe = health.get('toxicity', {}).get('is_safe', True)
    risk_label = "SAFE" if safe else "HIGH RISK"
    pdf.cell(60, 15, risk_label, 0, 0, 'C')
    
    # Extract Wallet
    dna = analysis.get('audience_dna', {})
    wallet = dna.get('spending_power', {}).get('verdict', 'Unknown')
    pdf.cell(60, 15, wallet, 0, 1, 'C')
    
    pdf.ln(20)
    
    # 3. Audience DNA
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, "🧬 Audience DNA Analysis", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    summary = dna.get('summary', 'No summary available.')
    pdf.multi_cell(0, 7, summary)
    pdf.ln(5)
    
    # Personas
    personas = dna.get('personas', {}).get('personas', [])
    if personas:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Key Personas:", 0, 1)
        pdf.set_font('Arial', '', 11)
        for p in personas[:3]:
            pdf.cell(5)
            pdf.cell(0, 7, f"- {p.get('name')}: {p.get('description', '')[:80]}...", 0, 1)
            
    pdf.ln(10)
    
    # 4. Brand Safety
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, "🛡️ Brand Safety Check", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    tox = health.get('toxicity', {})
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f"Toxicity Score: {tox.get('toxic_pct', 0)}%", 0, 1)
    pdf.multi_cell(0, 7, f"Summary: {health.get('trust', {}).get('verdict', 'N/A')}")
    
    # 5. Output
    # Return as bytes string
    return pdf.output(dest='S').encode('latin1')
