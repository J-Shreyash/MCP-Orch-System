"""
AI Agent System - COMPLETE VERSION WITH ALL FEATURES + VALIDATION
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
Version: 5.1 - Production Ready with Validation

FEATURES:
✅ ChatGPT-style input with Send + Mic buttons
✅ 5 tabs: Chat, Upload Files, My Files, Create Note, Browse Notes
✅ CSV upload in same tab as PDF/files
✅ Visualizations in Chat tab only (no separate tab)
✅ All original features preserved
✅ Fixed: Validates notes before displaying (no more orphaned entries)
✅ Fixed: Delete now works properly with pre-validation
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
from datetime import datetime
import time
import json
import logging
import re
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional

# CRITICAL FIX: Add current directory to Python path FIRST
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Load environment variables BEFORE importing agent
from dotenv import load_dotenv
load_dotenv()  # Load .env file

# Now import agent and CSV modules
from agent import AIAgent
from csv_data_manager import CSVDataManager
from csv_query_engine import CSVQueryEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="AI Agent System - Sepia ML",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - ALL ORIGINAL STYLING PRESERVED
CUSTOM_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main-header {
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 15px 0 5px 0;
        margin-bottom: 0;
    }
    .sub-header {
        text-align: center;
        color: #888;
        font-size: 0.95em;
        margin-top: 0;
        padding-top: 0;
        margin-bottom: 20px;
    }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
    }
    
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
    
    .csv-card {
        padding: 12px;
        border: 2px solid #48bb78;
        border-radius: 10px;
        margin: 8px 0;
        background-color: #2d3748;
    }
    .csv-card strong {
        color: #9ae6b4 !important;
        font-size: 0.95em !important;
        display: block;
        margin-bottom: 6px;
    }
    .csv-card span {
        color: #e2e8f0 !important;
        display: block;
        margin: 3px 0;
        font-size: 0.85em !important;
    }
    
    .delete-confirm {
        padding: 12px;
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 10px;
        margin: 8px 0;
        color: #856404;
        font-size: 0.9em;
    }
    
    .success-box {
        padding: 15px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        color: #155724;
        margin: 10px 0;
        font-size: 0.95em;
    }
    
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
    
    .warning-box {
        padding: 12px;
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 10px;
        margin: 8px 0;
        color: #856404;
        font-size: 0.9em;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================================
# CHATGPT-STYLE INPUT WITH SEND BUTTON + MIC
# ============================================================================

def render_chatgpt_input_with_send():
    """ChatGPT-style input with Send button AND Mic button inside"""
    
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { 
            box-sizing: border-box; 
            margin: 0; 
            padding: 0; 
        }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: transparent;
            padding: 0;
        }
        
        .input-container {
            position: relative;
            width: 100%;
            max-width: 100%;
        }
        
        .input-wrapper {
            position: relative;
            display: flex;
            align-items: center;
            background: #40414f;
            border: 1px solid #565869;
            border-radius: 12px;
            padding: 12px 16px;
            transition: all 0.2s ease;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        
        .input-wrapper:focus-within {
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
        }
        
        .input-wrapper.recording {
            border-color: #ff4444;
            box-shadow: 0 0 0 2px rgba(255, 68, 68, 0.2);
            background: rgba(255, 68, 68, 0.05);
        }
        
        .text-input {
            flex: 1;
            background: transparent;
            border: none;
            color: #ececf1;
            font-size: 16px;
            line-height: 24px;
            outline: none;
            padding: 8px 12px;
            resize: none;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .text-input::placeholder {
            color: #8e8ea0;
        }
        
        .text-input::-webkit-scrollbar {
            width: 8px;
        }
        
        .text-input::-webkit-scrollbar-thumb {
            background: #565869;
            border-radius: 4px;
        }
        
        .button-group {
            display: flex;
            gap: 6px;
            margin-left: 8px;
        }
        
        .icon-button {
            width: 36px;
            height: 36px;
            min-width: 36px;
            border-radius: 8px;
            background: transparent;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            padding: 0;
        }
        
        .icon-button:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .icon-button:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }
        
        .icon-button:disabled:hover {
            background: transparent;
        }
        
        .mic-button.recording {
            background: #ff4444;
            animation: pulse-recording 2s ease-in-out infinite;
        }
        
        .mic-button.recording:hover {
            background: #ff5555;
        }
        
        @keyframes pulse-recording {
            0%, 100% {
                box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.7);
            }
            50% {
                box-shadow: 0 0 0 8px rgba(255, 68, 68, 0);
            }
        }
        
        .send-button {
            background: #19c37d;
            opacity: 1;
            visibility: visible;
        }
        
        .send-button:hover:not(:disabled) {
            background: #17b373;
        }
        
        .send-button:disabled {
            background: #565869;
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .icon {
            width: 20px;
            height: 20px;
            fill: #acacbe;
            transition: fill 0.2s ease;
        }
        
        .icon-button:hover .icon {
            fill: #ececf1;
        }
        
        .mic-button.recording .icon {
            fill: #ffffff;
        }
        
        .send-button .icon {
            fill: #ffffff;
            opacity: 1;
        }
        
        .send-button:disabled .icon {
            fill: #8e8ea0;
            opacity: 0.7;
        }
        
        .status-indicator {
            position: absolute;
            bottom: -28px;
            left: 16px;
            font-size: 12px;
            color: #8e8ea0;
            display: none;
        }
        
        .status-indicator.active {
            display: block;
        }
        
        .status-indicator.recording {
            color: #ff4444;
            font-weight: 600;
        }
        
        .waveform {
            position: absolute;
            bottom: -32px;
            left: 50%;
            transform: translateX(-50%);
            display: none;
            gap: 3px;
            align-items: center;
            height: 20px;
        }
        
        .waveform.active {
            display: flex;
        }
        
        .wave-bar {
            width: 3px;
            background: #667eea;
            border-radius: 2px;
            animation: wave 1.2s ease-in-out infinite;
        }
        
        .wave-bar:nth-child(1) { animation-delay: 0s; }
        .wave-bar:nth-child(2) { animation-delay: 0.1s; }
        .wave-bar:nth-child(3) { animation-delay: 0.2s; }
        .wave-bar:nth-child(4) { animation-delay: 0.3s; }
        .wave-bar:nth-child(5) { animation-delay: 0.4s; }
        
        @keyframes wave {
            0%, 100% { height: 6px; }
            50% { height: 18px; }
        }
    </style>
    </head>
    <body>
    
    <div class="input-container">
        <div class="input-wrapper" id="inputWrapper">
            <textarea 
                class="text-input" 
                id="textInput" 
                placeholder="Message AI Agent..." 
                rows="1"
                autocomplete="off"
            ></textarea>
            
            <div class="button-group">
                <button class="icon-button mic-button" id="micButton" title="Voice input">
                    <svg class="icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                    </svg>
                </button>
                
                <button class="icon-button send-button" id="sendButton" title="Send message">
                    <svg class="icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
        </div>
        
        <div class="waveform" id="waveform">
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
        </div>
        
        <div class="status-indicator" id="statusIndicator"></div>
    </div>
    
    <script>
        console.log('[Init] Component starting...');
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            const statusIndicator = document.getElementById('statusIndicator');
            statusIndicator.textContent = 'Voice input requires Chrome/Edge browser';
            statusIndicator.classList.add('active');
            document.getElementById('micButton').disabled = true;
            document.getElementById('micButton').style.opacity = '0.3';
        } else {
            const micButton = document.getElementById('micButton');
            const sendButton = document.getElementById('sendButton');
            const textInput = document.getElementById('textInput');
            const inputWrapper = document.getElementById('inputWrapper');
            const waveform = document.getElementById('waveform');
            const statusIndicator = document.getElementById('statusIndicator');
            
            let recognition = new SpeechRecognition();
            let isRecording = false;
            let finalTranscript = '';
            let messageCounter = 0;
            
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';
            recognition.maxAlternatives = 1;
            
            function updateSendButton() {
                const hasText = textInput.value.trim().length > 0;
                if (hasText) {
                    sendButton.disabled = false;
                    sendButton.style.opacity = '1';
                    sendButton.style.background = '#19c37d';
                } else {
                    sendButton.disabled = true;
                    sendButton.style.opacity = '0.5';
                    sendButton.style.background = '#565869';
                }
            }
            
            textInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 200) + 'px';
                updateSendButton();
            });
            
            recognition.onresult = (event) => {
                let interimTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript + ' ';
                    } else {
                        interimTranscript += transcript;
                    }
                }
                
                textInput.value = (finalTranscript + interimTranscript).trim();
                textInput.style.height = 'auto';
                textInput.style.height = Math.min(textInput.scrollHeight, 200) + 'px';
                updateSendButton();
            };
            
            recognition.onstart = () => {
                isRecording = true;
                micButton.classList.add('recording');
                inputWrapper.classList.add('recording');
                waveform.classList.add('active');
                statusIndicator.textContent = 'Listening...';
                statusIndicator.classList.add('active', 'recording');
            };
            
            recognition.onend = () => {
                if (isRecording) {
                    try {
                        recognition.start();
                    } catch (e) {
                        stopRecording();
                    }
                } else {
                    stopRecording();
                }
            };
            
            recognition.onerror = (event) => {
                console.error('[Voice] Error:', event.error);
                stopRecording();
            };
            
            function stopRecording() {
                isRecording = false;
                micButton.classList.remove('recording');
                inputWrapper.classList.remove('recording');
                waveform.classList.remove('active');
                statusIndicator.classList.remove('active', 'recording');
                
                try {
                    recognition.stop();
                } catch (e) {}
                
                textInput.focus();
            }
            
            micButton.addEventListener('click', (e) => {
                e.preventDefault();
                
                if (!isRecording) {
                    finalTranscript = textInput.value.trim();
                    if (finalTranscript) {
                        finalTranscript += ' ';
                    }
                    
                    try {
                        recognition.start();
                    } catch (e) {
                        console.error('[Mic] Start error:', e);
                    }
                } else {
                    stopRecording();
                }
            });
            
            function sendMessage() {
                const text = textInput.value.trim();
                
                if (!text) {
                    console.log('[Send] ⚠️ Empty message, not sending');
                    return;
                }
                
                messageCounter++;
                const msgId = messageCounter;
                const messageValue = text + '|||MSG' + msgId + '|||' + Date.now();
                
                console.log('[Send] 📤 Sending message:', messageValue.substring(0, 50));
                
                // Streamlit components require this specific message format
                const payload = {
                    type: 'streamlit:setComponentValue',
                    value: messageValue
                };
                
                // Method 1: Send to parent window (primary method)
                let messageSent = false;
                try {
                    if (window.parent && window.parent !== window) {
                        window.parent.postMessage(payload, '*');
                        messageSent = true;
                        console.log('[Send] ✅ Message sent to window.parent');
                    }
                } catch (e) {
                    console.error('[Send] ❌ Error sending to parent:', e);
                }
                
                // Method 2: Try sending to top window
                if (!messageSent) {
                    try {
                        if (window.top && window.top !== window) {
                            window.top.postMessage(payload, '*');
                            messageSent = true;
                            console.log('[Send] ✅ Message sent to window.top');
                        }
                    } catch (e) {
                        console.error('[Send] ❌ Error sending to top:', e);
                    }
                }
                
                // Method 3: Try direct window postMessage
                if (!messageSent) {
                    try {
                        window.postMessage(payload, '*');
                        console.log('[Send] ✅ Message sent to window');
                    } catch (e) {
                        console.error('[Send] ❌ Error with window.postMessage:', e);
                    }
                }
                
                // Method 4: Store in localStorage as fallback
                try {
                    localStorage.setItem('streamlit_chat_message', messageValue);
                    localStorage.setItem('streamlit_chat_timestamp', Date.now().toString());
                    console.log('[Send] ✅ Message stored in localStorage');
                } catch (e) {
                    console.error('[Send] ❌ Error with localStorage:', e);
                }
                
                // Method 5: Try to access Streamlit's component frame directly
                try {
                    // Find the Streamlit iframe
                    const frames = window.parent.frames || [];
                    for (let i = 0; i < frames.length; i++) {
                        try {
                            frames[i].postMessage(payload, '*');
                            console.log('[Send] ✅ Message sent to frame', i);
                        } catch (e) {
                            // Ignore cross-origin errors
                        }
                    }
                } catch (e) {
                    console.log('[Send] Could not access frames:', e.message);
                }
                
                // Clear input immediately (user feedback)
                textInput.value = '';
                textInput.style.height = 'auto';
                finalTranscript = '';
                updateSendButton();
                
                console.log('[Send] ✅ Input cleared, waiting for Streamlit to process...');
            }
            
            sendButton.addEventListener('click', (e) => {
                e.preventDefault();
                sendMessage();
            });
            
            textInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    sendMessage();
                    return false;
                }
            });
            
            // Also prevent form submission if textarea is inside a form
            const form = textInput.closest('form');
            if (form) {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (textInput.value.trim()) {
                        sendMessage();
                    }
                    return false;
                });
            }
            
            updateSendButton();
        }
    </script>
    
    </body>
    </html>
    """
    
    result = components.html(html_code, height=90, scrolling=False)
    return result


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def restore_csv_tables_from_database():
    """
    Restore CSV tables metadata from database on page refresh
    This ensures uploaded CSV files persist after refresh
    """
    try:
        if not st.session_state.csv_manager:
            return
        
        # System tables to exclude (configurable via env, no hardcoding)
        system_tables_env = os.getenv("SYSTEM_TABLES_EXCLUDE")
        if system_tables_env:
            system_tables = {table.strip().lower() for table in system_tables_env.split(',')}
        else:
            # Smart default: detect system tables dynamically (tables that aren't user CSV uploads)
            system_tables = {
                'documents', 'pdfs', 'activity_logs', 'csv_metadata',
                'migrations', 'schema_migrations', 'users', 'sessions'
            }
        
        # List all tables from database
        all_tables = st.session_state.csv_manager.list_tables()
        
        if not all_tables:
            return
        
        # Filter out system tables and get metadata for CSV tables
        csv_tables_restored = {}
        
        for table_name in all_tables:
            # Ensure table_name is a string
            if not isinstance(table_name, str):
                table_name = str(table_name)
            
            # Skip system tables (case-insensitive)
            if table_name.lower() in system_tables:
                continue
            
            # Get table info
            table_info = st.session_state.csv_manager.get_table_info(table_name)
            
            if table_info:
                row_count = table_info.get('row_count', 0)
                column_count = table_info.get('column_count', 0)
                columns = table_info.get('columns', [])
                
                # Extract column names from column definitions
                column_names = []
                if columns:
                    for col in columns:
                        if isinstance(col, (list, tuple)) and len(col) > 0:
                            column_names.append(col[0])
                        elif isinstance(col, dict):
                            column_names.append(col.get('Field', col.get('field', '')))
                
                # Restore metadata
                csv_tables_restored[table_name] = {
                    "rows": row_count,
                    "columns": column_count,
                    "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Approximate
                    "filename": f"{table_name}.csv",  # Approximate
                    "size_mb": 0,  # Not stored, set to 0
                    "column_names": column_names if column_names else [col.get('Field', '') for col in columns]
                }
        
        # Restore to session state
        st.session_state.csv_tables = csv_tables_restored
        
        if csv_tables_restored:
            logger.info(f"✅ Restored {len(csv_tables_restored)} CSV tables from database")
        
    except Exception as e:
        logger.error(f"❌ Failed to restore CSV tables: {e}", exc_info=True)
        # Don't fail initialization if restore fails
        pass


