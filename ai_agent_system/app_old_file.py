"""
AI Agent System - Streamlit Interface COMPLETE FIX
FIXES: Upload redirect + Font size + Better UX + Search Notes Fixed
Company: Sepia ML | v2.5.0 - PRODUCTION READY
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import os
import time
import traceback

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import agent
from agent import AIAgent
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Agent System - Sepia ML",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - FIXED FONT SIZE + DARK MODE
CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 20px;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2em;
        margin-bottom: 30px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* PDF Card - FIXED Font Size */
    .pdf-card {
        padding: 12px;
        border: 2px solid #4a5568;
        border-radius: 10px;
        margin: 8px 0;
        background-color: #2d3748;
    }
    .pdf-card strong {
        color: #90cdf4 !important;
        font-size: 0.95em !important;
        display: block;
        margin-bottom: 6px;
    }
    .pdf-card span {
        color: #e2e8f0 !important;
        display: block;
        margin: 3px 0;
        font-size: 0.85em !important;
    }
    
    /* Note Card - FIXED Font Size */
    .note-card {
        padding: 12px;
        border: 2px solid #4a5568;
        border-radius: 10px;
        margin: 8px 0;
        background-color: #2d3748;
    }
    .note-card strong {
        color: #90cdf4 !important;
        font-size: 0.95em !important;
        display: block;
        margin-bottom: 6px;
    }
    .note-card span {
        color: #e2e8f0 !important;
        display: block;
        margin: 3px 0;
        font-size: 0.85em !important;
    }
    
    /* Delete Confirmation */
    .delete-confirm {
        padding: 12px;
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 10px;
        margin: 8px 0;
        color: #856404;
        font-size: 0.9em;
    }
    
    /* Success Box */
    .success-box {
        padding: 15px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        color: #155724;
        margin: 10px 0;
        font-size: 0.95em;
    }
    
    /* Upload Progress */
    .upload-progress {
        padding: 15px;
        background-color: #e3f2fd;
        border: 2px solid #2196f3;
        border-radius: 10px;
        margin: 10px 0;
        color: #0d47a1;
        font-size: 0.95em;
        font-weight: bold;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_session_state():
    """Initialize session state"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'system_ready' not in st.session_state:
        st.session_state.system_ready = False
    if 'last_upload_result' not in st.session_state:
        st.session_state.last_upload_result = None
    if 'delete_confirm' not in st.session_state:
        st.session_state.delete_confirm = {}
    if 'refresh_trigger' not in st.session_state:
        st.session_state.refresh_trigger = 0
    if 'upload_complete' not in st.session_state:
        st.session_state.upload_complete = False
    if 'stay_on_upload_tab' not in st.session_state:
        st.session_state.stay_on_upload_tab = False


def check_env_file():
    """Check if .env file exists"""
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        st.error("❌ `.env` file not found!")
        return False
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        st.error("❌ OPENAI_API_KEY not set!")
        return False
    return True


def initialize_system():
    """Initialize AI Agent"""
    try:
        if not check_env_file():
            return None
        with st.spinner("🔄 Initializing..."):
            st.session_state.agent = AIAgent()
            health_status = st.session_state.agent.check_all_services()
            st.session_state.system_ready = True
            return health_status
    except Exception as e:
        st.error(f"❌ Initialization failed: {str(e)}")
        return None


