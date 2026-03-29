# Phantom - Ethical RedTeam

> An autonomous AI red team agent that thinks, adapts, and hacks like a real pentester.

![Phantom in action](images/phantom-banner.png)

Phantom is an open-source autonomous offensive security agent. Point it at an authorized target, and it reasons through the entire attack chain on its own: reconnaissance, scanning, exploitation, lateral movement, and reporting. No predefined scripts, no hand-holding.

It works with any LLM provider (cloud or local), generates custom attack tools on the fly when its built-in arsenal isn't enough, and delivers a full debrief with a precise timeline when it's done.

**This project exists to prove one thing:** AI can do offensive security autonomously.

> **Legal notice:** Use only on systems you own or have written authorization to test. Nothing in this repository grants permission to target third-party systems.

---

## Why Phantom?

Most security tools run a checklist. Phantom doesn't. It:

- **Thinks for itself** - decides its own attack strategy based on what it discovers
- **Chains findings** - combines vulnerabilities into real exploitation paths (e.g., SSRF + internal service = RCE)
- **Writes its own tools** - encounters something new? It generates and runs a custom script to handle it
- **Goes deep** - persistence, lateral movement, data exfiltration, all within scope
- **Debriefs you** - timeline + attack graph of everything it did, with full logs

---

## Quick Start

### One-liner install

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/kmdn-ch/phantom-ethical-redteam/main/get.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/kmdn-ch/phantom-ethical-redteam/main/get.ps1 | iex
```

The installer clones the repo, detects your LLM provider, asks for your target scope, and installs dependencies. If Phantom is already installed, it updates automatically.

### Manual install

```bash
git clone https://github.com/kmdn-ch/phantom-ethical-redteam.git ~/phantom
cd ~/phantom
chmod +x install.sh
./install.sh
```

### Run a mission

```bash
source .venv/bin/activate
export $(cat .env)
python3 agent/main.py
```

### Resume a mission

```bash
python3 agent/main.py --resume 20260318_120000
```

---

## Supported LLM Providers

Phantom works with any of these out of the box. Local models via Ollama are fully supported - no cloud required.

| Provider | Default Model | API Key Env Var |
|---|---|---|
| Anthropic (Claude) | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |
| OpenAI (ChatGPT) | `gpt-5.4` | `OPENAI_API_KEY` |
| xAI (Grok) | `grok-4-20-beta` | `XAI_API_KEY` |
| Google (Gemini) | `gemini-3.0-pro` | `GEMINI_API_KEY` |
| Mistral | `mistral-large-latest` | `MISTRAL_API_KEY` |
| DeepSeek | `deepseek-chat-v3.2` | `DEEPSEEK_API_KEY` |
| Ollama (local) | `deepseek-v3.2:cloud` | *(none)* |

---

## What's in the Toolbox (26 tools)

### Reconnaissance
- **Subdomain discovery** - passive enumeration via crt.sh + HackerTarget
- **Port scanning** - Nmap with quick, service, full, and vuln scan modes
- **Tech fingerprinting** - WhatWeb with Python fallback

### Scanning & Fuzzing
- **CVE scanning** - Nuclei for known vulnerabilities and misconfigurations
- **WordPress scanner** - version, users, plugins, xmlrpc, debug.log, config backups
- **Directory fuzzing** - ffuf for hidden endpoints
- **SQL injection** - sqlmap detection and exploitation
- **Payload library** - PayloadsAllTheThings integration (13 attack categories)

### Exploitation & Network
- **Credential brute force** - Hydra for HTTP, SSH, FTP, MySQL, RDP
- **Metasploit** - module search, exploit execution, auxiliary scanning
- **JWT attacks** - HS256 brute force, alg=none, claim tampering, token forging
- **GraphQL enumeration** - introspection, schema dump, sensitive field discovery
- **Privilege escalation** - Linux/Windows enumeration (SUID, sudo, Docker, SeImpersonate)
- **Network MITM** - ARP probing via Bettercap (Linux only)

### Evidence & Stealth
- **Screenshots** - Playwright / wkhtmltoimage / Chromium capture
- **Auth management** - bearer, basic, cookie, custom headers per target
- **Stealth profiles** - 4 modes (silent / stealthy / normal / aggressive) with UA rotation and proxy support

### Social Engineering (educational only)
- **Phishing templates** - dynamic email templates for 5 scenarios
- **Zphisher pages** - phishing page templates for awareness training

### Reporting
- **Report generation** - Markdown + HTML + optional PDF
- **Mission diff** - compare sessions to track remediation (new / resolved / persistent)
- **Risk scoring** - aggregate CVSS from findings
- **Scope check** - verify targets before acting
- **Log reader** - parse Nuclei JSONL, ffuf JSON, and other tool outputs
- **Human checkpoint** - pause and ask the operator
- **Cleanup** - remove temp files, preserve reports

---

## How It Works

Here's what a real mission looks like:

```
Phantom: Starting mission on https://target.com
  Scope confirmed. Beginning with passive recon.

