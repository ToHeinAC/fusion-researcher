"""Research query interface and report generation page."""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Research - Fusion Research", page_icon="📝", layout="wide")

st.title("📝 Research")
st.markdown("Natural language queries and report generation.")

# Check if database exists
db_path = Path("research/fusion_research.db")
if not db_path.exists():
    st.warning("⚠️ Database not initialized.")
    st.stop()

try:
    from src.data.database import get_database
    from src.services.company_service import CompanyService
    from src.services.report_service import ReportService
    
    db = get_database()
    company_service = CompanyService(db)
    report_service = ReportService(db)
    
    # Tabs for different research functions
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Natural Language Query",
        "📊 SWOT Analysis",
        "⚖️ Company Comparison",
        "📄 Report Generation",
    ])
    
    with tab1:
        st.markdown("### 🔍 Ask Questions About Fusion Industry")
        st.markdown("Query the database using natural language with your local Ollama LLM.")
        
        # Get Ollama settings from session state
        ollama_model = st.session_state.get("llm_model", "qwen3:8b")
        ollama_url = st.session_state.get("ollama_base_url", "http://localhost:11434")
        
        st.info(f"🤖 Using model: **{ollama_model}** at {ollama_url}")
        
        # Sample queries
        st.markdown("**Sample Queries:**")
        sample_queries = [
            "Show me all German fusion startups with funding over EUR 100M",
            "What are the top 5 fusion companies by total funding?",
            "List companies using Stellarator technology",
            "Which companies have TRL 6 or higher?",
        ]
        
        selected_sample = st.selectbox("Select a sample query or type your own:", [""] + sample_queries)
        
        query = st.text_area(
            "Enter your question:",
            value=selected_sample,
            height=100,
            placeholder="e.g., What are the top risks for German fusion startups?"
        )
        
        if st.button("🔍 Search", type="primary"):
            if query:
                with st.spinner(f"Processing query with {ollama_model}..."):
                    try:
                        from src.llm.chain_factory import ChainFactory
                        from src.llm.query_processor import NLQueryProcessor
                        
                        factory = ChainFactory(
                            model=ollama_model,
                            db_path=str(db_path),
                            base_url=ollama_url,
                        )
                        processor = NLQueryProcessor(factory.llm, factory.db)
                        
                        result = processor.process_query(query)
                        
                        if result.error:
                            st.error(f"Error: {result.error}")
                        else:
                            st.markdown("### Answer")
                            st.markdown(result.answer)
                            
                            if result.sql:
                                with st.expander("View SQL Query"):
                                    st.code(result.sql, language="sql")
                            
                            if result.results:
                                with st.expander("View Raw Results"):
                                    st.json(result.results[:20])
                    except Exception as e:
                        st.error(f"Query failed: {e}")
            else:
                st.warning("Please enter a query.")
    
    with tab2:
        st.markdown("### 📊 SWOT Analysis Generator")
        st.markdown("Generate AI-powered SWOT analysis for any company.")
        
        ollama_model = st.session_state.get("llm_model", "qwen3:8b")
        ollama_url = st.session_state.get("ollama_base_url", "http://localhost:11434")
        
        companies = company_service.get_all_companies(limit=100)
        company_names = [c.name for c in companies]
        
        if company_names:
            selected_company = st.selectbox("Select a company:", company_names)
            
            market_context = st.text_area(
                "Additional market context (optional):",
                placeholder="e.g., Focus on European market positioning...",
                height=100,
            )
            
            if st.button("📊 Generate SWOT", type="primary"):
                company = next((c for c in companies if c.name == selected_company), None)
                if company:
                    with st.spinner(f"Generating SWOT analysis with {ollama_model}..."):
                        try:
                            from src.llm.chain_factory import get_llm
                            from src.llm.analyzer import FusionAnalyzer
                            
                            llm = get_llm(model=ollama_model, base_url=ollama_url)
                            analyzer = FusionAnalyzer(llm)
                            
                            swot = analyzer.generate_swot(company, market_context)
                            
                            st.markdown(f"## SWOT Analysis: {swot.company_name}")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("### ✅ Strengths")
                                for s in swot.strengths:
                                    st.markdown(f"- {s}")
                                
                                st.markdown("### 🎯 Opportunities")
                                for o in swot.opportunities:
                                    st.markdown(f"- {o}")
                            
                            with col2:
                                st.markdown("### ⚠️ Weaknesses")
                                for w in swot.weaknesses:
                                    st.markdown(f"- {w}")
                                
                                st.markdown("### 🚨 Threats")
                                for t in swot.threats:
                                    st.markdown(f"- {t}")
                            
                            with st.expander("View Raw Markdown"):
                                st.markdown(swot.raw_markdown)
                                st.download_button(
                                    "📥 Download SWOT",
                                    swot.raw_markdown,
                                    file_name=f"swot_{selected_company.replace(' ', '_')}.md",
                                    mime="text/markdown",
                                )
                        except Exception as e:
                            st.error(f"SWOT generation failed: {e}")
            else:
                st.info("No companies in database.")
    
    with tab3:
        st.markdown("### ⚖️ Company Comparison")
        st.markdown("Compare two companies head-to-head.")
        
        ollama_model = st.session_state.get("llm_model", "qwen3:8b")
        ollama_url = st.session_state.get("ollama_base_url", "http://localhost:11434")
        
        companies = company_service.get_all_companies(limit=100)
        company_names = [c.name for c in companies]
        
        if len(company_names) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                company_a = st.selectbox("Company A:", company_names, key="comp_a")
            
            with col2:
                remaining = [n for n in company_names if n != company_a]
                company_b = st.selectbox("Company B:", remaining, key="comp_b")
            
            # Show static comparison first
            st.markdown("#### Quick Comparison")
            
            comp_a = next((c for c in companies if c.name == company_a), None)
            comp_b = next((c for c in companies if c.name == company_b), None)
            
            if comp_a and comp_b:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**{comp_a.name}**")
                    st.markdown(f"- Country: {comp_a.country}")
                    st.markdown(f"- Technology: {comp_a.technology_approach or 'N/A'}")
                    st.markdown(f"- TRL: {comp_a.trl or 'N/A'}")
                    st.markdown(f"- Funding: {comp_a.funding_display}")
                    st.markdown(f"- Team: {comp_a.team_size or 'N/A'}")
                
                with col2:
                    st.markdown(f"**{comp_b.name}**")
                    st.markdown(f"- Country: {comp_b.country}")
                    st.markdown(f"- Technology: {comp_b.technology_approach or 'N/A'}")
                    st.markdown(f"- TRL: {comp_b.trl or 'N/A'}")
                    st.markdown(f"- Funding: {comp_b.funding_display}")
                    st.markdown(f"- Team: {comp_b.team_size or 'N/A'}")
            
            st.markdown("---")
            
            if st.button("⚖️ Generate AI Comparison", type="primary"):
                with st.spinner(f"Generating comparison with {ollama_model}..."):
                    try:
                        from src.llm.chain_factory import get_llm
                        from src.llm.analyzer import FusionAnalyzer
                        
                        llm = get_llm(model=ollama_model, base_url=ollama_url)
                        analyzer = FusionAnalyzer(llm)
                        
                        if comp_a and comp_b:
                            comparison = analyzer.compare_companies(comp_a, comp_b)
                            
                            st.markdown(f"## AI Analysis: {comparison.company_a} vs {comparison.company_b}")
                            st.markdown(comparison.raw_markdown)
                    except Exception as e:
                        st.error(f"Comparison failed: {e}")
        else:
            st.info("Need at least 2 companies for comparison.")
    
    with tab4:
        st.markdown("### 📄 Report Generation")
        st.markdown("Generate comprehensive market reports.")
        
        report_type = st.selectbox(
            "Report Type:",
            ["Market Overview", "Company Profile", "Investment Thesis"],
        )
        
        if report_type == "Market Overview":
            if st.button("📄 Generate Market Overview", type="primary"):
                with st.spinner("Generating report..."):
                    report = report_service.generate_market_overview()
                    st.markdown(report)
                    
                    st.download_button(
                        "📥 Download Report",
                        report,
                        file_name="market_overview.md",
                        mime="text/markdown",
                    )
        
        elif report_type == "Company Profile":
            companies = company_service.get_all_companies(limit=100)
            company_names = [c.name for c in companies]
            
            if company_names:
                selected = st.selectbox("Select Company:", company_names)
                
                if st.button("📄 Generate Company Profile", type="primary"):
                    company = next((c for c in companies if c.name == selected), None)
                    if company:
                        with st.spinner("Generating report..."):
                            report = report_service.generate_company_profile(company.id)
                            if report:
                                st.markdown(report)
                                
                                st.download_button(
                                    "📥 Download Report",
                                    report,
                                    file_name=f"profile_{selected.replace(' ', '_')}.md",
                                    mime="text/markdown",
                                )
                            else:
                                st.error("Failed to generate report.")
            else:
                st.info("No companies in database.")
        
        elif report_type == "Investment Thesis":
            focus = st.text_input("Focus Area:", value="German startups")
            
            if st.button("📄 Generate Investment Thesis", type="primary"):
                with st.spinner("Generating report..."):
                    report = report_service.generate_investment_thesis(focus)
                    st.markdown(report)
                    
                    st.download_button(
                        "📥 Download Report",
                        report,
                        file_name="investment_thesis.md",
                        mime="text/markdown",
                    )

except Exception as e:
    st.error(f"Error loading research page: {e}")
    st.exception(e)