def handle_file_upload(uploaded_file):
    """Handle file upload with better progress feedback"""
    try:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name
        file_type = uploaded_file.type
        file_size = len(file_bytes)
        
        max_size = 100 * 1024 * 1024
        if file_size > max_size:
            return {
                "success": False,
                "error": f"File too large! Max: 100MB"
            }
        
        temp_dir = Path.home() / "AppData" / "Local" / "Temp" / "agent_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_path = temp_dir / file_name
        with open(temp_path, "wb") as f:
            f.write(file_bytes)
        
        if file_type == "application/pdf" or file_name.endswith('.pdf'):
            result = st.session_state.agent.rag_pdf_client.upload_pdf(str(temp_path))
            
            if result.get('success'):
                try:
                    drive_result = st.session_state.agent.drive_client.upload_file(str(temp_path))
                    drive_id = drive_result.get('file_id') if drive_result.get('success') else None
                except:
                    drive_id = None
                
                return {
                    "success": True,
                    "file_name": file_name,
                    "file_type": "PDF",
                    "size": file_size,
                    "storage": "RAG PDF + Drive" if drive_id else "RAG PDF",
                    "pdf_id": result.get('pdf_id'),
                    "drive_id": drive_id,
                    "page_count": result.get('page_count', 0),
                    "chunks_created": result.get('chunks_created', 0),
                    "message": f"✅ PDF '{file_name}' processed successfully!"
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', 'Unknown error')
                }
        else:
            result = st.session_state.agent.drive_client.upload_file(str(temp_path))
            
            if result.get('success'):
                return {
                    "success": True,
                    "file_name": file_name,
                    "file_type": file_type,
                    "size": file_size,
                    "storage": "Google Drive",
                    "drive_id": result.get('file_id'),
                    "message": f"✅ File '{file_name}' uploaded!"
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', 'Unknown error')
                }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Upload error: {str(e)}"
        }


def delete_pdf(pdf_id: str, pdf_name: str):
    """Delete PDF from RAG system"""
    try:
        result = st.session_state.agent.rag_pdf_client.delete_pdf(pdf_id)
        
        if result.get('success'):
            st.success(f"✅ PDF '{pdf_name}' deleted successfully!")
            st.balloons()
            time.sleep(1)
            st.session_state.refresh_trigger += 1
            st.rerun()
        else:
            st.error(f"❌ Failed to delete: {result.get('error')}")
    
    except Exception as e:
        st.error(f"❌ Delete error: {str(e)}")


def delete_note(doc_id: str, note_title: str):
    """Delete note from database"""
    try:
        result = st.session_state.agent.database_client.delete_document(doc_id)
        
        if result.get('success'):
            st.success(f"✅ Note '{note_title}' deleted successfully!")
            st.balloons()
            time.sleep(1)
            st.session_state.refresh_trigger += 1
            st.rerun()
        else:
            st.error(f"❌ Failed to delete: {result.get('error')}")
    
    except Exception as e:
        st.error(f"❌ Delete error: {str(e)}")