[TOOL] run_nmap (service scan)
  22/tcp   SSH        OpenSSH 8.9
  80/tcp   HTTP       Apache 2.4.51
  443/tcp  HTTPS      Apache 2.4.51
  3306/tcp MySQL      MariaDB 10.6

[TOOL] run_recon
  47 unique subdomains discovered

[TOOL] run_whatweb
  WordPress detected. Missing: CSP, X-Frame-Options

[TOOL] run_nuclei
  [CRITICAL] CVE-2023-2745 - wp-admin path traversal
  [HIGH] CVE-2022-3590 - xmlrpc SSRF

[TOOL] run_ffuf
  /admin, /wp-login.php, /api/v1/users, /backup.zip

[TOOL] run_sqlmap
  UNION injection found - 4 columns, 12 tables, 4200 users
```

After 10 turns, Phantom pauses for a human check-in:

```
Pause after 10 steps.
Enter = continue | 'stop' = stop | 'report' = force report
```

When the mission ends:

```
=== MISSION COMPLETE ===

Risk Score: 9.2/10 (Critical)
  Critical: 3 | High: 5 | Medium: 2 | Low: 1

Critical findings:
  1. CVE-2023-2745 - WordPress path traversal (arbitrary file read)
  2. SQL injection on /api/v1/users?id= (full database dump)
  3. /backup.zip publicly accessible (plaintext credentials)
```

Reports saved as Markdown, HTML, and optional PDF in `logs/<session>/`.

---

## Configuration

The installer creates your config files from templates. They are not tracked by git.

### `config.yaml`

```yaml
provider: "anthropic"        # anthropic | openai | grok | gemini | ollama | mistral | deepseek
model: ""                    # leave empty for provider default
autonomous: true
max_autonomous_turns: 50
pause_every_n_turns: 10

# Performance
max_parallel_tools: 4        # concurrent tool execution
requests_per_second: 5       # rate limit
retry_max: 3                 # retries with exponential backoff

# Stealth
stealth_profile: "normal"    # silent | stealthy | normal | aggressive
# proxy: "http://127.0.0.1:8080"  # route through Burp
```

### Scope file (`scopes/current_scope.md`)

```markdown
# Authorized targets
http://target.com
http://api.target.com
192.168.1.0/24

# Authorization: Pentest contract signed 2026-03-15
```

---

## Project Structure

```
phantom/
  agent/
    main.py                  # Entry point
    agent_client.py          # Agentic loop + parallel execution
    providers/               # 7 LLM provider adapters
    tools/                   # 26 tool implementations
    utils/                   # Input validation + sanitization
  tests/                     # Unit tests
  prompts/system_prompt.txt  # Agent system prompt
  config.yaml.example        # Config template
  scopes/                    # Scope templates
  install.sh / install.ps1   # Interactive installers
  get.sh / get.ps1           # One-liner downloaders
```

---

## Mission Diff (Remediation Tracking)

Compare two sessions to see what got fixed and what's still open:

```
Mission Diff: session_A -> session_B

  NEW (1):
    [+] [HIGH] CVE-2024-1234

  RESOLVED (8):
    [-] [CRITICAL] CVE-2023-2745
    [-] [HIGH] SQLi on /api/users

  PERSISTENT: 7 findings
```

---

## Legal

This tool is for **authorized penetration testing only**. Running it against systems you do not have written permission to test is illegal. The authors are not responsible for misuse.

---

*Built by [KMDN](https://github.com/kmdn-ch) - Switzerland*