def init_session_state():
    """Initialize all session state variables"""
    logger.info("Initializing session state...")
    
    # Chat messages
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        logger.info("Initialized chat messages")
    
    # AI Agent
    if 'agent' not in st.session_state:
        try:
            logger.info("Initializing AI Agent...")
            st.session_state.agent = AIAgent()
            logger.info("✅ AI Agent initialized successfully")
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}")
            st.session_state.agent = None
    
    # CSV Manager
    if 'csv_manager' not in st.session_state:
        if st.session_state.agent and hasattr(st.session_state.agent, 'db_client'):
            try:
                st.session_state.csv_manager = CSVDataManager(st.session_state.agent.db_client)
                logger.info("✅ CSV Manager initialized")
            except Exception as e:
                logger.warning(f"⚠️ CSV Manager init failed: {e}")
                st.session_state.csv_manager = None
        else:
            st.session_state.csv_manager = None
    
    # CSV Query Engine
    if 'csv_query_engine' not in st.session_state:
        if st.session_state.agent and hasattr(st.session_state.agent, 'db_client'):
            try:
                st.session_state.csv_query_engine = CSVQueryEngine(st.session_state.agent.db_client)
                logger.info("✅ CSV Query Engine initialized")
            except Exception as e:
                logger.warning(f"⚠️ CSV Query Engine init failed: {e}")
                st.session_state.csv_query_engine = None
        else:
            st.session_state.csv_query_engine = None
    
    # CSV tables tracking
    if 'csv_tables' not in st.session_state:
        st.session_state.csv_tables = {}
    
    if 'csv_tables_restored' not in st.session_state:
        st.session_state.csv_tables_restored = False
    
    # Restore CSV tables from database if not already restored and CSV manager is available
    # This ensures CSV files persist after page refresh
    if not st.session_state.csv_tables_restored and st.session_state.csv_manager:
        try:
            restore_csv_tables_from_database()
            st.session_state.csv_tables_restored = True
            if st.session_state.csv_tables:
                logger.info(f"✅ Restored {len(st.session_state.csv_tables)} CSV tables from database")
        except Exception as e:
            logger.warning(f"⚠️ Failed to restore CSV tables: {e}")
            # Still mark as attempted to avoid repeated failures
            st.session_state.csv_tables_restored = True
    
    # Current table
    if 'current_table' not in st.session_state:
        st.session_state.current_table = None
    
    # System state
    if 'system_ready' not in st.session_state:
        st.session_state.system_ready = False
    
    # Upload results
    if 'last_upload_result' not in st.session_state:
        st.session_state.last_upload_result = None
    
    # Delete confirmations
    if 'delete_confirm' not in st.session_state:
        st.session_state.delete_confirm = {}
    
    # Upload completion flag
    if 'upload_complete' not in st.session_state:
        st.session_state.upload_complete = False
    
    # Last processed message
    if 'last_processed' not in st.session_state:
        st.session_state.last_processed = ''
    
    # Query results for visualization
    if 'query_results' not in st.session_state:
        st.session_state.query_results = None
    
    # Viz data
    if 'viz_data' not in st.session_state:
        st.session_state.viz_data = None
    
    # CSV file display state - track which messages have been expanded
    if 'csv_display_expanded' not in st.session_state:
        st.session_state.csv_display_expanded = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_env_file():
    """Check if .env file exists and has OPENAI_API_KEY"""
    # Check multiple possible locations
    possible_paths = [
        Path(__file__).parent / '.env',
        Path.cwd() / '.env',
        Path.home() / '.env'
    ]
    
    for env_path in possible_paths:
        if env_path.exists():
            logger.info(f"Found .env file at: {env_path}")
            load_dotenv(env_path)
            break
    else:
        logger.warning("No .env file found in standard locations")
    
    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found in environment variables!")
        st.info("**Please add your API key to `.env` file:**")
        st.code("OPENAI_API_KEY=your_key_here")
        return False
    
    logger.info("✅ OPENAI_API_KEY found")
    return True


