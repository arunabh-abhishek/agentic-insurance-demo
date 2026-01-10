import streamlit as st
import time
import pandas as pd
import requests  # Added for the API call
from fpdf import FPDF

st.set_page_config(page_title="Agentic Policy Advisor", layout="wide")

# --- DATA: Driver Personas ---
PERSONAS = {
    "Safe Driver (Alice)": {
        "score": 98, "history": "Clean", "id": "DRV-001",
        "reasoning": "Elite safety score due to 0 reported incidents and smooth braking patterns."
    },
    "High Risk Driver (Bob)": {
        "score": 42, "history": "2 Accidents", "id": "DRV-002",
        "reasoning": "High-risk designation driven by recent at-fault collisions and frequent speeding."
    },
    "New Driver (Charlie)": {
        "score": 75, "history": "No Record", "id": "DRV-003",
        "reasoning": "Moderate risk due to lack of historical data; score based on peer-group averages."
    }
}

# --- PDF TOOL ---
def create_detailed_pdf(tier_name, quote_data, vin, driver, score, df_comp, car_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Insurance Quote: {tier_name} Plan", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, f"Vehicle: {car_name} (VIN: {vin})", ln=True, align='C')
    pdf.cell(0, 10, f"Driver: {driver} (Score: {score})", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Monthly Premium Estimate: ${quote_data['price']:.2f}", ln=True)
    pdf.cell(0, 10, f"Liability Limit: {quote_data['limit']}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(80, 10, "Feature", 1)
    pdf.cell(40, 10, "Included", 1, ln=True)
    
    pdf.set_font("Arial", '', 10)
    for index, row in df_comp.iterrows():
        status = "Yes" if row[tier_name] == "✅" else "No"
        pdf.cell(80, 10, row['Feature'], 1)
        pdf.cell(40, 10, status, 1, ln=True)
    
    return bytes(pdf.output())

# --- UI APP ---
st.title("🛡️ Agentic Insurance Underwriter")

col_in1, col_in2 = st.columns(2)
with col_in1:
    vin_val = st.text_input("Vehicle VIN", value="1G1YY2E")
with col_in2:
    selected_name = st.selectbox("Driver Profile", list(PERSONAS.keys()))

driver_info = PERSONAS[selected_name]

if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False

if st.button("🚀 Run Agentic Analysis"):
    st.session_state.analyzed = True
    
    with st.status("Agent Reasoning Process...", expanded=True) as status:
        st.write("🔍 Initializing Underwriting Agent...")
        
        # --- NEW API LOGIC ---
        st.write(f"📡 Connecting to NHTSA API to decode VIN: {vin_val}")
        try:
            api_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin_val}?format=json"
            response = requests.get(api_url).json()
            
            # Extract Make, Model, and Year from the API results
            results = {item['Variable']: item['Value'] for item in response['Results']}
            st.session_state.car_make = results.get("Make", "Unknown")
            st.session_state.car_model = results.get("Model", "Unknown")
            st.session_state.car_year = results.get("Model Year", "Unknown")
            st.session_state.car_full_name = f"{st.session_state.car_year} {st.session_state.car_make} {st.session_state.car_model}"
            
            st.write(f"✅ Vehicle identified: {st.session_state.car_full_name}")
        except Exception as e:
            st.error("API Error. Falling back to default vehicle.")
            st.session_state.car_full_name = "2024 Toyota Camry"

        st.write(f"📊 Fetching telematics for {selected_name}...")
        time.sleep(0.5)
        st.write(f"📈 Analyzing score: {driver_info['score']}/100")
        st.write("✨ Generating optimized coverage tiers...")
        time.sleep(0.5)
        status.update(label="Analysis Complete!", state="complete")
        st.balloons()

# Display results
if st.session_state.analyzed:
    car_name = st.session_state.car_full_name
    base_rate = 100 + (100 - driver_info['score']) * 2
    
    tiers = {
        "Optimized": {"price": base_rate * 0.85, "limit": "$100,000", "details": ["Bodily Injury Liability", "Property Damage"], "summary": "Minimum legal protection."},
        "Basic": {"price": base_rate, "limit": "$500,000", "details": ["All Optimized features", "Fire & Theft", "Roadside Assist"], "summary": "Standard protection."},
        "Premium": {"price": base_rate * 1.5, "limit": "$1,500,000", "details": ["All Basic features", "Collision Damage", "Rental Reimbursement"], "summary": "Maximum protection."}
    }
    
    comparison_data = {
        "Feature": ["Legal Liability", "Fire & Theft", "Accidental Damage", "Roadside Assist", "Rental Car"],
        "Optimized": ["✅", "❌", "❌", "❌", "❌"],
        "Basic": ["✅", "✅", "❌", "✅", "❌"],
        "Premium": ["✅", "✅", "✅", "✅", "✅"]
    }
    df_comp = pd.DataFrame(comparison_data)

    st.info(f"**Vehicle Identified:** {car_name} | **Driver Score:** {driver_info['score']}/100")

    cols = st.columns(3)
    for i, (name, data) in enumerate(tiers.items()):
        with cols[i]:
            container = st.container(border=True)
            container.markdown(f"### {name}")
            container.markdown(f"## ${data['price']:.2f} <small>/mo</small>", unsafe_allow_html=True)
            container.markdown(f"**Limit: {data['limit']}**")
            container.write("---")
            for detail in data['details']:
                container.markdown(f"🔹 {detail}")
            
            # Generate PDF using the live car name
            pdf_bytes = create_detailed_pdf(name, data, vin_val, selected_name, driver_info['score'], df_comp, car_name)
            container.download_button(label=f"Get {name} PDF", data=pdf_bytes, file_name=f"{name}.pdf", mime="application/pdf", key=f"btn_{name}")

    st.write("### Quick Feature Match")
    st.table(df_comp)

    # --- CHAT SECTION ---
    st.divider()
    st.subheader("💬 Ask the Underwriting Agent")
    if "messages" not in st.session_state: st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Why is the premium high?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            if "high" in prompt.lower() or "price" in prompt.lower():
                response = f"My risk analysis shows: {driver_info['reasoning']}"
            elif "car" in prompt.lower() or "vin" in prompt.lower():
                response = f"The {car_name} (VIN: {vin_val}) was analyzed for safety ratings and parts cost to influence this quote."
            else:
                response = "I can explain the risk factors for this driver or vehicle profile."
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})