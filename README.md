<!-- Centered Banner Image -->
<p align="center" style="background: linear-gradient(to bottom, #fdfdfd, #f2f2f2); padding: 20px; border-bottom: 3px solid #1F2421;">
  <img src="docs/assets/branding-overview.png" width="450" alt="Branding Overview" style="border-radius: 8px;" />
</p>

<h1 align="center" style="font-family: Arial; font-weight: bold; color: #006DFF; margin-top: 20px;">
  Self Labs Trading System v2.0
</h1>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License: MIT" />
  <img src="https://img.shields.io/badge/version-2.0-green" alt="Version 2.0" />
  <img src="https://img.shields.io/badge/status-alpha-orange" alt="Status: Alpha" />
</p>

---

<p align="center" style="font-family:Arial; color:#1F2421; font-size:16px; line-height:1.6; max-width:700px; margin: 0 auto;">
  <strong>Self Labs Trading System v2.0</strong> (formerly known as <em>HASS</em>) is a <strong>Highly Available, Scalable, and Sustainable</strong> platform for modern algorithmic trading.
  Through its <em>dynamic agent swarm architecture</em>, <em>NLP-driven orchestration</em>, and <em>robust data flows</em>, it adapts swiftly to changing market conditions—while remaining accessible to both novice and expert traders.
</p>

---

## 🌟 Key Highlights

<div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; margin-top: 20px;">
  <div style="flex: 1; min-width: 250px; background: #F2BB05; padding: 15px; border-radius: 8px;">
    <h3 style="font-family: Arial; color: #1F2421; margin-top: 0;">Dynamic Agent Swarm</h3>
    <ul style="font-family: Arial; color: #1F2421;">
      <li>Agents specialize in Market Data, Media Analysis, Pattern Recognition, Risk Management, and Execution.</li>
      <li>Automatic scaling ensures resilience and real-time performance.</li>
    </ul>
  </div>
  <div style="flex: 1; min-width: 250px; background: #006DFF; padding: 15px; border-radius: 8px;">
    <h3 style="font-family: Arial; color: #FFFFFF; margin-top: 0;">NLP-Driven Orchestration</h3>
    <ul style="font-family: Arial; color: #FFFFFF;">
      <li>Use simple text commands to spawn or retire agents.</li>
      <li>Facilitates dynamic strategy changes without heavy coding.</li>
    </ul>
  </div>
</div>

<div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; margin-top: 20px;">
  <div style="flex: 1; min-width: 250px; background: #1F2421; padding: 15px; border-radius: 8px;">
    <h3 style="font-family: Arial; color: #F2BB05; margin-top: 0;">Scalable Architecture</h3>
    <ul style="font-family: Arial; color: #FFFFFF;">
      <li>Built on Kubernetes, Docker, Kafka, ClickHouse, and Redis.</li>
      <li>Ensures high throughput and low latency under peak loads.</li>
    </ul>
  </div>
  <div style="flex: 1; min-width: 250px; background: #C9C9C1; padding: 15px; border-radius: 8px;">
    <h3 style="font-family: Arial; color: #1F2421; margin-top: 0;">User-Friendly</h3>
    <ul style="font-family: Arial; color: #1F2421;">
      <li>Works for non-technical traders, while still meeting professional demands.</li>
      <li>Visual dashboards and straightforward NLP commands simplify adoption.</li>
    </ul>
  </div>
</div>

---

## 🎨 Branding & Aesthetics

<p style="font-family:Arial; color:#1F2421; line-height:1.6;">
  Self Labs believes in a clean, modern aesthetic that balances <strong>trust and innovation</strong>. Our signature palette:
</p>