def initialize_system():
    """Initialize AI Agent System"""
    try:
        if not check_env_file():
            return None
        
        with st.spinner("🔄 Initializing AI Agent System..."):
            if st.session_state.agent is None:
                st.session_state.agent = AIAgent()
            
            # Check service health
            health_status = {
                'search_mcp': {'available': st.session_state.agent.search_client.is_available() if st.session_state.agent.search_client else False},
                'drive_mcp': {'available': st.session_state.agent.drive_client.is_available() if st.session_state.agent.drive_client else False},
                'database_mcp': {'available': st.session_state.agent.db_client.is_available() if st.session_state.agent.db_client else False},
                'rag_pdf_mcp': {'available': st.session_state.agent.rag_client.is_available() if st.session_state.agent.rag_client else False}
            }
            
            st.session_state.system_ready = True
            return health_status
            
    except Exception as e:
        st.error(f"❌ Initialization failed: {str(e)}")
        logger.error(f"System initialization failed: {e}", exc_info=True)
        return None


def handle_file_upload(uploaded_file):
    """Handle file upload - supports PDF, CSV, and other files"""
    try:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name
        file_type = uploaded_file.type
        file_size = len(file_bytes)
        
        # Check file size
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            return {"success": False, "error": "File too large! Max: 100MB"}
        
        # Create temp directory
        temp_dir = Path.home() / "AppData" / "Local" / "Temp" / "agent_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / file_name
        
        # Save file
        with open(temp_path, "wb") as f:
            f.write(file_bytes)
        
        # Handle based on file type
        if file_type == "application/pdf" or file_name.endswith('.pdf'):
            # PDF upload
            result = st.session_state.agent.rag_client.upload_pdf(str(temp_path))
            if result.get('success'):
                return {
                    "success": True,
                    "file_type": "pdf",
                    "file_name": file_name,
                    "page_count": result.get('page_count', 0),
                    "chunks_created": result.get('chunks_created', 0),
                    "size": file_size,
                    "message": f"✅ PDF '{file_name}' processed successfully!"
                }
            return {"success": False, "error": result.get('error', 'Unknown error')}
        
        elif file_type == "text/csv" or file_name.endswith('.csv'):
            # CSV upload
            df = pd.read_csv(temp_path)
            table_name = Path(file_name).stem.lower().replace(' ', '_').replace('-', '_')
            
            result = st.session_state.csv_manager.upload_csv(df, table_name, show_progress=False)
            if result.get('success'):
                # Store in session state
                st.session_state.csv_tables[table_name] = {
                    "rows": result.get("rows_inserted", len(df)),
                    "columns": len(df.columns),
                    "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "filename": file_name,
                    "size_mb": file_size / (1024 * 1024),
                    "column_names": list(df.columns)
                }
                st.session_state.current_table = table_name
                
                return {
                    "success": True,
                    "file_type": "csv",
                    "file_name": file_name,
                    "table_name": table_name,
                    "rows": result.get("rows_inserted", 0),
                    "columns": len(df.columns),
                    "size": file_size,
                    "message": f"✅ CSV '{file_name}' uploaded as table '{table_name}'!"
                }
            return {"success": False, "error": result.get('error', 'Unknown error')}
        
        else:
            # Other files - upload to Drive
            result = st.session_state.agent.drive_client.upload_file(str(temp_path))
            if result.get('success'):
                return {
                    "success": True,
                    "file_type": "other",
                    "file_name": file_name,
                    "size": file_size,
                    "message": f"✅ File '{file_name}' uploaded to Drive!"
                }
            return {"success": False, "error": result.get('error', 'Unknown error')}
            
    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def delete_pdf(pdf_id, pdf_name):
    """Delete PDF"""
    try:
        result = st.session_state.agent.rag_client.delete_pdf(pdf_id)
        if result.get('success'):
            st.success(f"✅ Deleted '{pdf_name}'!")
            st.balloons()
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"❌ Failed: {result.get('error')}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def delete_csv_table(table_name):
    """Delete CSV table"""
    try:
        result = st.session_state.csv_manager.delete_table(table_name)
        if result.get('success'):
            if table_name in st.session_state.csv_tables:
                del st.session_state.csv_tables[table_name]
            if st.session_state.current_table == table_name:
                st.session_state.current_table = None
            st.success(f"✅ Deleted table '{table_name}'!")
            st.balloons()
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"❌ Failed: {result.get('error')}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def delete_note(doc_id, title):
    """
    Delete note with pre-validation
    CRITICAL FIX: Validates document exists before attempting delete
    """
    try:
        if not doc_id or str(doc_id).lower() == 'none':
            st.error("❌ Invalid document ID")
            logger.error(f"Invalid doc_id: {doc_id}")
            return
        
        logger.info(f"Attempting to delete note: {title} (ID: {doc_id})")
        
        # CRITICAL FIX: First verify the document exists
        verify_result = st.session_state.agent.db_client.get_document(doc_id)
        
        if not verify_result.get('success'):
            st.warning(f"⚠️ Note '{title}' not found - may have been already deleted")
            logger.warning(f"Document {doc_id} doesn't exist")
            time.sleep(2)
            st.rerun()
            return
        
        # Document exists, proceed with delete
        result = st.session_state.agent.db_client.delete_document(doc_id)
        
        logger.info(f"Delete result: {result}")
        
        if result and result.get('success'):
            st.success(f"✅ Deleted '{title}'!")
            st.balloons()
            time.sleep(1)
            st.rerun()
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No response from server'
            st.error(f"❌ Failed to delete: {error_msg}")
            logger.error(f"Delete failed: {error_msg}")
    
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Error: {error_msg}")
        logger.error(f"Delete note exception: {e}", exc_info=True)