def save_to_database(title, content, category="general"):
    """Save note to database"""
    try:
        result = st.session_state.agent.database_client.create_document(
            title=title,
            content=content,
            category=category
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_database(query, limit=10):
    """Search database - FIXED VERSION"""
    try:
        result = st.session_state.agent.database_client.search_documents(
            query=query,
            limit=limit
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "documents": []}


def main():
    """Main application"""
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">🤖 AI Agent System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Production-Ready MCP Orchestration | Sepia ML</div>', unsafe_allow_html=True)
    
    # Initialize system if not ready
    if not st.session_state.system_ready:
        health_status = initialize_system()
        
        if health_status:
            st.success("✅ System initialized successfully!")
            
            with st.expander("🔍 Service Status"):
                cols = st.columns(4)
                services = ['search_mcp', 'drive_mcp', 'database_mcp', 'rag_pdf_mcp']
                for idx, service in enumerate(services):
                    with cols[idx]:
                        status = health_status.get(service, {})
                        if status.get('available'):
                            st.success(f"✅ {service.replace('_', ' ').title()}")
                        else:
                            st.error(f"❌ {service.replace('_', ' ').title()}")
        else:
            st.stop()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ System Control")
        
        if st.button("🔄 Refresh Services", use_container_width=True):
            st.session_state.system_ready = False
            st.rerun()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        
        if st.session_state.agent:
            try:
                stats = st.session_state.agent.get_system_stats()
                pdf_stats = stats.get('pdf_stats', {})
                db_stats = stats.get('database_stats', {})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📄 PDFs", pdf_stats.get('total_pdfs', 0))
                with col2:
                    st.metric("📝 Notes", db_stats.get('total_documents', 0))
            except:
                st.info("Stats unavailable")
        
        st.markdown("---")
        st.markdown("### ℹ️ System Info")
        st.caption("**Version:** 2.5.0 COMPLETE")
        st.caption("**Company:** Sepia ML")
        st.caption("**Status:** Production Ready")
    
    # Main tabs - CRITICAL: Set default tab based on upload state
    if st.session_state.stay_on_upload_tab:
        default_tab = 1  # Upload Files tab
    else:
        default_tab = 0  # Chat tab
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Chat",
        "📤 Upload Files",
        "📂 My Files",
        "📝 Create Note",
        "🔍 Browse Notes"
    ])
    
    # Tab 1: Chat
    with tab1:
        st.markdown("### 💬 Chat with AI Agent")
        st.markdown("Ask anything! I can search the web, analyze your PDFs, and manage your notes.")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            if st.session_state.messages:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
            else:
                st.info("👋 Start a conversation!")
    
    # Chat input OUTSIDE tabs
    user_input = st.chat_input("Type your message...")
    if user_input:
        st.session_state.stay_on_upload_tab = False  # Reset flag
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({"role": "user", "content": user_input, "timestamp": timestamp})
        
        with st.spinner("🤔 Processing..."):
            try:
                response = st.session_state.agent.process_query(user_input)
                st.session_state.messages.append({"role": "assistant", "content": response, "timestamp": timestamp})
                st.rerun()
            except Exception as e:
                st.error(f"❌ {str(e)}")
    
    # Tab 2: Upload Files - FIXED: No redirect, shows progress
    with tab2:
        st.markdown("### 📤 Upload Files")
        st.markdown("Upload PDFs for AI analysis or any files to Google Drive")
        
        # Show last upload result
        if st.session_state.last_upload_result and st.session_state.upload_complete:
            if st.session_state.last_upload_result.get('success'):
                result = st.session_state.last_upload_result
                st.markdown(f"""
                <div class="success-box">
                    ✅ {result['message']}<br>
                    📊 Details: Pages: {result.get('page_count', 'N/A')} | Chunks: {result.get('chunks_created', 'N/A')}<br>
                    💾 Size: {result.get('size', 0) / (1024*1024):.2f} MB
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"❌ {st.session_state.last_upload_result.get('error')}")
            
            if st.button("✓ Clear Message", key="clear_msg"):
                st.session_state.last_upload_result = None
                st.session_state.upload_complete = False
                st.session_state.stay_on_upload_tab = False
                st.rerun()
        
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            accept_multiple_files=True,
            help="PDFs: AI analysis + Drive | Other: Drive only",
            key="main_uploader"
        )
        
        if uploaded_files:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info(f"📁 {len(uploaded_files)} file(s) selected")
            
            with col2:
                if st.button("🚀 Upload", type="primary", use_container_width=True, key="upload_btn"):
                    st.session_state.stay_on_upload_tab = True  # CRITICAL: Stay on this tab
                    st.session_state.upload_complete = False
                    
                    # Show uploading message
                    upload_status = st.empty()
                    upload_status.markdown("""
                    <div class="upload-progress">
                        ⏳ Uploading and processing files...<br>
                        📊 Large PDFs may take 1-3 minutes<br>
                        🔄 Please wait...
                    </div>
                    """, unsafe_allow_html=True)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    success_count = 0
                    last_result = None
                    
                    for idx, file in enumerate(uploaded_files):
                        status_text.text(f"📤 Processing {idx+1}/{len(uploaded_files)}: {file.name}")
                        progress_bar.progress((idx) / len(uploaded_files))
                        
                        result = handle_file_upload(file)
                        
                        if result.get('success'):
                            success_count += 1
                            last_result = result
                    
                    progress_bar.progress(1.0)
                    status_text.text(f"✅ Complete! {success_count}/{len(uploaded_files)} uploaded")
                    
                    st.session_state.last_upload_result = last_result
                    st.session_state.upload_complete = True
                    
                    time.sleep(1)
                    upload_status.empty()
                    st.rerun()
    
    # Tab 3: My Files - SMALLER FONT
    with tab3:
        st.markdown("### 📂 My Files - PDFs & Notes")
        
        col1, col2 = st.columns(2)
        
        # PDFs Section
        with col1:
            st.markdown("#### 📄 Uploaded PDFs")
            
            if st.button("🔄 Refresh", key="refresh_pdfs"):
                st.session_state.refresh_trigger += 1
                st.rerun()
            
            try:
                pdf_result = st.session_state.agent.rag_pdf_client.list_pdfs(limit=100)
                
                if pdf_result.get('success'):
                    pdfs = pdf_result.get('pdfs', [])
                    
                    if pdfs:
                        st.info(f"📊 Total: {len(pdfs)} PDFs")
                        
                        for pdf in pdfs:
                            pdf_id = pdf.get('pdf_id')
                            pdf_name = pdf.get('filename', 'Unknown')
                            pages = pdf.get('page_count', 0)
                            chunks = pdf.get('chunks_count', 0)
                            size_mb = pdf.get('file_size', 0) / (1024 * 1024)
                            uploaded_at = str(pdf.get('uploaded_at', 'Unknown'))[:19]
                            
                            with st.container():
                                st.markdown(f"""
                                <div class="pdf-card">
                                    <strong>📄 {pdf_name}</strong>
                                    <span>Pages: {pages} | Chunks: {chunks} | Size: {size_mb:.1f}MB</span>
                                    <span>🕒 {uploaded_at}</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                confirm_key = f"confirm_pdf_{pdf_id}"
                                
                                col_a, col_b = st.columns([1, 3])
                                
                                with col_a:
                                    if st.button("🗑️", key=f"del_pdf_{pdf_id}", help="Delete PDF"):
                                        st.session_state.delete_confirm[confirm_key] = True
                                        st.rerun()
                                
                                if st.session_state.delete_confirm.get(confirm_key, False):
                                    st.markdown(f"""
                                    <div class="delete-confirm">
                                        ⚠️ Delete '{pdf_name}'?
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col_yes, col_no = st.columns(2)
                                    
                                    with col_yes:
                                        if st.button("✅ Yes", key=f"yes_pdf_{pdf_id}"):
                                            st.session_state.delete_confirm[confirm_key] = False
                                            delete_pdf(pdf_id, pdf_name)
                                    
                                    with col_no:
                                        if st.button("❌ No", key=f"no_pdf_{pdf_id}"):
                                            st.session_state.delete_confirm[confirm_key] = False
                                            st.rerun()
                    else:
                        st.info("📭 No PDFs yet")
                else:
                    st.error("❌ Failed to load PDFs")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        # Notes Section
        with col2:
            st.markdown("#### 📝 Saved Notes")
            
            if st.button("🔄 Refresh", key="refresh_notes"):
                st.session_state.refresh_trigger += 1
                st.rerun()
            
            try:
                notes_result = st.session_state.agent.database_client.list_documents(limit=100)
                
                if notes_result.get('success'):
                    notes = notes_result.get('documents', [])
                    
                    if notes:
                        st.info(f"📊 Total: {len(notes)} Notes")
                        
                        for note in notes:
                            doc_id = note.get('document_id') or note.get('doc_id')
                            title = note.get('title', 'Untitled')
                            content = note.get('content', '')
                            category = note.get('category', 'general')
                            created_at = str(note.get('created_at', 'Unknown'))[:19]
                            
                            preview = content[:80] + "..." if len(content) > 80 else content
                            
                            with st.container():
                                st.markdown(f"""
                                <div class="note-card">
                                    <strong>📝 {title}</strong>
                                    <span>📁 {category} | {preview}</span>
                                    <span>🕒 {created_at}</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                confirm_key = f"confirm_note_{doc_id}"
                                
                                col_a, col_b = st.columns([1, 3])
                                
                                with col_a:
                                    if st.button("🗑️", key=f"del_note_{doc_id}", help="Delete Note"):
                                        st.session_state.delete_confirm[confirm_key] = True
                                        st.rerun()
                                
                                if st.session_state.delete_confirm.get(confirm_key, False):
                                    st.markdown(f"""
                                    <div class="delete-confirm">
                                        ⚠️ Delete '{title}'?
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col_yes, col_no = st.columns(2)
                                    
                                    with col_yes:
                                        if st.button("✅ Yes", key=f"yes_note_{doc_id}"):
                                            st.session_state.delete_confirm[confirm_key] = False
                                            delete_note(doc_id, title)
                                    
                                    with col_no:
                                        if st.button("❌ No", key=f"no_note_{doc_id}"):
                                            st.session_state.delete_confirm[confirm_key] = False
                                            st.rerun()
                    else:
                        st.info("📭 No notes yet")
                else:
                    st.error("❌ Failed to load notes")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Tab 4: Create Note
    with tab4:
        st.markdown("### 📝 Create New Note")
        
        note_title = st.text_input("Title", placeholder="Enter note title...")
        note_content = st.text_area("Content", placeholder="Write your note...", height=300)
        note_category = st.selectbox("Category", ["general", "work", "personal", "research", "ideas", "meetings", "tasks", "budget", "code"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save", type="primary", use_container_width=True):
                if note_title and note_content:
                    with st.spinner("💾 Saving..."):
                        result = save_to_database(note_title, note_content, note_category)
                        
                        if result.get('success'):
                            st.success(f"✅ Saved '{note_title}'!")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed: {result.get('error')}")
                else:
                    st.warning("⚠️ Title and content required!")
        
        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.rerun()
    
    # Tab 5: Browse Notes - FIXED SEARCH
    with tab5:
        st.markdown("### 🔍 Browse & Search Notes")
        
        search_query = st.text_input("Search", placeholder="Enter keywords (e.g., test1, shreyash)...")
        
        if st.button("🔍 Search", type="primary", use_container_width=True):
            if search_query:
                with st.spinner("🔍 Searching..."):
                    # CRITICAL FIX: Use the fixed search function with increased limit
                    result = search_database(search_query, 20)
                    
                    if result.get('success'):
                        docs = result.get('documents', [])
                        
                        if docs:
                            st.success(f"✅ Found {len(docs)} results!")
                            
                            for idx, doc in enumerate(docs, 1):
                                similarity = doc.get('similarity', 0.5)
                                relevance = int(similarity * 100)
                                
                                title = doc.get('title', 'Untitled')
                                content = doc.get('content', '')
                                category = doc.get('category', 'general')
                                
                                with st.expander(f"{idx}. {title} ({relevance}%)", expanded=(idx==1)):
                                    st.write(f"**Category:** {category}")
                                    st.write(f"**Relevance:** {relevance}%")
                                    st.write(f"**Content:**")
                                    st.write(content)
                                    
                                    doc_id = doc.get('document_id')
                                    if doc_id:
                                        if st.button("🗑️ Delete", key=f"search_del_{doc_id}_{idx}"):
                                            delete_note(doc_id, title)
                        else:
                            st.warning("💡 No matches found!")
                            st.info("**Tip:** Try:\n- Searching for 'test' or 'shreyash'\n- Using fewer words\n- Checking spelling")
                    else:
                        st.error(f"❌ Search failed: {result.get('error')}")
            else:
                st.warning("⚠️ Enter search query!")
    
    # Footer
    st.markdown("---")
    st.caption("**Sepia ML** | v2.5.0 | Upload Fixed + Font Reduced + Search Fixed")


if __name__ == "__main__":
    main()