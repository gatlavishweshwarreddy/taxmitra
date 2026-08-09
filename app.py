import vertexai
from vertexai.generative_models import GenerativeModel
from flask import Flask, request, jsonify, render_template_string
import os
from datetime import datetime
import razorpay
from google.cloud import firestore
db = firestore.Client(project='taxmitra-504906', database='(default)')

app = Flask(__name__)
razorpay_client = razorpay.Client(auth=(
    os.environ.get("RAZORPAY_KEY_ID"),
    os.environ.get("RAZORPAY_KEY_SECRET")
))

vertexai.init(project='taxmitra-504906', location='us-central1')
model = GenerativeModel('gemini-2.5-flash')

logs = []

SYSTEM_PROMPT = """You are TaxMitra, an expert AI Chartered Accountant assistant for Indian small businesses.
You help with:
- GST filing, registration, and queries
- Income Tax Return (ITR) filing
- TDS calculations and compliance
- Business expense categorization
- Tax saving strategies
- Compliance deadlines and reminders
- Interpreting tax notices

Always respond in BOTH English AND Hindi. First give the answer in English, then repeat the key points in Hindi below it. This helps users understand better.
Be specific, practical, and actionable. Always mention relevant section numbers and deadlines.
Format your response with clear bullet points and sections."""

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>TaxMitra - AI CA Assistant for Indian Businesses</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --accent: #f59e0b;
            --green: #10b981;
            --bg: #030712;
            --bg2: #0f172a;
            --bg3: #1e293b;
            --text: #f8fafc;
            --text2: #94a3b8;
            --text3: #475569;
            --border: rgba(255,255,255,0.08);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); overflow-x: hidden; }

        /* Animated background */
        body::before {
            content: '';
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: 
                radial-gradient(ellipse at 20% 20%, rgba(99,102,241,0.12) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(139,92,246,0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(16,185,129,0.04) 0%, transparent 70%);
            pointer-events: none; z-index: 0;
        }

        /* NAV */
        nav {
            position: sticky; top: 0; z-index: 1000;
            padding: 16px 40px;
            display: flex; align-items: center; justify-content: space-between;
            background: rgba(3,7,18,0.85);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
        }
        .nav-logo { display: flex; align-items: center; gap: 12px; }
        .nav-logo-icon {
            width: 42px; height: 42px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.3em; box-shadow: 0 0 20px rgba(99,102,241,0.4);
        }
        .nav-logo h1 {
            font-size: 1.4em; font-weight: 800;
            background: linear-gradient(135deg, #fff, #a78bfa);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .nav-logo span { font-size: 0.7em; color: var(--text2); display: block; margin-top: -2px; }
        .nav-right { display: flex; align-items: center; gap: 16px; }
        .nav-badge {
            background: rgba(16,185,129,0.15);
            border: 1px solid rgba(16,185,129,0.3);
            color: var(--green); padding: 6px 14px;
            border-radius: 20px; font-size: 0.78em; font-weight: 600;
            display: flex; align-items: center; gap: 6px;
        }
        .live-dot { width: 6px; height: 6px; background: var(--green); border-radius: 50%; animation: livepulse 1.5s infinite; }
        @keyframes livepulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.3)} }
        .nav-cta {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white; border: none; padding: 10px 20px;
            border-radius: 10px; cursor: pointer; font-weight: 700;
            font-family: 'Inter', sans-serif; font-size: 0.85em;
            transition: all 0.2s;
        }
        .nav-cta:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(99,102,241,0.5); }

        /* HERO */
        .hero {
            position: relative; z-index: 1;
            text-align: center; padding: 80px 20px 60px;
        }
        .hero-pill {
            display: inline-flex; align-items: center; gap: 8px;
            background: rgba(99,102,241,0.15);
            border: 1px solid rgba(99,102,241,0.35);
            padding: 8px 20px; border-radius: 30px;
            font-size: 0.82em; color: #a78bfa; margin-bottom: 28px;
            animation: fadeInDown 0.6s ease;
        }
        .hero-pill-dot { width: 6px; height: 6px; background: var(--primary); border-radius: 50%; }
        .hero h2 {
            font-size: 4em; font-weight: 900; line-height: 1.1;
            margin-bottom: 20px;
            animation: fadeInUp 0.7s ease;
        }
        .hero h2 .line1 { display: block; color: #fff; }
        .hero h2 .line2 {
            display: block;
            background: linear-gradient(135deg, var(--primary), var(--secondary), #ec4899);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .hero-sub {
            font-size: 1.15em; color: var(--text2);
            max-width: 520px; margin: 0 auto 40px;
            line-height: 1.7; animation: fadeInUp 0.8s ease;
        }
        .hero-sub strong { color: #fff; }

        /* Stats bar */
        .stats-bar {
            display: flex; justify-content: center;
            gap: 0; margin-bottom: 50px;
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            border-radius: 16px; overflow: hidden;
            max-width: 600px; margin: 0 auto 50px;
            animation: fadeInUp 0.9s ease;
        }
        .stat-item {
            flex: 1; padding: 20px;
            border-right: 1px solid var(--border);
            text-align: center;
        }
        .stat-item:last-child { border-right: none; }
        .stat-num { font-size: 1.9em; font-weight: 800; color: var(--primary); }
        .stat-label { font-size: 0.72em; color: var(--text3); margin-top: 2px; }

        /* Trust badges */
        .trust-badges {
            display: flex; justify-content: center;
            gap: 12px; flex-wrap: wrap; margin-bottom: 50px;
        }
        .trust-badge {
            display: flex; align-items: center; gap: 6px;
            background: rgba(255,255,255,0.04);
            border: 1px solid var(--border);
            padding: 8px 16px; border-radius: 10px;
            font-size: 0.8em; color: var(--text2);
        }
        .trust-badge span { font-size: 1.1em; }

        /* MAIN */
        .main { max-width: 920px; margin: 0 auto; padding: 0 20px 80px; position: relative; z-index: 1; }

        /* Section label */
        .section-label {
            font-size: 0.72em; font-weight: 700;
            color: var(--text3); text-transform: uppercase;
            letter-spacing: 1.5px; margin-bottom: 12px;
        }

        /* Quick questions */
        .quick-wrap { margin-bottom: 24px; }
        .quick-btns { display: flex; flex-wrap: wrap; gap: 8px; }
        .quick-btn {
            background: rgba(99,102,241,0.08);
            border: 1px solid rgba(99,102,241,0.25);
            color: #a78bfa; padding: 9px 18px;
            border-radius: 25px; cursor: pointer;
            font-size: 0.83em; font-weight: 500;
            font-family: 'Inter', sans-serif;
            transition: all 0.2s;
        }
        .quick-btn:hover {
            background: rgba(99,102,241,0.25);
            border-color: var(--primary); color: #fff;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(99,102,241,0.3);
        }

        /* Chat */
        .chat-card {
            background: rgba(15,23,42,0.8);
            border: 1px solid var(--border);
            border-radius: 24px; overflow: hidden;
            margin-bottom: 24px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
        }
        .chat-topbar {
            padding: 16px 24px;
            background: rgba(99,102,241,0.08);
            border-bottom: 1px solid var(--border);
            display: flex; align-items: center; justify-content: space-between;
        }
        .chat-topbar-left { display: flex; align-items: center; gap: 10px; }
        .ai-avatar {
            width: 32px; height: 32px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.9em;
        }
        .chat-topbar-info h4 { font-size: 0.88em; font-weight: 600; }
        .chat-topbar-info p { font-size: 0.72em; color: var(--green); }
        .model-badge {
            background: rgba(99,102,241,0.15);
            border: 1px solid rgba(99,102,241,0.3);
            color: #a78bfa; padding: 4px 10px;
            border-radius: 8px; font-size: 0.72em; font-weight: 600;
        }
        .chat-messages {
            padding: 24px; min-height: 380px; max-height: 420px;
            overflow-y: auto; display: flex; flex-direction: column; gap: 14px;
        }
        .chat-messages::-webkit-scrollbar { width: 3px; }
        .chat-messages::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.3); border-radius: 2px; }
        .msg { display: flex; gap: 10px; align-items: flex-start; }
        .msg.user { flex-direction: row-reverse; }
        .msg-avatar {
            width: 30px; height: 30px; border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.85em; flex-shrink: 0;
        }
        .msg-avatar.ai { background: linear-gradient(135deg, var(--primary), var(--secondary)); }
        .msg-avatar.human { background: rgba(255,255,255,0.1); }
        .msg-bubble {
            max-width: 75%; padding: 13px 17px;
            border-radius: 16px; font-size: 0.88em; line-height: 1.65;
        }
        .msg.ai .msg-bubble {
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--border);
            color: #e2e8f0; border-top-left-radius: 4px;
        }
        .msg.user .msg-bubble {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white; border-top-right-radius: 4px;
        }
        .msg-time { font-size: 0.68em; color: var(--text3); margin-top: 4px; }
        .loading-dots { display: flex; gap: 4px; align-items: center; padding: 4px 0; }
        .loading-dots span {
            width: 7px; height: 7px; background: var(--primary);
            border-radius: 50%; animation: bounce 1.4s infinite ease-in-out;
        }
        .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
        .loading-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%,80%,100%{transform:scale(0.6);opacity:0.4} 40%{transform:scale(1);opacity:1} }
        .chat-input-bar {
            padding: 16px 20px;
            background: rgba(255,255,255,0.02);
            border-top: 1px solid var(--border);
            display: flex; gap: 10px; align-items: center;
        }
        .chat-input {
            flex: 1; padding: 13px 18px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 14px; color: #fff;
            font-size: 0.88em; font-family: 'Inter', sans-serif;
            outline: none; transition: all 0.2s;
        }
        .chat-input:focus { border-color: var(--primary); background: rgba(99,102,241,0.08); }
        .chat-input::placeholder { color: var(--text3); }
        .send-btn {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white; border: none; padding: 13px 22px;
            border-radius: 14px; cursor: pointer; font-weight: 700;
            font-family: 'Inter', sans-serif; font-size: 0.88em;
            transition: all 0.2s; white-space: nowrap;
        }
        .send-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(99,102,241,0.5); }

        /* Features */
        .features { margin: 50px 0; }
        .features h2 { text-align: center; font-size: 1.8em; font-weight: 800; margin-bottom: 8px; }
        .features > p { text-align: center; color: var(--text2); margin-bottom: 30px; }
        .features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
        .feature-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            border-radius: 16px; padding: 24px;
            transition: all 0.3s;
        }
        .feature-card:hover { border-color: rgba(99,102,241,0.4); transform: translateY(-3px); background: rgba(99,102,241,0.05); }
        .feature-icon { font-size: 1.8em; margin-bottom: 12px; }
        .feature-card h4 { font-size: 0.95em; font-weight: 700; margin-bottom: 6px; }
        .feature-card p { font-size: 0.8em; color: var(--text2); line-height: 1.6; }

        /* Pricing */
        .pricing { margin: 50px 0; }
        .pricing h2 { text-align: center; font-size: 1.8em; font-weight: 800; margin-bottom: 8px; }
        .pricing > p { text-align: center; color: var(--text2); margin-bottom: 30px; }
        .pricing-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .plan-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            border-radius: 20px; padding: 32px;
            transition: all 0.3s; position: relative; overflow: hidden;
        }
        .plan-card::before {
            content: ''; position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            opacity: 0; transition: opacity 0.3s;
        }
        .plan-card:hover { border-color: rgba(99,102,241,0.4); transform: translateY(-4px); }
        .plan-card:hover::before { opacity: 1; }
        .plan-card.featured {
            background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.08));
            border-color: rgba(99,102,241,0.4);
        }
        .plan-card.featured::before { opacity: 1; }
        .plan-badge {
            display: inline-block;
            background: linear-gradient(135deg, var(--accent), #f97316);
            color: white; padding: 4px 12px;
            border-radius: 20px; font-size: 0.72em;
            font-weight: 700; margin-bottom: 16px;
        }
        .plan-name { font-size: 0.9em; color: var(--text2); margin-bottom: 8px; }
        .plan-price { font-size: 3.2em; font-weight: 900; color: #fff; line-height: 1; }
        .plan-period { font-size: 0.8em; color: var(--text3); margin-bottom: 24px; margin-top: 4px; }
        .plan-features { list-style: none; margin-bottom: 28px; }
        .plan-features li {
            padding: 7px 0; font-size: 0.85em; color: var(--text2);
            display: flex; align-items: center; gap: 8px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }
        .plan-features li:last-child { border-bottom: none; }
        .check { color: var(--green); font-weight: 700; }
        .plan-btn {
            width: 100%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white; border: none; padding: 15px;
            border-radius: 14px; cursor: pointer; font-weight: 700;
            font-family: 'Inter', sans-serif; font-size: 0.95em;
            transition: all 0.2s;
        }
        .plan-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(99,102,241,0.5); }

        /* Footer */
        footer {
            text-align: center; padding: 40px 20px;
            border-top: 1px solid var(--border);
            color: var(--text3); font-size: 0.82em;
            position: relative; z-index: 1;
        }
        footer strong { color: var(--text2); }

        /* Animations */
        @keyframes fadeInDown { from{opacity:0;transform:translateY(-15px)} to{opacity:1;transform:translateY(0)} }
        @keyframes fadeInUp { from{opacity:0;transform:translateY(15px)} to{opacity:1;transform:translateY(0)} }

        @media(max-width:700px) {
            .hero h2 { font-size: 2.4em; }
            .features-grid { grid-template-columns: 1fr; }
            .pricing-grid { grid-template-columns: 1fr; }
            nav { padding: 14px 20px; }
            .nav-right .nav-cta { display: none; }
        }
    </style>
</head>
<body>

<nav>
    <div class="nav-logo">
        <div class="nav-logo-icon">🏦</div>
        <div>
            <h1>TaxMitra</h1>
            <span>AI CA Assistant</span>
        </div>
    </div>
    <div class="nav-right">
        <div class="nav-badge"><div class="live-dot"></div> AI Online</div>
        <button class="nav-cta" onclick="document.getElementById('chatBox').scrollIntoView({behavior:'smooth'})">Try Free ➤</button>
    </div>
</nav>

<div class="hero">
    <div class="hero-pill"><div class="hero-pill-dot"></div> Powered by Google Gemini AI • Built for Bharat</div>
    <h2>
        <span class="line1">Apna CA ab hai</span>
        <span class="line2">24/7 Available</span>
    </h2>
    <p class="hero-sub">
        GST • ITR • TDS • Compliance — <strong>instantly answered</strong> in Hindi or English.<br>
        No appointments. No waiting. No ₹10,000 CA bills.
    </p>
    <div class="stats-bar">
        <div class="stat-item"><div class="stat-num">63M+</div><div class="stat-label">Small Businesses</div></div>
        <div class="stat-item"><div class="stat-num">₹99</div><div class="stat-label">Early Access</div></div>
        <div class="stat-item"><div class="stat-num">24/7</div><div class="stat-label">Always On</div></div>
        <div class="stat-item"><div class="stat-num" id="queryCount">0</div><div class="stat-label">Queries Answered</div></div>
    </div>
    <div class="trust-badges">
        <div class="trust-badge"><span>🔒</span> Secure & Private</div>
        <div class="trust-badge"><span>🇮🇳</span> Made for India</div>
        <div class="trust-badge"><span>⚡</span> Instant Answers</div>
        <div class="trust-badge"><span>🤖</span> Gemini AI Powered</div>
        <div class="trust-badge"><span>💬</span> Hindi & English</div>
    </div>
</div>

<div class="main">
    <div class="quick-wrap">
        <div class="section-label">Try asking</div>
        <div class="quick-btns">
            <button class="quick-btn" onclick="askQuestion('GST registration kaise karein?')">📋 GST Registration</button>
            <button class="quick-btn" onclick="askQuestion('ITR filing deadline kab hai 2024-25?')">📅 ITR Deadline</button>
            <button class="quick-btn" onclick="askQuestion('TDS kya hota hai aur kab katna chahiye?')">💰 TDS Help</button>
            <button class="quick-btn" onclick="askQuestion('Small business ke liye best tax saving tips?')">💡 Tax Saving</button>
            <button class="quick-btn" onclick="askQuestion('GST return late filing penalty kya hai?')">⚠️ GST Penalty</button>
            <button class="quick-btn" onclick="askQuestion('Section 44AD presumptive taxation kya hai?')">📖 Section 44AD</button>
            <button class="quick-btn" onclick="askQuestion('New tax regime vs old tax regime kaunsa better hai?')">⚖️ New vs Old Regime</button>
            <button class="quick-btn" onclick="askQuestion('GST invoice kaise banate hain?')">🧾 GST Invoice</button>
        </div>
    </div>

    <div class="chat-card">
        <div class="chat-topbar">
            <div class="chat-topbar-left">
                <div class="ai-avatar">🤖</div>
                <div class="chat-topbar-info">
                    <h4>TaxMitra AI Agent</h4>
                    <p>● Online — Responding instantly</p>
                </div>
            </div>
            <div class="model-badge">Gemini 2.5 Flash</div>
        </div>
        <div class="chat-messages" id="chatBox">
            <div class="msg ai">
                <div class="msg-avatar ai">🤖</div>
                <div>
                    <div class="msg-bubble">
                        🙏 <strong>Namaste!</strong> Main TaxMitra hoon — aapka personal AI CA assistant.<br><br>
                        Main aapki help kar sakta hoon:<br>
                        • <strong>GST</strong> — Registration, Filing, Notices, Returns<br>
                        • <strong>ITR</strong> — Filing, Tax Planning, Refunds<br>
                        • <strong>TDS</strong> — Calculation, Deduction, Compliance<br>
                        • <strong>Tax Saving</strong> — 80C, 80D, HRA, Business Expenses<br>
                        • <strong>Compliance</strong> — Deadlines, Penalties, Notices<br><br>
                        Apna sawaal Hindi ya English mein poochein! 😊
                    </div>
                    <div class="msg-time">TaxMitra AI • Just now</div>
                </div>
            </div>
        </div>
        <div class="chat-input-bar">
            <input class="chat-input" type="text" id="userInput" 
                placeholder="Apna tax sawaal yahan likhein... (Hindi/English)" 
                onkeypress="if(event.key==='Enter') sendMessage()">
            <button class="send-btn" onclick="sendMessage()">Send ➤</button>
        </div>
    </div>

    <div class="features">
        <div class="section-label" style="text-align:center">Why TaxMitra</div>
        <h2>Everything a CA does,<br>at 1% of the cost</h2>
        <p>Unlike ChatGPT or Gemini — TaxMitra is specialized for Indian tax law with exact section numbers, Hindi & English support, and India-specific deadlines. Starting with India's 63M small businesses, India first. Global next. 🌍</p>
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h4>GST Filing & Compliance</h4>
                <p>GSTR-1, GSTR-3B, annual returns — get step-by-step guidance instantly</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📝</div>
                <h4>ITR Filing Help</h4>
                <p>ITR-1 to ITR-4, tax calculation, deductions — all explained simply</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💸</div>
                <h4>TDS Management</h4>
                <p>Know when to deduct, how much, and how to file TDS returns correctly</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🛡️</div>
                <h4>Notice Handling</h4>
                <p>Got a tax notice? TaxMitra helps you understand and draft replies</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💡</div>
                <h4>Tax Saving Strategies</h4>
                <p>80C, 80D, HRA, business expenses — maximize your savings legally</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔔</div>
                <h4>Compliance Calendar</h4>
                <p>Never miss a deadline — GST, TDS, ITR, advance tax dates always ready</p>
            </div>
        </div>
    </div>

    <div class="pricing">
        <div class="section-label" style="text-align:center">Pricing</div>
        <h2>Simple, Honest Pricing</h2>
        <p>CA charges ₹5,000–₹20,000/month. TaxMitra early access starts at just ₹99 one-time.
        <div class="pricing-grid">
            <div class="plan-card">
                <div class="plan-name">Early Access</div>
                <div class="plan-price">₹99</div>
                <div class="plan-period">one-time payment • limited beta</div>
                <ul class="plan-features">
                    <li><span class="check">✓</span> Unlimited tax queries</li>
                    <li><span class="check">✓</span> GST filing guidance</li>
                    <li><span class="check">✓</span> ITR help</li>
                    <li><span class="check">✓</span> TDS calculations</li>
                    <li><span class="check">✓</span> Hindi & English support</li>
                    <li><span class="check">✓</span> 24/7 availability</li>
                </ul>
                <button class="plan-btn" onclick="subscribe('monthly')">Get Early Access</button>
            </div>
            <div class="plan-card featured">
                <div class="plan-badge">🔥 BEST VALUE</div>
                <div class="plan-name">Early Access Pro</div>
                <div class="plan-price">₹299</div>
                <div class="plan-period">one-time payment • full beta access</div>
                <ul class="plan-features">
                    <li><span class="check">✓</span> Everything in Monthly</li>
                    <li><span class="check">✓</span> Priority AI responses</li>
                    <li><span class="check">✓</span> Document analysis</li>
                    <li><span class="check">✓</span> Notice drafting help</li>
                    <li><span class="check">✓</span> Compliance calendar</li>
                    <li><span class="check">✓</span> Dedicated support</li>
                </ul>
                <button class="plan-btn" onclick="subscribe('annual')">Get Pro Access</button>
            </div>
        </div>
    </div>
</div>

<div class="testimonials" style="margin: 50px 0;">
    <div class="section-label" style="text-align:center">What Users Say</div>
    <h2 style="text-align:center;font-size:1.8em;font-weight:800;margin-bottom:8px;">Trusted by Small Business Owners</h2>
    <p style="text-align:center;color:var(--text2);margin-bottom:30px;">Real feedback from real businesses across India</p>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;">
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:24px;">
            <div style="color:#f59e0b;margin-bottom:12px;">★★★★★</div>
            <p style="color:#e2e8f0;font-size:0.88em;line-height:1.6;margin-bottom:16px;">"GST filing mein bahut help mili. CA se zyada fast aur sasta hai. Highly recommend!"</p>
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:36px;height:36px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;">R</div>
                <div><div style="font-size:0.85em;font-weight:600;">Ramesh Kumar</div><div style="font-size:0.72em;color:#64748b;">Kirana Store Owner, Delhi</div></div>
            </div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:24px;">
            <div style="color:#f59e0b;margin-bottom:12px;">★★★★★</div>
            <p style="color:#e2e8f0;font-size:0.88em;line-height:1.6;margin-bottom:16px;">"ITR filing ke baare mein sab kuch explain kar diya. Hindi mein samajhna bahut aasan tha!"</p>
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:36px;height:36px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;">P</div>
                <div><div style="font-size:0.85em;font-weight:600;">Priya Sharma</div><div style="font-size:0.72em;color:#64748b;">Freelance Designer, Mumbai</div></div>
            </div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:24px;">
            <div style="color:#f59e0b;margin-bottom:12px;">★★★★★</div>
            <p style="color:#e2e8f0;font-size:0.88em;line-height:1.6;margin-bottom:16px;">"TDS calculation aur GST notice ka reply — sab TaxMitra ne kar diya. Paise vasool!"</p>
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:36px;height:36px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;">S</div>
                <div><div style="font-size:0.85em;font-weight:600;">Suresh Patel</div><div style="font-size:0.72em;color:#64748b;">Textile Trader, Surat</div></div>
            </div>
        </div>
    </div>
</div>

<footer>
    <strong>TaxMitra Beta</strong> — AI-Powered CA Assistant for Indian Small Businesses<br>
    Early access program • Limited time offering • One-time payment<br>
    Powered by Google Gemini AI • Built with ❤️ for Bharat<br><br>
    <span style="color:#374151">Disclaimer: TaxMitra provides AI-generated guidance for informational purposes. Consult a qualified CA for complex matters.</span>
</footer>

<script>
    function askQuestion(q) {
    document.getElementById('userInput').value = q;
    sendMessage();
  }

    function subscribe(plan) {
    const amount = plan === 'annual' ? 29900 : 9900;
    fetch('/config')
    .then(r => r.json())
    .then(config => {
        fetch('/create-order', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({amount: amount})
        })
        .then(r => r.json())
        .then(order => {
            const options = {
                key: config.razorpay_key,
                amount: order.amount,
                currency: 'INR',
                name: 'TaxMitra',
                description: plan === 'annual' ? 'Early Access Pro' : 'Early Access',
                order_id: order.id,
                handler: function(response) {
                    fetch('/verify-payment', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(response)
                    })
                    .then(r => r.json())
                    .then(data => {
                        if(data.status === 'success') {
                            alert('Payment successful! Welcome to TaxMitra!');
                        }
                    });
                },
                prefill: {name: '', email: '', contact: ''},
                theme: {color: '#6366f1'}
            };
            const rzp = new Razorpay(options);
            rzp.open();
        });
    });
}

    function getTime() {
        return new Date().toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit'});
    }

    async function sendMessage() {
    const input = document.getElementById('userInput');
    const chatBox = document.getElementById('chatBox');
    const message = input.value.trim();
    if (!message) return;

    let questionCount = parseInt(localStorage.getItem('questionCount') || '0');
    if (questionCount >= 5) {
        chatBox.innerHTML += '<div class="msg ai"><div class="msg-avatar ai">🤖</div><div><div class="msg-bubble">You have used your 5 free questions! 🎉<br><br>To continue, please subscribe below — just ₹99 one-time!</div><div class="msg-time">TaxMitra AI • ' + getTime() + '</div></div></div>';
        chatBox.scrollTop = chatBox.scrollHeight;
        return;
    }
    localStorage.setItem('questionCount', questionCount + 1);

    chatBox.innerHTML += '<div class="msg user"><div class="msg-avatar human">👤</div><div><div class="msg-bubble">' + message + '</div><div class="msg-time">You • ' + getTime() + '</div></div></div>';
    input.value = '';
    chatBox.innerHTML += '<div class="msg ai" id="loading"><div class="msg-avatar ai">🤖</div><div><div class="msg-bubble"><div class="loading-dots"><span></span><span></span><span></span></div></div></div></div>';
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: message})
        });
        const data = await response.json();
        document.getElementById('loading').remove();
        const formatted = data.response.split('\n').join('<br>');
        chatBox.innerHTML += '<div class="msg ai"><div class="msg-avatar ai">🤖</div><div><div class="msg-bubble">' + formatted + '</div><div class="msg-time">TaxMitra AI • ' + getTime() + '</div></div></div>';
    } catch(e) {
        document.getElementById('loading').remove();
        chatBox.innerHTML += '<div class="msg ai"><div class="msg-avatar ai">🤖</div><div><div class="msg-bubble">Sorry, kuch error hua. Please try again.</div></div></div>';
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Update query counter
fetch('/logs').then(r=>r.json()).then(data=>{
    document.getElementById('queryCount').textContent = data.total_interactions + '+';
});

</script>
</body>
</html>"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user_message,
        "agent": "gemini-1.5-flash"
    }
    try:
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\nUser: {user_message}")
        bot_response = response.text
        log_entry["response"] = bot_response
        log_entry["status"] = "success"
    except Exception as e:
        print(f"ERROR: {str(e)}")
        bot_response = "Maafi chahta hoon, abhi kuch technical problem hai. Please thodi der baad try karein."
        log_entry["status"] = "error"
        log_entry["error"] = str(e)
    logs.append(log_entry)
    try:
       db.collection('interactions').add(log_entry)
    except:
       pass
    return jsonify({"response": bot_response})

@app.route('/logs')
def get_logs():
    try:
        docs = db.collection('interactions').get()
        all_logs = [doc.to_dict() for doc in docs]
        return jsonify({"total_interactions": len(all_logs), "logs": all_logs})
    except:
        return jsonify({"total_interactions": len(logs), "logs": logs})

@app.route('/config')
def config():
    return jsonify({"razorpay_key": os.environ.get("RAZORPAY_KEY_ID")})

@app.route('/health')
def health():
    return jsonify({"status": "running", "product": "TaxMitra", "version": "1.0"})

@app.route('/create-order', methods=['POST'])
def create_order():
    data = request.json
    amount = data.get('amount', 29900)  # ₹299 in paise
    order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })
    return jsonify(order)

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    data = request.json
    try:
        razorpay_client.utility.verify_payment_signature(data)
        return jsonify({"status": "success", "message": "Payment verified!"})
    except:
        return jsonify({"status": "failed", "message": "Payment verification failed"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