- **Primary Blue (#006DFF):** Tech-forward, innovative vibes.  
- **Gold Yellow (#F2BB05):** Conveys optimism, market growth, and energy.  
- **Rich Black (#1F2421):** Stability and authority for essential UI elements.  
- **Neutral Gray (#C9C9C1):** Subtle contrast for secondary content.  
- **White (#FFFFFF):** Clear, open space for UI legibility.

---

## 🏗️ Architecture Overview

<details>
<summary style="font-weight:bold; color:#006DFF; cursor:pointer;">Click to Expand Technical Layout</summary>

**Core Backend:**
- **Language:** Python 3.11+  
- **Framework:** FastAPI  
- **Messaging:** Apache Kafka  
- **Datastores:** MongoDB, ClickHouse, Redis

**Containerization & Orchestration:**
- **Containers:** Docker  
- **Orchestrator:** Kubernetes  
- **Communication:** gRPC + NLP threads

**Agents:**
- **Market Data** – Gathers real-time/historical quotes.  
- **Media Analysis** – Parses news, social media sentiment.  
- **Pattern Recognition** – Identifies technical signals and patterns.  
- **Risk Management** – Monitors portfolio exposure, applies failsafes.  
- **Execution** – Places and monitors orders, integrating with broker APIs.

</details>

---

## 📜 Documentation & Versioning

- **Quick-Start Guides (`docs/quick-start/`):**  
  Rapid introductions for new users.  
- **Standard Documentation (`docs/standard/`):**  
  Detailed references, advanced tutorials, best practices.  
- **CHANGELOG & PROGRESS:**  
  - **`CHANGELOG.md`** – Tracks significant changes, version tags, and commit references.  
  - **`PROGRESS.md`** – Logs incremental development milestones and demos.

NLP usage, agent scaling instructions, and deeper system design references can be found in `docs/using-changelog.md` and the `standard` docs set.

---

## 🎥 Video Demos & Iterations

- **Short Demo Clips (2-3 min):** Show quick UI updates or minor feature additions.  
- **In-Depth Walkthroughs (5-10 min):** Cover major milestones—like new agent integrations, NLP upgrades, or multi-symbol analytics.

Users—including Will Sargent and other stakeholders—can watch these demos to provide feedback, ensuring the system’s roadmap aligns with real-world trading needs.

---

## 🚀 What the System Is Doing

1. **Coordinating Agents:**  
   A “swarm intelligence” approach means specialized agents work in sync, exchanging insights, reacting to market signals, and automatically adjusting resource usage.

2. **Natural Language Interaction:**  
   Traders or support staff can say, “Activate two more Market Data agents for AAPL and TSLA,” and watch the system dynamically allocate containers in seconds—no coding required.

3. **Adaptive Scaling & Data-Driven Insights:**  
   Each agent ingests real-time data, identifies actionable signals, and outputs them to a visual dashboard or via NLP prompts. Powered by Kafka and Kubernetes, the platform handles burst traffic and rapid data spikes effortlessly.

---

## 🛣️ Roadmap & Next Steps

**Immediate Focus:**
- A “vertical slice” MVP covering one agent for each major function (Market Data, Execution, etc.), enabling a minimal end-to-end trading demo.

**Mid-Term Objectives:**
- Integrate robust backtesting (e.g., via QuantConnect Lean).  
- Expand NLP to handle advanced commands (timeframe, multi-symbol, varied strategies).

**Long-Term Vision:**
- Patent or protect unique agent-swarm orchestration if it proves commercially differentiating.  
- Offer multi-tenant capabilities for broader commercial usage.  
- Enhance UI aesthetics and real-time analytics to maintain a competitive edge.

---

## 🤝 Acknowledgments & Vision

<p style="font-family:Arial; color:#1F2421; line-height:1.5; margin:20px 0;">
  <strong>Built by Self Labs</strong>, this trading system merges data-driven insights, NLP-driven orchestration, and advanced microservice patterns to make algo-trading more accessible, powerful, and responsive than ever.
</p>

> **“Rooted in Data, Thriving in Markets.”**  
> **“Core MØSS: Where Intelligence Meets Growth.”**  
> **“Trading Evolved. Precision Delivered.”**

<p align="center" style="font-family:Arial; color:#1F2421;">
  <strong>© 2024 Self Labs - MIT Licensed</strong>
</p>

---

<sup><sub>*This README blends visual enhancements, structured sections, and consistent branding, reflecting Self Labs’ vision for a world-class trading orchestration platform.*</sub></sup>
