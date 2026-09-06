# 🤖 Natural Language CLI - Complete Guide

## 🚀 Quick Start

Start the natural language interface:
```bash
python sentinelai.py natural-cli
```

You'll see an interactive prompt where you can type commands in plain English!

---

## 💬 Example Commands

### Security Scanning
```
You> scan localhost quickly
You> fast scan on 127.0.0.1
You> aggressive scan google.com
You> scan 192.168.1.1 with full analysis
```

### System Information
```
You> show network info
You> network information
You> display network details
```

### Report Generation
```
You> generate a report
You> report as json
You> export csv report
You> create security report
```

### Analysis
```
You> analyze the scan results
You> ai analysis of security findings
```

### Help & Navigation
```
You> help
You> ?
You> exit
You> quit
```

---

## 🎯 How It Works

### Step 1: You Type in English
```
You> scan localhost quickly
```

### Step 2: AI Understands Intent
```
Parsing: "scan localhost quickly"
↓
Intent: {
  "action": "scan",
  "target": "127.0.0.1",
  "scan_type": "fast",
  "confidence": 0.95
}
```

### Step 3: System Executes Command
```
🔍 Scanning 127.0.0.1 (fast mode - ~30 seconds)...
[*] Using arguments: -p 22,80,443,3306,5432...
✅ Scan completed!
```

### Step 4: Results Displayed
```
Found 2 open ports:
  • Port 3306/tcp: mysql
  • Port 5432/tcp: postgresql
```

---

## 🧠 AI Understanding

The CLI uses **Claude or Gemini** to understand your intent:

| Your Input | Detected Action | Scan Type |
|-----------|-----------------|-----------|
| "scan localhost quickly" | scan | fast |
| "aggressive scan google.com" | scan | aggressive |
| "full port scan 192.168.1.1" | scan | aggressive |
| "show network info" | network | - |
| "generate report" | report | - |
| "help" | help | - |

### Fallback Mode
If Claude/Gemini are unavailable, the CLI uses **rule-based parsing** with keywords:
- **Keywords**: scan, report, network, help, exit
- **Speed**: fast/quick/top, standard, aggressive/full/deep
- **Targets**: Detects IPs (192.168.1.1), domains (google.com), localhost

---

## 🎨 Beautiful Terminal Output

```
╔════════════════════════════════════════════════════════╗
║           🛡️  SentinelAI - Natural Language CLI        ║
║              Powered by Claude/Gemini                  ║
╚════════════════════════════════════════════════════════╝

Type your commands in natural English!
Type 'help' for examples or 'exit' to quit.

You> scan localhost quickly

🔍 Scanning 127.0.0.1 (fast mode - ~30 seconds)...

AI:
✅ Scan completed!

============================================================
Found 2 open ports:
  • Port 3306/tcp: mysql
  • Port 5432/tcp: postgresql
============================================================
```

---

## 🔧 Configuration

### Available LLM Providers
```bash
python sentinelai.py natural-cli --llm claude
python sentinelai.py natural-cli --llm gemini
python sentinelai.py natural-cli --llm auto  # Auto-select available
```

### Required API Keys
Set in `.env`:
- `CLAUDE_API_KEY=sk-ant-...`
- `GEMINI_API_KEY=AQ.Ab8RN6...`
- `OPENAI_API_KEY=sk-...`

---

## 📊 Scan Types Explained

### ⚡ Fast Scan (~30 seconds)
- Scans **top 20 most common ports**
- Good for quick checks
- Keywords: "quick", "fast", "top ports"
```
python sentinelai.py scan --target 127.0.0.1 --fast
```

### 🔍 Standard Scan (~2-3 minutes)
- Scans **1000 ports** with service detection
- Balanced speed vs. thoroughness
- Default mode
```
python sentinelai.py scan --target 127.0.0.1
```

### 🚨 Aggressive Scan (~5-10 minutes)
- Full comprehensive scan with scripts
- Detects vulnerabilities
- Keywords: "aggressive", "full", "deep"
```
python sentinelai.py scan --target 127.0.0.1 --aggressive
```

---

## 🎓 Advanced Examples

### 1. Quick Scan Then Generate Report
```
You> scan 192.168.1.1 fast
[Scan completes]
You> generate report as json
```

### 2. Analyze Specific Target
```
You> scan google.com aggressively
[Long scan...]
You> analyze the results
```

### 3. Check Your Own System
```
You> network info
You> scan localhost
You> generate csv report
```

---

## 🛠️ Troubleshooting

### "No AI Available" Message?
- Install dependencies: `pip install -r requirements.txt`
- Add API keys to `.env`
- Check internet connection

### Scan Times Out?
- Use `--fast` flag for quick scans
- Check if Nmap is installed: `nmap --version`
- Verify target is reachable: `ping <target>`

### Command Not Understood?
- Try simpler wording
- Use keywords like "scan", "report", "network"
- Type `help` to see examples

---

## 📝 Conversation History

All interactions are logged:
```python
cli.conversation_history = [
  {
    "user": "scan localhost quickly",
    "intent": {"action": "scan", "target": "127.0.0.1", ...},
    "success": true
  },
  ...
]
```

---

## 🚀 Future Enhancements

- [ ] Multi-turn conversations with context
- [ ] Scan scheduling and automation
- [ ] Advanced threat analysis
- [ ] Vulnerability database integration
- [ ] Custom prompt templates
- [ ] Voice input support

---

## 🎯 Key Differences from Traditional CLI

| Feature | Traditional CLI | Natural Language CLI |
|---------|-----------------|---------------------|
| Command Syntax | Strict format needed | Plain English |
| Learning Curve | Steep | Very gentle |
| Flexibility | Fixed parameters | Understands variations |
| AI Integration | None | Full Claude/Gemini |
| Error Messages | Technical | Conversational |
| Speed | Very fast | Slight AI latency |

---

**Status: ✅ Ready for Use!**

Your mentor will love this innovation! 🎉