def save_to_database(title, content, category="general"):
    """Save note to database"""
    try:
        return st.session_state.agent.db_client.create_document(
            title=title, content=content, category=category
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_database(query, limit=10):
    """Search database"""
    try:
        return st.session_state.agent.db_client.search_documents(
            query=query, limit=limit
        )
    except Exception as e:
        return {"success": False, "error": str(e), "documents": []}


def generate_data_explanation(df: pd.DataFrame, table_name: str) -> str:
    """
    Generate explanation of what the data represents using OpenAI GPT-4o-mini
    
    Args:
        df: DataFrame with the data
        table_name: Name of the table/CSV file
        
    Returns:
        Explanation string
    """
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Unable to generate explanation: OpenAI API key not found."
        
        client = OpenAI(api_key=api_key)
        
        # Get sample data and column info
        sample_data = df.head(5).to_dict('records')
        columns = list(df.columns)
        column_types = {col: str(df[col].dtype) for col in columns}
        
        # Build prompt
        prompt = f"""Analyze this CSV data and provide a short, clear explanation (2-3 sentences) of what this data represents.

Table/File Name: {table_name}
Columns: {', '.join(columns)}
Column Types: {column_types}
Sample Data (first 5 rows): {sample_data}

Provide a clear, concise explanation that helps a user understand:
1. What kind of data this is
2. What the main purpose or context is
3. What insights could be derived from it

Keep it brief (2-3 sentences max) and easy to understand."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a data analyst. Provide clear, concise explanations of datasets in 2-3 sentences."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        explanation = response.choices[0].message.content.strip()
        return explanation
        
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        return f"Unable to generate explanation: {str(e)}"


def render_visualization(query_result):
    """Render visualization in chat based on query result"""
    if not query_result or not query_result.get("success"):
        return
    
    data = query_result.get("data", [])
    if not data:
        return
    
    try:
        # Convert to DataFrame
        if isinstance(data[0], (list, tuple)):
            # If data is list of lists/tuples, try to infer column names from first row
            if len(data) > 0 and isinstance(data[0], (list, tuple)):
                # Check if first row might be headers
                if all(isinstance(x, str) for x in data[0]):
                    df = pd.DataFrame(data[1:], columns=data[0])
                else:
                    df = pd.DataFrame(data)
            else:
                df = pd.DataFrame(data)
        else:
            df = pd.DataFrame(data)
        
        # Clean up DataFrame - remove any unnamed columns
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Detect numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        
        if not numeric_cols:
            st.info("ℹ️ No numeric columns available for visualization. Showing data summary instead.")
            st.dataframe(df.describe(include='all') if len(df) > 0 else df.head(), use_container_width=True)
            return
        
        st.markdown("### 📈 Data Visualizations")
        
        # Generate multiple visualizations based on data structure
        viz_count = 0
        
        # 1. If there are categorical and numeric columns, create bar chart
        if cat_cols and numeric_cols:
            # Use first categorical and first numeric column
            cat_col = cat_cols[0]
            num_col = numeric_cols[0]
            
            # Aggregate if there are many unique categories
            if df[cat_col].nunique() > 20:
                # Group by category and sum/average the numeric column
                df_agg = df.groupby(cat_col)[num_col].sum().reset_index()
                df_agg = df_agg.sort_values(num_col, ascending=False).head(20)
                fig = px.bar(df_agg, x=cat_col, y=num_col,
                            title=f"{num_col} by {cat_col} (Top 20)",
                            labels={cat_col: cat_col, num_col: num_col})
            else:
                df_viz = df.groupby(cat_col)[num_col].sum().reset_index() if len(df) > 100 else df
                fig = px.bar(df_viz, x=cat_col, y=num_col,
                            title=f"{num_col} by {cat_col}",
                            labels={cat_col: cat_col, num_col: num_col})
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            viz_count += 1
        
        # 2. Histogram for numeric columns
        if numeric_cols:
            for num_col in numeric_cols[:2]:  # Show max 2 histograms
                fig = px.histogram(df, x=num_col, 
                                 title=f"Distribution of {num_col}",
                                 nbins=30)
                st.plotly_chart(fig, use_container_width=True)
                viz_count += 1
                if viz_count >= 3:  # Limit total visualizations
                    break
        
        # 3. Scatter plot if we have 2+ numeric columns
        if len(numeric_cols) >= 2 and viz_count < 3:
            fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1],
                           title=f"{numeric_cols[1]} vs {numeric_cols[0]}",
                           labels={numeric_cols[0]: numeric_cols[0], 
                                  numeric_cols[1]: numeric_cols[1]})
            st.plotly_chart(fig, use_container_width=True)
            viz_count += 1
        
        # 4. Pie chart if we have categorical data with reasonable number of categories
        if cat_cols and numeric_cols and viz_count < 3:
            cat_col = cat_cols[0]
            num_col = numeric_cols[0]
            if df[cat_col].nunique() <= 10:
                df_pie = df.groupby(cat_col)[num_col].sum().reset_index()
                fig = px.pie(df_pie, names=cat_col, values=num_col,
                           title=f"Distribution of {num_col} by {cat_col}")
                st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Visualization error: {e}", exc_info=True)
        st.error(f"Could not create visualization: {e}")
        # Fallback: show raw data
        try:
            st.dataframe(pd.DataFrame(data[:20]), use_container_width=True)
        except:
            pass


def detect_csv_file_query(text: str, csv_tables: dict) -> Optional[str]:
    """
    Detect if user wants to see data from a specific CSV file
    
    Args:
        text: User's query text
        csv_tables: Dictionary of available CSV tables
        
    Returns:
        Table name if detected, None otherwise
    """
    text_lower = text.lower()
    
    # Patterns for "show me data from [file]"
    patterns = [
        r'show\s+me\s+data\s+from\s+(.+)',
        r'display\s+data\s+from\s+(.+)',
        r'show\s+data\s+from\s+(.+)',
        r'view\s+data\s+from\s+(.+)',
        r'see\s+data\s+from\s+(.+)',
        r'get\s+data\s+from\s+(.+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            file_ref = match.group(1).strip()
            
            # Try to match against table names or filenames
            for table_name, table_info in csv_tables.items():
                filename = table_info.get('filename', '').lower()
                # Check if file_ref matches table name or filename
                if file_ref in table_name.lower() or file_ref in filename:
                    return table_name
            
            # If no exact match, try partial match
            for table_name in csv_tables.keys():
                if file_ref in table_name.lower():
                    return table_name
    
    return None


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application"""
    
    # Initialize session state
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">🤖 AI Agent System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">📤 Send + 🎤 Mic | Powered by Sepia ML</div>', unsafe_allow_html=True)
    
    # Initialize system if not ready
    if not st.session_state.system_ready:
        health = initialize_system()
        if health:
            st.success("✅ System initialized successfully!")
            with st.expander("🔍 Service Status"):
                cols = st.columns(4)
                services = ['search_mcp', 'drive_mcp', 'database_mcp', 'rag_pdf_mcp']
                service_names = ['Search', 'Drive', 'Database', 'RAG PDF']
                for idx, (service, name) in enumerate(zip(services, service_names)):
                    with cols[idx]:
                        status = health.get(service, {})
                        if status.get('available'):
                            st.success(f"✅ {name}")
                        else:
                            st.error(f"❌ {name}")
            
            # Restore CSV tables after system is initialized (in case restore didn't run earlier)
            if st.session_state.csv_manager and not st.session_state.csv_tables_restored:
                try:
                    restore_csv_tables_from_database()
                    st.session_state.csv_tables_restored = True
                except Exception as e:
                    logger.warning(f"⚠️ Failed to restore CSV tables after system init: {e}")
        else:
            st.warning("⚠️ System started with limited functionality")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ System Control")
        
        if st.button("🔄 Refresh Services", use_container_width=True):
            st.session_state.system_ready = False
            st.rerun()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.query_results = None
            st.session_state.viz_data = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        
        if st.session_state.agent:
            try:
                # Get stats
                col1, col2 = st.columns(2)
                
                with col1:
                    # PDF count
                    try:
                        pdfs = st.session_state.agent.rag_client.list_pdfs(limit=1)
                        pdf_count = len(pdfs.get('pdfs', [])) if pdfs.get('success') else 0
                        st.metric("📄 PDFs", pdf_count)
                    except:
                        st.metric("📄 PDFs", "N/A")
                
                with col2:
                    # Notes count
                    try:
                        notes = st.session_state.agent.db_client.list_documents(limit=1000, validate=True)
                        note_count = notes.get('total_documents', 0) if notes.get('success') else 0
                        st.metric("📝 Notes", note_count)
                    except:
                        st.metric("📝 Notes", "N/A")
                
                # CSV count
                csv_count = len(st.session_state.csv_tables)
                st.metric("📊 CSV Tables", csv_count)
                
            except Exception as e:
                st.info("Stats unavailable")
                logger.error(f"Stats error: {e}")
        
        st.markdown("---")
        st.markdown("### ℹ️ Info")
        st.caption("**Version:** 5.1 Production")
        st.caption("**Company:** Sepia ML")
        st.caption("**Developer:** Shreyash Jadhav")
    
    # Main tabs - ALL 5 ORIGINAL TABS
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Chat",
        "📤 Upload Files",
        "📂 My Files",
        "📝 Create Note",
        "🔍 Browse Notes"
    ])
    
    # ========================================================================
    # TAB 1: CHAT
    # ========================================================================
    with tab1:
        # Display chat history
        for idx, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
                # Special handling for CSV file display
                if msg.get("csv_file_display"):
                    preview_data = msg.get("preview_data", [])
                    table_name = msg.get("table_name", "unknown")
                    full_data = msg.get("full_data", [])
                    row_count = msg.get("row_count", 0)
                    
                    if preview_data:
                        # Convert to DataFrame for display
                        df_preview = pd.DataFrame(preview_data[:10])
                        
                        # Display data preview in a nice table format
                        st.markdown("**Data Preview (first 10 rows):**")
                        st.dataframe(df_preview, use_container_width=True, hide_index=True)
                        
                        # Create unique key for this message
                        msg_key = f"csv_display_{idx}"
                        is_expanded = st.session_state.csv_display_expanded.get(msg_key, False)
                        
                        # Button to continue (show explanation and visualizations)
                        if not is_expanded:
                            if st.button("📊 Generate Analysis & Visualizations", key=f"btn_{msg_key}"):
                                st.session_state.csv_display_expanded[msg_key] = True
                                st.rerun()
                        else:
                            # Show explanation
                            st.markdown("---")
                            st.markdown("### 📝 Data Explanation")
                            
                            with st.spinner("Generating explanation..."):
                                df_full = pd.DataFrame(full_data) if full_data else df_preview
                                explanation = generate_data_explanation(df_full, table_name)
                                st.write(explanation)
                            
                            # Show visualizations
                            st.markdown("---")
                            if full_data:
                                viz_result = {
                                    "success": True,
                                    "data": full_data,
                                    "row_count": len(full_data)
                                }
                                render_visualization(viz_result)
                            else:
                                viz_result = {
                                    "success": True,
                                    "data": preview_data,
                                    "row_count": len(preview_data)
                                }
                                render_visualization(viz_result)
                
                # If message has visualization data (regular query), show it
                elif msg.get("viz_data") is not None:
                    render_visualization(msg.get("viz_data"))
        
        if not st.session_state.messages:
            st.info("👋 Welcome! Type, speak, or click Send button to start.")
        
        st.markdown("---")
        
        # Initialize message_value
        message_value = None
        
        # Use Streamlit's native chat input for reliable Enter key handling
        # This ensures Enter key always works
        user_input = st.chat_input("Type your message here and press Enter...")
        
        if user_input:
            # Process native chat input
            message_value = user_input + '|||MSG' + str(int(time.time() * 1000)) + '|||' + str(int(time.time() * 1000))
            logger.info(f"✅ Received from native chat input: {user_input[:50]}...")
        else:
            # Also render custom component for mic button (for voice input)
            voice_result = render_chatgpt_input_with_send()
            
            # Debug: Log what we received
            logger.debug(f"Component result type: {type(voice_result)}, value: {voice_result}")
            
            # Process messages from custom component - handle both string and dict responses
            if voice_result is not None:
                if isinstance(voice_result, str):
                    message_value = voice_result
                elif isinstance(voice_result, dict):
                    message_value = voice_result.get('value') or voice_result.get('data')
                elif hasattr(voice_result, 'value'):
                    message_value = getattr(voice_result, 'value', None)
                
                # Store component value in session state for debugging
                if message_value:
                    logger.info(f"✅ Received component value: {str(message_value)[:100]}...")
                    # Store in session state to help with debugging
                    if 'last_component_value' not in st.session_state or st.session_state.last_component_value != message_value:
                        st.session_state.last_component_value = message_value
                else:
                    logger.debug("⚠️ No message value received from component")
        
        # Process message if we have one
        if message_value and isinstance(message_value, str) and '|||MSG' in message_value:
            try:
                parts = message_value.split('|||MSG')
                text = parts[0].strip()
                msg_id = parts[1].split('|||')[0] if len(parts) > 1 else ''
                
                unique_key = f"{text}_{msg_id}"
                
                if text and unique_key != st.session_state.last_processed:
                    st.session_state.last_processed = unique_key
                    
                    # Add user message
                    st.session_state.messages.append({"role": "user", "content": text})
                    
                    # Check if this is a "Show me data from CSV file" query
                    detected_table = None
                    if st.session_state.csv_tables:
                        detected_table = detect_csv_file_query(text, st.session_state.csv_tables)
                    
                    # Check if this is a CSV query
                    # EXCLUDE "show all my documents" type queries from CSV detection
                    is_csv_query = False
                    list_all_patterns = [
                        'show all', 'list all', 'show my', 'list my', 
                        'all documents', 'all files', 'all pdfs', 'all notes',
                        'my documents', 'my files', 'uploaded documents'
                    ]
                    is_list_all_query = any(pattern in text.lower() for pattern in list_all_patterns)
                    
                    # Only treat as CSV query if:
                    # 1. There's a current table OR a detected table
                    # 2. It's NOT a "list all" query
                    # 3. It contains CSV-specific keywords OR is a "show me data from" query
                    table_to_use = detected_table or st.session_state.current_table
                    if table_to_use and not is_list_all_query:
                        # Use smart pattern detection instead of hardcoded keywords
                        try:
                            from config_manager import SmartPatternMatcher
                            matcher = SmartPatternMatcher()
                            is_csv_query = matcher.detect_csv_query_intent(text, has_csv_tables=True)
                        except ImportError:
                            # Fallback: semantic pattern matching (no hardcoded keywords)
                            import re
                            # Dynamic pattern: data operations (semantic approach)
                            data_patterns = [
                                r'\b(show|display|list|get|find)\s+(me\s+)?(data|rows|columns|records)\b',
                                r'\b(query|select|filter|sort|count|sum|avg|max|min)\b',
                                r'\b(chart|graph|plot|visualize|analyze)\b',
                                r'\b(top|bottom|first|last)\s+\d+\b'
                            ]
                            is_csv_query = detected_table or any(re.search(pattern, text.lower()) for pattern in data_patterns)
                    
                    # Process with AI
                    with st.spinner("🤔 Processing..."):
                        try:
                            if is_csv_query and detected_table:
                                # Set as current table for future queries
                                st.session_state.current_table = detected_table
                                
                                # Special handling for "Show me data from [CSV file]" queries
                                # Query to get first 10 rows for preview
                                result = st.session_state.csv_query_engine.query(
                                    "show me first 10 rows", 
                                    detected_table,
                                    custom_limit=10
                                )
                                
                                if result.get("success"):
                                    data = result.get("data", [])
                                    row_count = result.get("row_count", len(data))
                                    
                                    # Store full data for later use
                                    full_result = st.session_state.csv_query_engine.query(
                                        "show me all data",
                                        detected_table,
                                        custom_limit=1000
                                    )
                                    
                                    # Create message with special flag for CSV file display
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": f"✅ Query executed successfully! Retrieved {row_count} rows.",
                                        "csv_file_display": True,
                                        "table_name": detected_table,
                                        "preview_data": data,
                                        "full_data": full_result.get("data", []) if full_result.get("success") else data,
                                        "row_count": row_count
                                    })
                                else:
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": f"❌ Query failed: {result.get('error', 'Unknown error')}"
                                    })
                            elif is_csv_query:
                                # Handle regular CSV query
                                result = st.session_state.csv_query_engine.query(text, table_to_use)
                                
                                if result.get("success"):
                                    data = result.get("data", [])
                                    row_count = result.get("row_count", len(data))
                                    
                                    response_text = f"✅ Query executed successfully! Retrieved {row_count:,} rows.\n\n"
                                    
                                    # Show data preview
                                    if data:
                                        df_preview = pd.DataFrame(data[:10])
                                        # Use to_string() instead of to_markdown() to avoid tabulate dependency
                                        response_text += f"**Data Preview (first 10 rows):**\n```\n{df_preview.to_string()}\n```"
                                    
                                    # Store for visualization
                                    viz_data = result
                                    
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": response_text,
                                        "viz_data": viz_data
                                    })
                                else:
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": f"❌ Query failed: {result.get('error', 'Unknown error')}"
                                    })
                            else:
                                # Regular AI query - pass session state so agent can access CSV tables
                                response = st.session_state.agent.process_query(text, session_state=st.session_state)
                                
                                if response.get("success"):
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": response.get("response", "No response")
                                    })
                                else:
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": f"❌ Error: {response.get('error', 'Unknown error')}"
                                    })
                        
                        except Exception as e:
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"❌ Error: {str(e)}"
                            })
                            logger.error(f"Query processing error: {e}", exc_info=True)
                    
                    st.rerun()
            
            except Exception as e:
                logger.error(f"Message parsing error: {e}")
    
    # ========================================================================
    # TAB 2: UPLOAD FILES (PDF, CSV, and Other Files)
    # ========================================================================
    with tab2:
        st.markdown("### 📤 Upload Files")
        st.markdown("Upload **PDFs** (AI analysis), **CSV files** (data analysis), or any files (Google Drive)")
        
        # Show last upload result
        if st.session_state.last_upload_result and st.session_state.upload_complete:
            if st.session_state.last_upload_result.get('success'):
                result = st.session_state.last_upload_result
                file_type = result.get('file_type', 'unknown')
                
                if file_type == 'pdf':
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ {result['message']}<br>
                        📊 Pages: {result.get('page_count', 'N/A')} | Chunks: {result.get('chunks_created', 'N/A')}<br>
                        💾 Size: {result.get('size', 0) / (1024*1024):.2f} MB
                    </div>
                    """, unsafe_allow_html=True)
                
                elif file_type == 'csv':
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ {result['message']}<br>
                        📊 Rows: {result.get('rows', 'N/A'):,} | Columns: {result.get('columns', 'N/A')}<br>
                        📋 Table: {result.get('table_name', 'N/A')}<br>
                        💾 Size: {result.get('size', 0) / (1024*1024):.2f} MB
                    </div>
                    """, unsafe_allow_html=True)
                
                else:
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ {result['message']}<br>
                        💾 Size: {result.get('size', 0) / (1024*1024):.2f} MB
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.error(f"❌ {st.session_state.last_upload_result.get('error')}")
            
            if st.button("✓ Clear Message", key="clear_msg"):
                st.session_state.last_upload_result = None
                st.session_state.upload_complete = False
                st.rerun()
        
        # File uploader - accepts all file types
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            accept_multiple_files=True,
            type=None,  # Accept all file types
            help="📄 PDFs: AI analysis | 📊 CSV: Data tables | 📁 Others: Google Drive"
        )
        
        if uploaded_files:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"📁 {len(uploaded_files)} file(s) selected")
                
                # Show file types
                file_types = {}
                for f in uploaded_files:
                    ftype = f.type or "unknown"
                    file_types[ftype] = file_types.get(ftype, 0) + 1
                
                type_str = ", ".join([f"{count} {ftype}" for ftype, count in file_types.items()])
                st.caption(f"Types: {type_str}")
            
            with col2:
                if st.button("🚀 Upload All", type="primary", use_container_width=True):
                    upload_status = st.empty()
                    upload_status.markdown('<div class="upload-progress">⏳ Uploading...</div>', unsafe_allow_html=True)
                    
                    progress_bar = st.progress(0)
                    success_count = 0
                    last_result = None
                    
                    for idx, file in enumerate(uploaded_files):
                        progress_bar.progress((idx) / len(uploaded_files))
                        result = handle_file_upload(file)
                        if result.get('success'):
                            success_count += 1
                            last_result = result
                    
                    progress_bar.progress(1.0)
                    
                    if success_count > 0:
                        st.session_state.last_upload_result = last_result
                        st.session_state.upload_complete = True
                    
                    time.sleep(1)
                    st.rerun()
    
    # ========================================================================
    # TAB 3: MY FILES (PDFs, CSVs, Notes) - WITH VALIDATION
    # ========================================================================
    with tab3:
        st.markdown("### 📂 My Files")
        
        col1, col2, col3 = st.columns(3)
        
        # Column 1: PDFs
        with col1:
            st.markdown("#### 📄 PDFs")
            if st.button("🔄 Refresh", key="refresh_pdfs"):
                st.rerun()
            
            try:
                pdfs = st.session_state.agent.rag_client.list_pdfs(limit=100)
                if pdfs.get('success') and pdfs.get('pdfs'):
                    st.info(f"📊 Total: {len(pdfs['pdfs'])} PDFs")
                    for pdf in pdfs['pdfs']:
                        st.markdown(f"""
                        <div class="pdf-card">
                            <strong>📄 {pdf.get('filename', 'Unknown')}</strong>
                            <span>Pages: {pdf.get('page_count', 0)} | Chunks: {pdf.get('chunks_count', 0)}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_pdf_{pdf.get('pdf_id')}"):
                            delete_pdf(pdf.get('pdf_id'), pdf.get('filename'))
                else:
                    st.info("📭 No PDFs uploaded yet")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        # Column 2: CSV Tables
        with col2:
            st.markdown("#### 📊 CSV Tables")
            if st.button("🔄 Refresh", key="refresh_csvs"):
                st.rerun()
            
            if st.session_state.csv_tables:
                st.info(f"📊 Total: {len(st.session_state.csv_tables)} tables")
                for table_name, info in st.session_state.csv_tables.items():
                    st.markdown(f"""
                    <div class="csv-card">
                        <strong>📊 {table_name}</strong>
                        <span>Rows: {info.get('rows', 0):,} | Cols: {info.get('columns', 0)}</span>
                        <span>File: {info.get('filename', 'N/A')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_csv_{table_name}"):
                        delete_csv_table(table_name)
            else:
                st.info("📭 No CSV tables yet")
        
        # Column 3: Notes - WITH VALIDATION
        with col3:
            st.markdown("#### 📝 Notes")
            
            col_a, col_b = st.columns([2, 1])
            with col_a:
                if st.button("🔄 Refresh", key="refresh_notes"):
                    st.rerun()
            with col_b:
                if st.button("🧹 Clean", key="clean_notes", help="Remove invalid entries", use_container_width=True):
                    with st.spinner("Cleaning..."):
                        cleanup = st.session_state.agent.db_client.cleanup_orphaned_entries()
                        if cleanup.get('success'):
                            orphaned = cleanup.get('orphaned_count', 0)
                            if orphaned > 0:
                                st.success(f"✅ Removed {orphaned} orphaned entries!")
                                time.sleep(2)
                            else:
                                st.info("✓ No orphaned entries found")
                                time.sleep(1)
                        st.rerun()
            
            try:
                # CRITICAL FIX: Use validate=True to filter orphaned entries
                notes = st.session_state.agent.db_client.list_documents(limit=100, validate=True)
                
                if notes.get('success') and notes.get('documents'):
                    valid_notes = notes['documents']
                    filtered_count = notes.get('filtered_count', 0)
                    
                    status_text = f"📊 Total: {len(valid_notes)} Notes"
                    if filtered_count > 0:
                        status_text += f" ({filtered_count} orphaned filtered)"
                    
                    st.info(status_text)
                    
                    if filtered_count > 0:
                        st.markdown(f"""
                        <div class="warning-box">
                            ⚠️ {filtered_count} orphaned entries hidden. Click 'Clean' to remove them.
                        </div>
                        """, unsafe_allow_html=True)
                    
                    for note in valid_notes:
                        content = note.get('content', '')
                        preview = content[:60] + "..." if len(content) > 60 else content
                        
                        doc_id = note.get('document_id')
                        title = note.get('title', 'Untitled')
                        
                        st.markdown(f"""
                        <div class="note-card">
                            <strong>📝 {title}</strong>
                            <span>{preview}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        delete_key = f"del_note_{doc_id}"
                        if st.button("🗑️", key=delete_key):
                            delete_note(doc_id, title)
                else:
                    st.info("📭 No notes created yet")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"Notes listing error: {e}", exc_info=True)
    
    # ========================================================================
    # TAB 4: CREATE NOTE
    # ========================================================================
    with tab4:
        st.markdown("### 📝 Create New Note")
        
        title = st.text_input("Title", placeholder="Enter note title...")
        content = st.text_area("Content", placeholder="Write your note content...", height=300)
        category = st.selectbox("Category", [
            "general", "work", "personal", "research", 
            "ideas", "meetings", "tasks", "budget", "code"
        ])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Note", type="primary", use_container_width=True):
                if title and content:
                    with st.spinner("💾 Saving..."):
                        result = save_to_database(title, content, category)
                        if result.get('success'):
                            st.success(f"✅ Note '{title}' saved successfully!")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed: {result.get('error')}")
                else:
                    st.warning("⚠️ Please provide both title and content!")
        
        with col2:
            if st.button("🗑️ Clear Form", use_container_width=True):
                st.rerun()
    
    # ========================================================================
    # TAB 5: BROWSE NOTES - WITH VALIDATION
    # ========================================================================
    with tab5:
        st.markdown("### 🔍 Search & Browse Notes")
        
        query = st.text_input("Search notes", placeholder="Enter keywords to search...")
        
        if st.button("🔍 Search", type="primary", use_container_width=True):
            if query:
                with st.spinner("🔍 Searching..."):
                    result = search_database(query, 20)
                    if result.get('success') and result.get('documents'):
                        valid_docs = [doc for doc in result['documents'] 
                                     if doc.get('document_id') and str(doc.get('document_id')).lower() != 'none']
                        
                        if valid_docs:
                            st.success(f"✅ Found {len(valid_docs)} matching notes!")
                            for idx, doc in enumerate(valid_docs, 1):
                                similarity = doc.get('similarity', 0.5)
                                relevance = int(similarity * 100)
                                
                                doc_id = doc.get('document_id')
                                
                                with st.expander(f"{idx}. {doc.get('title', 'Untitled')} ({relevance}% match)", expanded=(idx==1)):
                                    st.write(f"**Category:** {doc.get('category', 'general')}")
                                    st.write(f"**Relevance:** {relevance}%")
                                    st.write("**Content:**")
                                    st.write(doc.get('content', ''))
                                    
                                    if doc_id:
                                        delete_key = f"search_del_{doc_id}_{idx}"
                                        if st.button("🗑️ Delete", key=delete_key):
                                            delete_note(doc_id, doc.get('title', 'Untitled'))
                        else:
                            st.warning("💡 No valid matching notes found!")
                    else:
                        st.warning("💡 No matching notes found!")
                        st.info("**Tip:** Try different keywords or check spelling")
            else:
                st.warning("⚠️ Please enter a search query!")
    
    # Footer
    st.markdown("---")
    st.caption("**Sepia ML** | v5.1 Production | All Features + Validation")


if __name__ == "__main__":
    main()