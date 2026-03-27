# Secure Downloads Log

## 2026-03-25 15:45 — ontology
- **Source:** clawhub.com/skills/ontology (oswalpalash)
- **Author:** oswalpalash
- **Verdict:** 🟡 SUSPICIOUS
- **Flags found:** 1 — Python script (scripts/ontology.py) not fully scannable
- **Action:** INSTALLED ✅
- **Approved by:** Yehuda Mizrahi (triple confirmation)
- **Notes:** ClawHub official source. SKILL.md content clean. Script reads/writes only to memory/ontology/. Credential type explicitly documented as "never store secrets directly".
---

## 2026-03-26 09:14 — etoro (agent-portfolio)
- **Source:** https://www.etoro.com/wp-content/uploads/agent-portfolios/SKILL.md
- **Author:** eToro (official domain, NYSE: ETOR)
- **Verdict:** 🟡 SUSPICIOUS
- **Flags found:** 4 — hardcoded public API key, requires user real:write key, executes real trades with real money, external HTTP calls to public-api.etoro.com
- **Action:** INSTALLED ✅
- **Approved by:** Yehuda Mizrahi (triple confirmation)
- **Notes:** Technically safe — no malware, no prompt injection, no credential theft. Flags are financial risk (real money trades) and standard API integration patterns. Source is official eToro domain.
---
