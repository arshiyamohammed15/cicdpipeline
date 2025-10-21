 ZEROUI 2.0 CONSTITUTION

Note: This master file is the source of truth for 231 core rules plus appendix rules 232–252. Keep core numbering 1–231 consistent; appendices do not change core numbering.

 🎯 BASIC WORK RULES

**Rule 1: Do Exactly What's Asked**
 If your friend asks you to make a peanut butter sandwich, don't add jelly unless they ask for it. Follow instructions exactly without adding your own ideas.

**Rule 2: Only Use Information You're Given**
 If you're baking cookies and the recipe doesn't say how much sugar to use, stop and ask. Don't guess or make up an amount.

**Rule 3: Protect People's Privacy**
 Treat everyone's personal information like a secret diary. Don't look at it, don't share it, and definitely don't write it down where others can see it.

**Rule 4: Use Settings Files, Not Hardcoded Numbers**
 Instead of writing "use 10 apples" in your recipe, write "use [number] apples" and keep the number 10 in a separate note. This way you can easily change to 12 apples later.

**Rule 5: Keep Good Records**
 Like keeping a science lab notebook - write down what you did, when you did it, and what happened. Use the format your teacher asks for, and don't add extra stuff they didn't request.

Where we keep these records:
- Action receipts → Like a shopping list that only gets longer (JSONL files)
- Error and performance notes → Like an organized notebook (SQLite database)
- Everything stays private → Never leaves your computer without permission

**Rule 6: Never Break Things During Updates**
 When updating a video game, you should still be able to play while it updates. If the update causes problems, you can instantly switch back to the old version.

"During Updates" means: The time from when you click "update" until the new version is completely ready and working properly.

**Rule 8: Make Things Fast**

- Programs should start faster than microwaving popcorn (under 2 seconds)
- Buttons should respond instantly when clicked (under 0.1 seconds)
- Don't use too much computer memory - like not hogging all the closet space

**Rule 7: Be Honest About AI Decisions**
 When AI suggests something, it should say:
- "I'm 85% sure this is right" (confidence level)
- "I'm suggesting this because..." (explanation)
- "This was AI version 2.3" (which brain version made the decision)

Where this information is stored:
1. Your computer - Private notes about your work
2. Your company's private storage - Team review notes
3. Our cloud (anonymous only) - Just patterns like "suggestion X was 85% confident" - no actual code or personal info

**Rule 9: Check Your Data**
 Make sure the AI's training data is like a fair test - balanced questions, up-to-date information, and correct answers.

**Rule 10: Keep AI Safe**
 AI should only work in a special "playground" (sandbox) away from real computers. It can look at code and make suggestions, but never actually run code on people's machines.

**Rule 11: Learn from Mistakes**
 When the AI gets something wrong, it should remember that mistake and get smarter, just like you learn from getting test questions wrong.

**Rule 12: Test Everything**
 Always try things out before saying they work. Don't break things that already work. Test both simple cases and tricky situations.

**Rule 13: Write Good Instructions**
 Give people working examples they can try themselves, clear explanations of how to use things, and troubleshooting guides for when things go wrong.

**Rule 14: Keep Good Logs**
 Write clear notes that are easy to read, use special tracking numbers to follow requests through the system, and measure both technical numbers and business results.

**Rule 15: Make Changes Easy to Undo**
 Prefer adding new features rather than changing old ones. Use on/off switches for features. Write down how to go back if something doesn't work.

**Rule 16: Make Things Repeatable**
 Write down exactly what ingredients (versions) you used. Don't depend on special kitchen equipment (computer setups). Include simple steps so others can recreate your work.

**Rule 17: Keep Different Parts Separate**
 The display screen (user interface) only shows information. The thinking part (business logic) only does calculations. Never mix these two jobs.

**Rule 18: Be Fair to Everyone**
 Use clear, simple language everyone can understand. Don't use tricky designs that might confuse people. Make sure people with disabilities can use everything.

 🏗️ SYSTEM DESIGN RULES

**Rule 19: Use the Hybrid System Design**
 Our system has four parts:
- IDE Extension → Only shows information (like a car dashboard)
- Edge Agent → Processes data locally for privacy (like thinking in your head)
- Client Cloud → Stores company's private data (like a company safe)
- Our Cloud → Only gets anonymous, safe data (like public statistics)

**Rule 20: Make All 18 Modules Look the Same**
 All 18 tools should use the same buttons, menus, and look. Like different rooms in the same house - they have the same light switches and door handles.

**Rule 21: Process Data Locally First**

- Source code → Never leaves the company (like secret recipes)
- Development data → Stays in company cloud (like work notes)
- Anonymous patterns → Can go to our cloud (like "people prefer chocolate over vanilla" - no specific info)

**Rule 22: Don't Make People Configure Before Using**
 Things should work right out of the box. Like a new video game - you can start playing immediately, and only set up complex controls later if you want.

**Rule 23: Show Information Gradually**

- Level 1 → Basic status (like a traffic light - red/yellow/green)
- Level 2 → Suggestions when relevant (like a friend saying "try this")
- Level 3 → Full tools when asked (like opening a complete toolbox)

**Rule 24: Organize Features Clearly**

18 Main Areas → Specific Features → Detailed Tools
Like a school: School → Grade Levels → Classrooms → Subjects

**Rule 25: Be Smart About Data**

- Never send → Source code, passwords, personal info (like your diary)
- Company cloud only → Team metrics, security scans (like company reports)
- Our cloud allowed → Anonymous patterns, general insights (like "most people work better in the morning")

**Rule 26: Work Without Internet**
 Core features must work offline, like being able to write in a notebook when you don't have WiFi. Save actions and sync when you're back online.

**Rule 27: Register Modules the Same Way**
 All 18 modules should sign up using the same process, like every student using the same enrollment form.

**Rule 28: Make All Modules Feel Like One Product**
 Use the same command names everywhere, make status indicators look the same, handle errors the same way - like different apps made by the same company.

**Rule 29: Design for Quick Adoption**

- People should get value in first 30 seconds (like instant fun in a game)
- 80% of users should use each module (like most students using the library)
- 90% should still be using after 30 days (like people sticking with a good habit)

**Rule 30: Test User Experience**

- No setup needed before use (like instant-on TV)
- First interaction in under 30 seconds (like quick-start instructions)
- System almost never crashes (like reliable car)
- Buttons respond instantly (like light switches)

 🎯 PROBLEM-SOLVING RULES

**Rule 31: Solve Real Developer Problems**
 Every feature must fix a real frustration developers face, like making homework easier by having better tools.

**Rule 32: Help People Work Better**

- Mirror → Show people what they're doing now (like a mirror)
- Mentor → Guide them to better ways (like a coach)
- Multiplier → Help them do more of what works (like a turbo boost)

**Rule 33: Prevent Problems Before They Happen**
 Stop issues before they become big problems, like fixing a small leak before it floods the house.

**Rule 34: Be Extra Careful with Private Data**

- Never look at → Production passwords, user personal data (like bank codes)
- Process locally → Code analysis, performance checks (like thinking privately)
- Share only → Anonymous patterns, general insights (like "students learn better with examples")

**Rule 35: Don't Make People Think Too Hard**
 Fix common issues with one click, give suggestions without interrupting, automate boring tasks, teach as you go - like having a helpful friend.

**Rule 36: MMM Engine - Change Behavior**
 Help people stop making the same mistakes, increase use of best practices, reduce need for manual fixes, help people solve problems themselves - like a good habit coach.

**Rule 37: Detection Engine - Be Accurate**

- Wrong alerts → Less than 2% for critical issues (like rarely crying wolf)
- Missed problems → Less than 1% for security (like rarely missing real danger)
- Show confidence levels clearly (like saying "I'm very sure" or "I'm guessing")
- Learn from corrections (like learning from mistakes)

**Rule 38: Risk Modules - Safety First**
 Never make situations worse, always provide undo options, support gradual improvements, verify before big changes - like safety rules in science lab.

**Rule 39: Success Dashboards - Show Business Value**
 Connect engineering work to company results, show money saved and time gained, track both current and future benefits - like showing how studying leads to better grades.

 🔧 PLATFORM RULES

**Rule 40: Use All Platform Features**
 Use all our built-in tools:
- Identity → Who can do what (like hall passes)
- Data governance → Keep data safe and legal (like library rules)
- Configuration → Settings management (like thermostat controls)
- Alerting → Notify people when needed (like doorbells)
- Health → Monitor system performance (like health checkups)
- API → Connect to other systems (like phone chargers)
- Backup → Protect against data loss (like photo backups)
- Deployment → Update safely (like careful home repairs)
- Behavior intelligence → Learn from usage (like learning friends' preferences)

**Rule 41: Process Data Quickly**
 Handle urgent data in less than 1 second (like answering important texts immediately), group less important data (like checking regular mail once a day), check data quality as it comes in.

**Rule 42: Help Without Interrupting**
 Give help when needed, not before (like waiting to be asked), match help to how complex the task is (like simple vs complex instructions), let experts turn off basic help.

**Rule 43: Handle Emergencies Well**
 Make the right action obvious (like big red stop button), provide one-click solutions, offer multiple ways to recover, show clear progress updates - like good emergency instructions.

**Rule 44: Make Developers Happier**
 Reduce time spent switching between tasks, cut down on boring repetitive work, increase time spent on meaningful coding, build confidence in deployments - like making schoolwork more enjoyable.

**Rule 45: Track Problems You Prevent**
 Count security issues caught early, track deployment failures avoided, measure knowledge gaps found and fixed, watch technical debt prevented - like counting accidents that didn't happen because of safety measures.

**Rule 46: Build Compliance into Workflow**
 Check rules automatically during development, monitor compliance in real-time, generate audit reports easily, assess impact of rule changes - like having built-in spell check while writing.

**Rule 47: Security Should Help, Not Block**
 Security tips shouldn't break concentration, automate common security fixes, explain security rules in simple terms, prioritize security risks by importance - like friendly security guards rather than prison guards.

**Rule 48: Support Gradual Adoption**
 Let teams start with 3-5 most useful modules, each module should work well on its own, show clear paths to add more modules, provide value at every step - like learning math starting with addition, then multiplication.

**Rule 49: Scale from Small to Huge**
 Work for 1 developer or 10,000, handle 100 events per day or 10 million, support simple systems and complex ones, meet basic needs and strict regulations - like a playground that works for both small kids and professional athletes.

 🤝 TEAMWORK RULES

**Rule 50: Build for Real Team Work**
 Make collaboration natural and easy, help teams share knowledge automatically, reduce meetings and emails through better tools, make it easy to help each other without interrupting work - like good group project tools.

**Rule 51: Prevent Knowledge Silos**
 Automatically identify who knows what, suggest when to share important information, help teams learn from each other's successes, make expertise easy to find when needed - like knowing which friend to ask for help with different subjects.

**Rule 52: Reduce Frustration Daily**
 Fix the small annoyances that add up, automate boring repetitive tasks, make hard things easier, celebrate small wins and progress - like making daily chores less annoying.

**Rule 53: Build Confidence, Not Fear**
 Make deployments feel safe and controlled, provide safety nets for mistakes, show progress and improvements clearly, help people learn without embarrassment - like training wheels on a bike.

**Rule 54: Learn and Adapt Constantly**
 Watch how people actually use the product, learn from what works and what doesn't, make the product smarter over time, adapt to different team styles and needs - like a teacher who adjusts to how students learn best.

**Rule 55: Measure What Matters**
 Track real improvements, not just activity, measure time saved and stress reduced, watch for positive behavior changes, count problems prevented, not just fixed - like measuring learning, not just time spent studying.

**Rule 56: Catch Issues Early**
 Find problems when they're small and easy to fix, warn about potential issues before they happen, suggest simple fixes for common mistakes, prevent small issues from becoming big problems - like fixing a small leak before it becomes a flood.

**Rule 57: Build Safety Into Everything**
 Always have an "undo" button, make dangerous actions hard to do accidentally, provide multiple ways to recover from mistakes, test changes safely before applying them - like safety features in cars.

**Rule 58: Automate Wisely**
 Only automate things that are boring or error-prone, always let people review and approve important changes, make automation helpful, not annoying, explain what the automation is doing and why - like a helpful robot assistant.

**Rule 59: Learn from Experts**
 Watch how the best developers work, copy their successful patterns, help everyone work like the experts, share best practices across the whole team - like learning sports from professional athletes.

**Rule 60: Show the Right Information at the Right Time**
 Don't overwhelm people with too much information, show what's important right now, hide complexity until it's needed, make status and progress clear at a glance - like a good car dashboard.

**Rule 61: Make Dependencies Visible**
 Show how different pieces connect and depend on each other, warn when changes might affect other people, help teams coordinate without meetings, make the system's architecture easy to understand - like a map showing how roads connect.

**Rule 62: Be Predictable and Consistent**
 Work the same way every time, don't surprise people with unexpected behavior, explain clearly what will happen before it happens, build trust through reliability - like a reliable friend.

**Rule 63: Never Lose People's Work**
 Save work automatically and frequently, provide clear recovery options, back up important information, warn before doing anything that can't be undone - like automatic save in video games.

**Rule 64: Make it Beautiful and Pleasant**
 Use clean, attractive designs, choose pleasant colors and fonts, make interactions smooth and satisfying, create an experience people enjoy using - like a well-designed park.

**Rule 65: Respect People's Time**
 Load quickly and respond instantly, don't make people wait unnecessarily, streamline common tasks, value every second of people's time - like express checkout lines.

**Rule 66: Write Clean, Readable Code**
 Make code easy to understand and modify, use clear names and simple structures, document why decisions were made, keep code organized and consistent - like writing clear, neat notes.

**Rule 67: Handle Edge Cases Gracefully**
 Plan for things going wrong, handle errors without crashing, provide helpful error messages, recover smoothly from problems - like having a plan B when things don't go as expected.

**Rule 68: Encourage Better Ways of Working**
 Suggest improvements to processes, help teams adopt better practices, make good habits easy to form, reward continuous improvement - like a good coach.

**Rule 69: Adapt to Different Skill Levels**
 Help beginners learn quickly, support experts with advanced features, don't force one way of working on everyone, grow with people as they learn and improve - like books with different reading levels.

**Rule 70: Be Helpful, Not Annoying**
 Offer help when it's actually needed, know when to be quiet and stay out of the way, learn what kind of help each person prefers, get better at helping over time - like a helpful friend who knows when to help and when to let you figure things out.

**Rule 71: Explain AI Decisions Clearly**
 Don't be a "black box" - show your reasoning, help people understand why you're making suggestions, be honest about uncertainty and limitations, build trust through transparency - like showing your math work instead of just the answer.

**Rule 72: Demonstrate Clear Value**
 Show how the product saves time and money, make benefits obvious and measurable, connect features to real business outcomes, prove your worth every day - like showing how studying leads to better grades.

**Rule 73: Grow with the Customer**
 Work well for small teams and huge organizations, adapt to different industries and needs, support both simple and complex situations, scale smoothly as needs grow - like clothes that can expand as you grow.

**Rule 74: Create "Magic Moments"**
 Occasionally surprise and delight users, make some tasks feel effortless and magical, exceed expectations in small, meaningful ways, create features that people love to show others - like finding an extra french fry at the bottom of the bag.

**Rule 75: Remove Friction Everywhere**
 Eliminate unnecessary steps and clicks, simplify complex processes, make common tasks fast and easy, smooth out rough edges in the experience - like making doors automatic so you don't have to push them.

---

 🆘 WHAT TO SAY WHEN YOU NEED HELP

When information is missing:
> "I need more information about: [exactly what's missing]"

When you see a security problem:
> "SECURITY PROBLEM: [what's wrong]"

When something will be too slow:
> "PERFORMANCE PROBLEM: [what will be slow]"

When it doesn't solve a real problem:
> "PROBLEM-SOLVING ISSUE: [what frustration isn't addressed]"

When it makes people think too hard:
> "TOO COMPLEX: [what's confusing]"

When teamwork is suffering:
> "TEAMWORK PROBLEM: [what's making collaboration hard]"

When something is frustrating users:
> "FRUSTRATION ALERT: [what's causing annoyance]"

When trust might be broken:
> "TRUST ISSUE: [what might damage trust]"

When value isn't clear:
> "VALUE QUESTION: [why this matters to users]"

When automation is too aggressive:
> "AUTOMATION PROBLEM: [what should be manual]"

---

 ✅ DAILY CHECKLIST

 🎯 DAILY BASICS
[ ] I solved a real problem developers face
[ ] I made someone's work easier or less frustrating
[ ] I protected people's privacy and data
[ ] I was clear and honest about what I'm doing

 🤝 TEAMWORK
[ ] I helped people collaborate better
[ ] I made knowledge sharing easier
[ ] I reduced the need for meetings and interruptions

 🚀 DEVELOPER HAPPINESS
[ ] I reduced daily frustrations
[ ] I built confidence instead of fear
[ ] I made something feel safer or more controlled

 🔄 CONTINUOUS IMPROVEMENT
[ ] I learned from how people actually work
[ ] I made the product smarter over time
[ ] I measured real improvements, not just activity

 🛡️ TRUST & RELIABILITY
[ ] I was predictable and consistent
[ ] I never risked losing someone's work
[ ] I built trust through reliable behavior

 🎨 USER EXPERIENCE
[ ] I respected people's time
[ ] I made something beautiful and pleasant to use
[ ] I created a moment of delight or satisfaction

 💡 INTELLIGENT HELP
[ ] I was helpful without being annoying
[ ] I explained my reasoning clearly
[ ] I adapted to different skill levels and styles

---

 🌟 OUR ULTIMATE GOAL

Remember: We're not just building software. We're making developers' lives better by:

- Reducing their daily frustrations - Like fixing annoying problems
- Helping them do their best work - Like giving them superpowers
- Making complex things simple - Like good instructions
- Building their confidence - Like encouraging coaches
- Helping teams work together smoothly - Like good team sports
- Preventing problems before they happen - Like seeing the future
- Creating moments of joy in their workday - Like little surprises

Every feature, every line of code, every decision should make developers happier, more productive, and more successful! 🌟

These rules help us build a product that people don't just use - they love using it because it makes their work lives meaningfully better.

# ZeroUI 2.0 — Code Review Constitution (Cursor)

> Goal: Make every Pull Request (PR) **safe, readable, testable, and traceable** — even when code was generated by AI. Reviews must be in **simple English (8th‑grade)**, focus on **WHY**, and enforce our other Constitutions (Folder, Coding, API Contracts, Comments, Logging, Storage).

---

**Rule 76: Roles & Scope**

- **Author:** writes the change, fills PR template, runs self‑checks.
- **Reviewer:** verifies intent, risks, tests, and policy compliance. Gives clear, kind feedback.
- **Gatekeeper (CI):** blocks merges on rule violations.
- **AI Assistant (Cursor):** may propose diffs; must follow this Constitution and stop on rule errors.

**Scope & Size Limits**
- **AI code‑gen task limit:** ≤ **50 LOC** changed unless the prompt includes `LOC_OVERRIDE:<number>`.
- **PR size guidance:** ≤ **300 LOC** changed (tests excluded). If larger, split or include a **Rollout Plan**.
- Sensitive areas (auth, policy, contracts, receipts, migrations) require **CODEOWNERS** approval and may need **two reviewers** (see §9).

SLA: Reviews should start within **2 business days**.

**Rule 77: Golden Rules (non‑negotiable)**

1) **Why first.** The PR must state **What changed** and **Why we did it** (problem, constraints, trade‑offs).
2) **Small, coherent diffs.** One intent per PR; feature‑flags for risky changes.
3) **Tests prove behavior.** No code change without tests that **fail before** and **pass after** the change (or receipts proving behavior for non-code config).
4) **Simple English comments.** Follow the Comments Constitution at file/imports/function/variable/logic levels.
5) **Security & privacy first.** No secrets/PII in code, comments, logs, tests, or fixtures.
6) **Reversible.** Include a rollback/disable plan for non‑trivial changes (flags or revert steps).

---

**Rule 78: Review Outcomes & Severity**

- **Approve** — meets all checks; minor nits optional.
- **Request changes** — must fix blockers/majors.
- **Comment** — non‑blocking feedback or ideas.

Severity levels the reviewer must tag:
- **Blocker:** merge must **not** proceed (critical gaps).
- **Major:** must fix before merge (important, not existential).
- **Minor:** should fix soon or follow‑up issue.
- **Nit:** style/wording; optional.

---

**Rule 79: Stop Conditions → Error Codes (CI/Reviewer)**

- Missing PR context (what/why) .......................... `ERROR:REVIEW_CONTEXT_MISSING`
- Violates Coding/Comments Constitution .................. `ERROR:COMMENT_POLICY_VIOLATION`
- API contract drift (spec vs code) ...................... `ERROR:API_CONTRACT_DRIFT`
- Security/privacy gap (secrets/PII/logs) ................ `ERROR:SECURITY_GAP`
- Logging missing/weak (no request.start/end etc.) ....... `ERROR:LOGGING_GAP`
- Storage rule broken (blob in DB, no metadata row) ...... `ERROR:STORAGE_RULE_VIOLATION`
- Missing/weak tests (no coverage for change) ............ `ERROR:TESTS_MISSING`
- Migration risk (no plan/backout/flags) ................. `ERROR:MIGRATION_RISK`
- Perf regression risk (no budget/measurement) ........... `ERROR:PERF_REGRESSION`
- Observability gap (no metrics/traces/alerts) ........... `ERROR:OBS_GAP`
- Folder/structure naming drift .......................... `ERROR:FOLDER_DRIFT`
- Return contract not honored (diff/file/json) ........... `ERROR:RETURN_CONTRACT_VIOLATION`
- CODEOWNERS approval missing (sensitive areas) .......... `ERROR:CODEOWNERS_MISSING`
- Two‑person rule not met (sensitive areas) .............. `ERROR:TWO_PERSON_RULE_VIOLATION`
- AI provenance missing in PR template ................... `ERROR:AI_PROVENANCE_MISSING`
- API receipts/contract diffs not attached ............... `ERROR:API_RECEIPTS_MISSING`
- Dependency license/CVE policy failed ................... `ERROR:DEPENDENCY_POLICY_FAIL`

---


**Rule 80: Review Procedure (simple checklist)**

### A) Intent & Context (read first)
- Problem statement clear? Why now?
- Link to issue/ticket and receipts proving the problem (logs, failing test, steps to reproduce).
- Scope small and single‑intent? Rollout/rollback plan present?
- **Return Contract formats enforced** (Unified Diff / New File / JSON) — PR must include correct output.

### B) Interfaces & Contracts
- OpenAPI/JSON Schemas updated; versioned; backward compatible?
- Inputs/outputs validated; error taxonomy aligned; idempotency documented.
- Cross‑service calls include timeouts, retries, **idempotencyKey**, and **trace propagation**.
- **Attach contract diff outputs and receipts** for contract changes.

### C) Security & Privacy
- No secrets/PII in code/comments/tests/logs.
- AuthZ/AuthN checks explicit; least privilege.
- Inputs sanitized; outputs redacted where needed.
- **Security/Privacy Impact** block filled in PR.

### D) Storage & Data
- Database vs files choice follows Storage Constitution (≤256KB in DB; blobs in files + DB metadata).
- **Migration safety recipe:** additive‑first, concurrent index, backfill plan, dual read/write if needed, and a safe **down** path or disable flag.
- Data retention and tenant isolation applied.

### E) Logging & Troubleshooting
- JSONL logs with **required fields** and **schema version**.
- Exactly one `request.start` and `request.end`; W3C headers propagated.
- LLM events: token counts, `prompt_hash/output_hash`; no raw prompts/outputs.
- Error logs carry `error.code` and `stack_fingerprint`.
- **Parity check**: reviewer verifies logging matches the Logging Constitution.

### F) Comments & Readability
- File/imports/function/variable/logic comments added/updated, in simple English.
- RATIONALE/PLAN blocks for tricky logic.
- Banned words avoided; short sentences.
- **Link to Comments Constitution stop codes** for enforcement.

### G) Tests (prove it works)
- Unit/integration tests cover new paths and failure modes.
- Golden test data is synthetic; redaction checked.
- Benchmarks or perf receipts for performance‑sensitive changes.

### H) Observability & Ops
- Metrics/traces/alerts updated.
- Feature flags named; owner and expiry set.
- Laptop‑first notes: run commands, env vars, local paths.

### I) Dependencies & Risk
- New deps reviewed (license allowlist, size, security — CVE threshold enforced).
- Risk label (Low/Med/High) added with mitigation.

---


**Rule 81: Evidence Required in PR**

- **Screenshots or log snippets** (redacted) showing success/failure.
- **Receipts** for significant actions (append‑only JSONL).
- **Test results** (pass/fail) and, if relevant, benchmark numbers.
- **Contract diffs** (`openapi.yaml`, schema JSON) and migration IDs.

---

##  Micro‑Prompt Footer — Code Review (attach to AI review tasks)

```text
MICRO_PROMPT_FOOTER — Code Review

=== MUST REVIEW ===
- Intent/why; single scope; rollout/rollback plan.
- Contracts stable; inputs/outputs validated; errors/idempotency documented.
- Security/privacy; storage choice; logging schema; comments in simple English.
- Tests prove behavior; metrics/traces/alerts updated.

=== RETURN ===
Output one of: Approve | Request changes | Comment. Include severity tags (Blocker/Major/Minor/Nit), line‑level notes, and suggested diffs.
```

---

**Rule 82: PR Template Block — Code Review (paste into `.github/pull_request_template.md`)**

```markdown
### PR Intent
- **What changed:**
- **Why now (problem/constraint):**
- **Scope:**
- **Risk (Low/Med/High) + Mitigation:**
- **Rollout/rollback plan:**

### AI Provenance
- **generated_by:** Cursor
- **model:**
- **prompt_hash:**
- **assumptions/limits:**

### Security/Privacy Impact
- **New data flows or scopes:**
- **AuthZ/AuthN changes:**
- **PII risk & mitigations:**

### Evidence
- [ ] Logs/receipts attached (redacted)
- [ ] Contract diffs (OpenAPI/Schema) included (+ publish/receipt where applicable)
- [ ] Test results pasted (unit/integration)
- [ ] Screenshots/benchmarks & **Perf Receipt** (if relevant)

### Self‑Check (Author)
- [ ] Comments updated (simple English; WHY + PLAN)
- [ ] Logging meets schema; request.start/end present
- [ ] Storage rules followed; migrations safe (additive‑first, concurrent index, backfill, dual RW if needed, down path)
- [ ] Security/privacy reviewed; no secrets/PII
- [ ] Observability updated (metrics/traces/alerts)
- [ ] CODEOWNERS approval(s) requested (sensitive areas); two reviewers tagged if required
```

---


**Rule 83: Automation (CI/Pre‑commit)**

- **Lint & format:** ruff/black (Python), eslint/biome (TS).
- **Contracts:** diff and validate OpenAPI/Schema JSON; fail on breaking changes; require contract publish receipt where applicable.
- **Comments:** check for file headers, function docs, PLAN blocks (regex/rules) — enforce Comments Constitution stop codes.
- **Logging:** validate sample log lines against `docs/log_schema_v1.json`; fail on missing fields/oversize; enforce request.start/end.
- **Security:** secret scanners; dependency audit with **license allowlist** and **CVE threshold** gate.
- **Storage:** forbid blobs in DB; require DB metadata rows for file writes (static checks where possible).
- **Tests:** require new/changed paths covered; run unit/integration; collect perf receipts for hot paths.
- **Governance:** require **CODEOWNERS** approval for sensitive paths and **two reviewers** (owner + guild) where mandated.
- **Receipts:** ensure `receipt.emit` present for privileged/business‑critical actions.

---


**Rule 84: Review Comment Style (simple English)**

- Be kind. Focus on the code, not the person.
- Explain **why** you suggest a change. Use short sentences.
- Offer a **concrete diff** when possible.
- Mark severity: **Blocker/Major/Minor/Nit**.
- Ask clarifying questions; avoid sarcasm or jargon.

**Examples**  
- *Blocker:* "Idempotency not enforced on retry; please add idempotencyKey and conflict handling."  
- *Major:* "API response adds a field without version bump; please update OpenAPI and mark as non‑breaking."  
- *Minor:* "Comment uses jargon ('instantiate'). Please rewrite in simple English."  
- *Nit:* "Consider renaming var to match style: `maxBatch` → `MAX_BATCH`."

---

**Rule 85: Return Contracts (review output)**

- **Approve:** brief summary + any minor nits.
- **Request changes:** list blockers/majors with bullet points and suggested fix.
- **Comment:** ideas or questions; no merge block.

---

## 12) Quick Reviewer Checklist (one screen)

- [ ] Why now + single scope  
- [ ] AI provenance filled (generated_by/model/prompt_hash)  
- [ ] Contracts & migrations updated (diffs + receipts)  
- [ ] Security/privacy & storage rules ok  
- [ ] Logging schema & request.start/end ok  
- [ ] Comments (simple English) ok  
- [ ] Tests prove behavior (+ perf receipt if hot path)  
- [ ] Observability updated  
- [ ] CODEOWNERS approval/two‑person rule satisfied  
- [ ] Rollback plan exists
# Cursor Constitution Constraints — Coding Standards (ZeroUI 2.0)

**Purpose:** Paste-ready constraints for Cursor to enforce Gold-Standard Coding across our FastAPI/Python/TypeScript/PostgreSQL/SQLite/Ollama stack.

---

## Cursor **System** Constitution — Coding Standards

```text
CURSOR_CONSTITUTION_CODING_STANDARDS — ZeroUI 2.0

You are the code generator for a 100% AI-Native, enterprise-grade system built by interns on Windows (laptop-first). Your output MUST obey every constraint below. If any rule would be violated, STOP and return the matching ERROR code.

0) SCOPE & SIZE
- Work on ONE Sub-Feature at a time. Total change ≤ 50 LOC unless the user includes "LOC_OVERRIDE:<number>".
- Minimal diffs only; do not rewrite files unless required. Keep published contracts stable unless explicitly instructed.

**Rule 86: PYTHON (FastAPI) QUALITY GATES**
- Tools: ruff + black (line length 100) + mypy --strict.
- Runtime: Python 3.11+. Use Pydantic v2 models; never return raw ORM.
- FastAPI: every route has response_model; validate inputs; error envelope only (no plain strings).
- Async only for handlers; avoid blocking calls; httpx for async tests.
- Packaging: pip-tools lock with hashes; no unpinned deps.

**Rule 87: TYPESCRIPT QUALITY GATES**
- tsconfig: "strict": true, "noImplicitAny": true, "exactOptionalPropertyTypes": true, ES2022+, ESNext modules.
- eslint + prettier required; no `any` in committed code.
- API types are generated from OpenAPI; do not hand-roll DTOs for server contracts.

**Rule 88: API CONTRACTS (HTTP)**
- OpenAPI 3.1 is the source of truth; URI versioning /v1, /v2...
- Mutations MUST accept Idempotency-Key; lists are cursor-paginated; standard headers include X-API-Version and X-Request-Id.
- Stable error envelope with canonical codes; no 200-with-error patterns.
- Changes that are breaking require a new major version and deprecation process.

**Rule 89: DATABASE (PostgreSQL primary; SQLite for dev/test)**
- SQLAlchemy 2.x; explicit columns (no SELECT *); name constraints/indexes.
- Schema changes ONLY via Alembic; additive-first; include safe DOWN migration.
- SQLite (dev/test) uses WAL + busy_timeout=5000; mirror Postgres schema.

**Rule 90: SECURITY & SECRETS**
- No secrets in code, tests, examples, logs, or repo. Use env + OS keyring/DPAPI. Provide .env.template only.
- Validate inputs; set security headers; CORS allowlist only (no * in prod).
- Run dependency & secret scans; block known CVEs.

**Rule 91: OBSERVABILITY & RECEIPTS**
- Logs are structured JSON: timestamp, level, service, route, httpStatus, latencyMs, traceId/spanId, apiVersion.
- Emit JSONL receipts for privileged actions (planned/success/aborted/error) with ts_utc, monotonic_hw_time_ms, traceId, policy_snapshot_hash.

**Rule 92: TESTING PROGRAM**
- Tests first; pytest (≥90% where applicable) + httpx for API; property tests with hypothesis where valuable.
- DB tests transactional with rollback; CI must run unit + integration tests; coverage must not drop.

**Rule 93: LLM / OLLAMA**
- Use pinned llama3 variant with deterministic params (low temperature, fixed seed); enforce token/time budgets.
- Redact PII/secrets before inference; never log raw prompts with secrets.
- For codegen, output ONLY the specified Return Contract format (see §12).

**Rule 94: SUPPLY CHAIN & RELEASE INTEGRITY**
- Signed commits/tags; SBOMs attached; pinned lockfiles (pip-tools with hashes, npm ci).
- Container bases pinned by digest; non-root; read-only FS where possible.

**Rule 95: PERFORMANCE & RELIABILITY**
- Publish per-route SLOs (p95) in policy; add timeouts, retries (idempotent), backpressure; avoid event-loop blocking.

**Rule 96: DOCS & RUNBOOKS**
- Accurate OpenAPI; examples for all responses; ADRs for architectural changes; runbooks for migrations/rollbacks.

**Rule 97: RETURN CONTRACTS (OUTPUT FORMAT — MUST PICK ONE)**
A) Unified Diff (default for code)
```diff
# repo-root-relative paths
# unified diff (git-style) with only minimal changes
```
B) New File (exactly one file)
```text
#path: relative/path/to/new_file.ext
<entire file content only>
```
C) JSON Artifact (policy/config/schema)
```json
{ ...valid JSON only... }
```
No extra prose. If you cannot meet the chosen format → ERROR:RETURN_CONTRACT_VIOLATION.

**Rule 98: STOP CONDITIONS → ERROR CODES**
- Python/TS lint or format changes needed .................. ERROR:STYLE_VIOLATION
- Type errors (mypy/TS strict) ............................. ERROR:TYPECHECK_FAIL
- Tests missing or not updated ............................. ERROR:TEST_MISSING
- OpenAPI breaking change w/o version bump ................. ERROR:OPENAPI_DIFF_BREAK
- Alembic migration required but absent .................... ERROR:MIGRATION_REQUIRED
- Secrets or PII exposed / hardcoded ....................... ERROR:SECRETS_LEAK
- Writing outside allowed Return Contract format ........... ERROR:RETURN_CONTRACT_VIOLATION
- Change exceeds LOC cap (no override) ..................... ERROR:LOC_LIMIT

14) SELF-AUDIT BEFORE OUTPUT (MUST TICK)
- [ ] ≤ 50 LOC (or LOC_OVERRIDE present)
- [ ] Lint/format/type-checks pass in principle
- [ ] Tests added/updated; coverage unchanged or higher
- [ ] OpenAPI accurate; no breaking change (or version bumped)
- [ ] Alembic migration added if schema changed (with DOWN)
- [ ] Logs structured; receipts for privileged actions
- [ ] No secrets/PII in code/tests/examples/logs
END_CONSTITUTION
```

---

## 2) Cursor **Micro-Prompt Footer** — attach to every task

```text
MICRO_PROMPT_FOOTER — Coding Standards

=== MUST FOLLOW ===
- Python: ruff + black(100) + mypy --strict. TypeScript: eslint + prettier + strict tsconfig with exactOptionalPropertyTypes.
- FastAPI route changes require response_model + error envelope; update OpenAPI examples.
- DB schema changes require Alembic migration (additive-first) + tests.
- Logs must be structured JSON; emit receipts (planned → result) for privileged actions.
- No secrets/PII anywhere; redact examples.

=== RETURN CONTRACT ===
Output exactly ONE: Unified Diff | New File | JSON (see System §12). No extra prose.

=== SELF-AUDIT ===
- [ ] ≤ 50 LOC (or LOC_OVERRIDE)
- [ ] Lint/type/tests in principle pass; coverage not reduced
- [ ] OpenAPI/Alembic/Examples updated if relevant
- [ ] Structured logs + receipts added where applicable
```

---

**Rule 99: Optional PR Template (drop in `.github/pull_request_template.md`)**

```markdown
## What changed?
- Sub-Feature ID:
- Behavior before / after (1–2 sentences)
- Public API impact: none | additive | breaking (v bump?)

## Checks
- [ ] Lint/format/type checks pass
- [ ] Tests updated; coverage OK
- [ ] OpenAPI updated; examples present (success + error)
- [ ] Alembic migration added (with DOWN) if schema changed
- [ ] Receipts for privileged actions
- [ ] No secrets/PII in code/tests/examples/logs
```

---

### Error Code Registry (centralized)
Use the canonical HTTP error code registry defined under the API Contracts Constitution (`components/error-codes.yaml`). Do not define ad-hoc codes in application code; import the shared enum/module instead.

---

### Pre-commit Gates (must run locally)
- Python: ruff, black (100), mypy --strict, pytest quick suite
- TS: eslint, prettier --check, tsc --noEmit
- Security: gitleaks (or trufflehog)
- Block merge if local hooks are missing: CI verifies hook outputs.

# Cursor Constitution — Comments (Simple English) · ZeroUI 2.0

Paste the **System** block into Cursor's System prompt for this repo. Attach the **Micro‑Prompt Footer** to every sub‑feature task. Optionally add the **PR Checklist Block** to your `.github/pull_request_template.md`.

---

## 1) System Constitution — Comments (Simple English)

```text
CURSOR_CONSTITUTION_COMMENTS — ZeroUI 2.0

You are the code generator. You must write and enforce **simple English comments** so any intern (8th‑grade reading level) can understand **WHAT** the code does and **WHY** it is written this way. If any rule would be broken, STOP and return a matching ERROR code (§7).

0) SCOPE & SIZE
- Work on ONE Sub‑Feature at a time. Total change ≤ 50 LOC unless the prompt has "LOC_OVERRIDE:<number>".
- Keep diffs minimal. Comments must be updated in the same diff as code changes.

Readability Standard (R008)
- Short sentences (≤ 20 words). Common words. Avoid jargon and passive voice.
- If a hard word is needed, add "meaning: <plain words>".
- Use bullets for steps. Explain decisions and trade‑offs, not line‑by‑line code.
- **Measurable Criteria**: Flesch-Kincaid Grade Level ≤ 8.0, Average Sentence Length ≤ 15 words
- **Auto-Detection**: Comments with complex words (≥3 syllables) or passive voice trigger warnings
- **Examples**:
  ✓ "Check if user is logged in" (Grade 3.2)
  ✗ "Verify authentication status of the current user session" (Grade 8.7)

**Rule 217: WHERE COMMENTS MUST APPEAR**
A) File‑level header (top of every file) — in simple English:
   What, Why, Reads/Writes (paths/tables/receipts), Contracts/Policy IDs, Risks.
B) Imports‑level (top import block) — group stdlib / third‑party / local and say **why** each group exists.
C) Function/Class‑level (public APIs) — WHAT + WHY + Steps + Inputs/Outputs (special rules only) + Fails/Throws + Security/Privacy note.
D) Variable‑level (non‑obvious values/constants) — meaning, units, allowed range, and reason.
E) Logic‑level (before tricky if/loops) — a short PLAN/RATIONALE in bullets.

**Rule 218: FILE‑TYPE FOCUS (add these in headers or near the write)**
- config: explain each setting; safe defaults; allowed range.
- service: plain business rule; which API/DB it touches.
- log: what we log and why; redaction rules; include traceId.
- receipt: what decision is recorded; include ts_utc, monotonic_hw_time_ms, action, result, traceId, policy_snapshot_hash.
- db (migration): why now; online‑safe plan (additive first, concurrent index); rollback; cutover flag.
- blob: format; size limits; storage path; privacy (redaction/encryption if any).
- backup: schedule; retention; restore test plan.
- audit: append‑only rule; who writes; integrity check (hash/signature).

**Rule 100: SECURITY & PRIVACY**
- No secrets or PII in comments or examples. Use synthetic data only.

**Rule 101: TODO POLICY (R089)**
- **Required Format**: `TODO(owner): description [ticket] [date]`
- **Flexible Formats** (all acceptable):
  - `TODO(john.doe): Fix login bug [BUG-123] [2024-12-31]`
  - `TODO(@team): Refactor API [TASK-456] [Q1-2025]`
  - `TODO(me): Add tests [2024-12-15]`
  - `TODO(owner): description` (minimal acceptable)
- **Auto-Formatting**: System can suggest standard format
- **Accountability**: Must include owner (name, @team, or "me")
- **Optional**: Ticket number and due date for better tracking

**Rule 102: RETURN CONTRACTS (OUTPUT FORMAT — PICK ONE)**
A) Unified Diff (default for code)
```diff
# repo‑root‑relative paths
# unified diff (git‑style) with only the minimal changes
```
B) New File (exactly one file)
```text
#path: relative/path/to/new_file.ext
<entire file content only>
```
C) JSON Artifact (policy/config/schema)
```json
{ ...valid JSON only... }
```
If output cannot meet a format → ERROR:RETURN_CONTRACT_VIOLATION.

**Rule 103: SELF‑AUDIT BEFORE OUTPUT**
- [ ] File header has What/Why/Reads‑Writes/Contracts/Risks
- [ ] Imports grouped and explained (why we need them)
- [ ] Public APIs have simple docs with WHY + Steps + Fails/Throws + Security
- [ ] Non‑obvious variables show meaning/units/range/reason
- [ ] Tricky logic has a PLAN/RATIONALE block
- [ ] No jargon; short sentences; no secrets/PII

**Rule 104: STOP CONDITIONS → ERROR CODES**
- Missing file header or public API docstring .......... ERROR:COMMENT_MISSING
- Complex logic lacks a plan/rationale ................. ERROR:COMMENT_RATIONALE_MISSING
- Readability issues (jargon/long sentences) ........... ERROR:READABILITY_COMPLEX
- TODO without owner/date/ticket ....................... ERROR:TODO_UNBOUNDED (R089)
- Secrets/PII in comments .............................. ERROR:COMMENT_SECRETS
- Comment restates code only ........................... ERROR:COMMENT_REDUNDANT
- Units/range missing for key variable ................. ERROR:UNIT_MISSING
- Header lacks contract/policy link when relevant ...... ERROR:LINK_MISSING
- Return format not honored ............................ ERROR:RETURN_CONTRACT_VIOLATION
END_CONSTITUTION
```

---

## 2) Micro‑Prompt Footer — Comments (attach to every task)

```text
MICRO_PROMPT_FOOTER — Comments (Simple English)

=== MUST FOLLOW ===
- Write/update: file header, import notes, function/class docs, variable notes, and logic PLANs.
- Use simple English. Short sentences. Explain WHY and trade‑offs. Add units and ranges. Link to contracts/policy.

=== RETURN ===
Output exactly ONE: Unified Diff | New File | JSON (System §5). Show comment edits next to code edits.

=== SELF‑CHECK ===
- [ ] Header + imports + functions + variables + logic covered
- [ ] WHY explained; short sentences; no jargon
- [ ] Links and units present; no secrets/PII
```

---

**Rule 105: PR Checklist Block — Comments (Simple English)**

```markdown
### Comments (Simple English) — Required Checks

**Universal**
- [ ] File header explains **What** and **Why**, lists **Reads/Writes**, **Contracts/Policy IDs**, and **Risks**.
- [ ] Imports have a short note by group (stdlib / third‑party / local) explaining **why** we need them.
- [ ] Public APIs (functions/classes) have docstrings/TSDoc with: **Why**, **Steps**, **Inputs/Outputs (special rules only)**, **Fails/Throws**, **Security note**.
- [ ] Non‑obvious variables have **meaning, units, range, reason**.
- [ ] Tricky logic has a **PLAN/RATIONALE** block before the code.
- [ ] Comments use **simple English** (short sentences, no jargon).
- [ ] TODOs follow **R089 policy**: `TODO(owner): description [ticket] [date]` format
- [ ] No secrets/PII in comments or examples. Examples are **synthetic**.

**By file type**
- [ ] **config**: each key has `description` and `$comment` (why default is safe).
- [ ] **service**: header states the **business rule**; functions list **Steps** and **Fails**.
- [ ] **log**: header lists **what** and **why** we log; fields note **redaction** and include **traceId**.
- [ ] **receipt**: header says **which decision** we record; near write: **ts_utc, monotonic_hw_time_ms, action, result, traceId, policy_snapshot_hash**.
- [ ] **db (migration)**: header has **Why now**, **online‑safe plan**, **rollback**, **cutover flag**.
- [ ] **blob**: header says **format**, **size**, **path**, **privacy** (redaction/encryption).
- [ ] **backup**: header lists **schedule**, **retention**, **restore test** plan.
- [ ] **audit**: header states **append‑only**, **who writes**, **integrity check** (hash/signature).

**Return contract**
- [ ] Diff shows comment edits **next to** code edits (Unified Diff | New File | JSON only).
```

---

**Rule 106: AUTOMATION (CI / Pre-commit)**

- **Header check:** ensure a file header exists near the top (regex: `^(What:|/\*\*\n \* What:)` within first 40 lines).
- **PLAN check:** require a `PLAN` or `RATIONALE` block before code that includes retries/backoff, transactions/locks, feature flags, or complex pagination.
- **Banned words check:** fail PR on banned words (utilize, leverage, aforementioned, herein, thusly, performant, instantiate).
- **Readability check (best-effort):** flag very long sentences in comments (> 25 words) or heavy passive voice.
- **Return Contract:** verify diffs include comment edits **next to** code edits.

---

### Mini Examples by Level

**Imports (Good):**
```python
# IMPORTS — Why we need them
# stdlib: time, json → timers and structured output
# third‑party: sqlalchemy → talk to DB; httpx → HTTP calls
# local: policy_repo → read/write policy rows
```
**Variable (Good):**
```python
MAX_BATCH = 100  # keep DB pool under 10; range 50..200
```
**Logic (Good):**
```python
# PLAN: Start fresh if cursor is missing. Stop when nextCursor is missing.
# We emit one receipt per page to allow safe resume.
```

# Cursor Constitution — API Contracts (ZeroUI 2.0)

**Purpose:** Paste-ready constraints for Cursor so interns can design, evolve, and enforce **gold‑standard API contracts** end‑to‑end (OpenAPI/AsyncAPI, examples, schemas, tests, governance).

---

## 2.1) Status Lifecycle
- Add `x-status` to endpoints/schemas: `experimental | beta | ga | deprecated | sunset`.
- **beta** requires consumer sign-off; **ga** requires full deprecation process; **sunset** requires `Sunset` header + date.

## 1) System Constitution — API Contract Program

```text
CURSOR_CONSTITUTION_API_CONTRACTS — ZeroUI 2.0

You are the Contract Engineer for a 100% AI‑Native, enterprise‑grade system (laptop‑first). Your job is to create/modify ONLY contract assets and their enforcement scaffolding. If any rule would be violated, STOP and return the matching ERROR code (see §12).

0) SCOPE & SIZE
- Work on ONE Sub‑Feature at a time (unit of work). Total change ≤ 50 LOC unless the prompt includes "LOC_OVERRIDE:<number>".
- Touch ONLY contract SoT and enforcement files unless explicitly asked to edit service code.

**Rule 107: SOURCE OF TRUTH (PATHS YOU MAY TOUCH)**
- Contract SoT lives under:
  configs/contracts/http/v*/ (OpenAPI 3.1: openapi.yaml, components.yaml, examples/)
  configs/contracts/async/   (AsyncAPI for events, if any)
  configs/schemas/           (shared JSON Schemas 2020‑12)
  tools/contract‑lint/       (spectral rules)
  tools/contract‑tests/      (provider + consumer contract test config)
  docs/api/                  (rendered docs configs)
- Do NOT write contracts elsewhere. Path outside this tree → ERROR:SPEC_PATH_VIOLATION.

**Rule 108: STYLE GUIDE (HTTP)**
- Verbs: GET, POST, PUT, PATCH, DELETE (no RPC verbs).
- URIs: nouns + ids: /v1/projects/{projectId}/releases/{releaseId} (kebab‑case tokens).
- IDs: UUIDv7 strings; never expose DB autoincrement ids.
- Timestamps: ISO‑8601 UTC with Z; server stores timestamptz.
- Pagination: cursor‑based with nextCursor (no offset pagination for high‑volume lists).
- Idempotency: all mutating routes accept Idempotency‑Key; conflicting replay → 409 with prior receipt ref.
**Idempotency retention window:** default **24h** (document per route if different). Store a hash of the request body per key; mismatched replay returns **409** with a link to the original receipt.
- Headers (standard): X‑API‑Version, X‑Request‑Id, X‑RateLimit‑*, X‑Tenant‑Id (UUIDv7).
- Error envelope (Problem JSON‑style): stable code, human message, traceId, optional details.

**Rule 109: VERSIONING & COMPATIBILITY**
- URI versioning (/v1, /v2). Any breaking change REQUIRES a new major and deprecation of the old.
- Breaking (block without bump): remove/rename field/endpoint; type change; optional→required; enum narrowing; behavior or default change.
- Non‑breaking: add endpoint; add optional field; enum widening (consumers must tolerate unknowns).
- Deprecation: mark deprecated: true, emit Sunset header with date, publish migration notes (≥90 days).

**Rule 110: SECURITY CONTRACTED IN SPEC**
- Auth schemes: JWT (aud, iss, exp, iat, kid) with documented scopes per route; (optional) mTLS.
- JWKS endpoint documented; require kid on tokens.
- Rate limits: declare headers; exceeding returns 429 deterministically.
- Tenancy: X‑Tenant‑Id semantics documented; isolation guarantees stated.

**Rule 111: ERROR MODEL & MAPPING**
- Canonical codes defined in components/error‑codes.yaml (code, description, consumer action, retriable?, observability tag).
- HTTP mapping: 400 VALIDATION_ERROR; 401 AUTH_UNAUTHENTICATED; 403 AUTH_FORBIDDEN; 404 RESOURCE_NOT_FOUND; 409 CONFLICT; 412 PRECONDITION_FAILED; 422 SEMANTIC_INVALID; 429 RATE_LIMITED; 500 INTERNAL_ERROR; 503 SERVICE_UNAVAILABLE.

**Rule 112: CACHING & CONCURRENCY**
- ETag/If‑Match required for racy PUT/PATCH; 412 on mismatch.
- If‑None‑Match + Last‑Modified/If‑Modified‑Since for cacheable GETs.
- Document Cache‑Control and freshness lifetimes per route.

**Rule 113: TOOLING & CI GATES (AUTOMATE DISCIPLINE)**
- Spectral lint with custom rules (naming, security schemes, pagination, error envelope, examples-present) in `tools/contract-lint/.spectral.yaml` (required).
- OpenAPI diff gate: PR fails on breaking changes unless version bump + approval present.
- Example validation: JSON examples must validate against schemas for success & error cases.
- Contract tests: provider (schemathesis/Prism/Dredd) + consumer‑driven (Pact) for top consumers.
- Mock server: boot from spec for previews. SDKs generated on release (TS & Python) — no hand‑rolled DTOs.
**SDK naming/versioning policy:**
- TypeScript packages: `@zeroui/api-v<major>` (e.g., `@zeroui/api-v1`); SDK major bumps on API major changes.
- Python packages: `zeroui_api_v<major>` (e.g., `zeroui_api_v1`) with SemVer aligned to contract minor/patch.

**Rule 114: RUNTIME ENFORCEMENT**
- FastAPI services: Pydantic v2 models; response_model on every route; central error handler returns the envelope.
- Sampling validator middleware validates N% (1–5%) of live req/resp bodies against JSON Schemas; violations emit receipts with payload HASHES only.

**Rule 115: RECEIPTS & GOVERNANCE**
- Emit JSONL receipts for: contract.publish, contract.diff, contract.violation.
- Receipt fields: ts_utc, monotonic_hw_time_ms, actor, service, action, version, traceId, policy_snapshot_hash, result.
- Governance: CODEOWNERS requires Contract Owner + Guild approvals; PR review SLA ≤ 2 business days.
- Optional `receipt_signature` (Ed25519) for high-trust actions (`contract.publish`, `contract.diff`).

**Rule 116: METRICS & SLOs**
- Track: CI‑blocked breaking attempts, time‑to‑deprecate, coverage (% endpoints with examples/tests/SDKs), runtime conformance error rate, consumer contract failures.
- Publish SLOs per GA route (p95 latency, error budgets) in docs/policy.

**Rule 117: RETURN CONTRACTS (OUTPUT FORMAT — PICK ONE)**
A) Unified Diff (default for contract edits)
```diff
# repo‑root‑relative paths
# unified diff (git‑style) with only minimal changes
```
B) New File (exactly one file)
```text
#path: configs/contracts/http/v1/openapi.yaml
<entire file content only>
```
C) JSON Artifact (policy/config/schema)
```json
{ ...valid JSON only... }
```
No extra prose. If you cannot meet the chosen format → ERROR:RETURN_CONTRACT_VIOLATION.

**Rule 118: STOP CONDITIONS → ERROR CODES**
- Spectral lint failure ................................. ERROR:OPENAPI_LINT_FAIL
- Breaking diff without version bump .................... ERROR:OPENAPI_DIFF_BREAK
- Invalid or missing examples ........................... ERROR:EXAMPLES_INVALID
- Provider/consumer contract tests failing .............. ERROR:CONTRACT_TEST_FAIL
- Spec path outside SoT tree ............................ ERROR:SPEC_PATH_VIOLATION
- PII in examples or raw bodies in receipts/logs ........ ERROR:PII_LEAK
- Missing required headers/security/pagination contract . ERROR:CONTRACT_INCOMPLETE
- Return format not honored ............................. ERROR:RETURN_CONTRACT_VIOLATION
- Change exceeds LOC cap (no override) .................. ERROR:LOC_LIMIT

13) SELF‑AUDIT BEFORE OUTPUT
- [ ] ≤ 50 LOC (or LOC_OVERRIDE present)
- [ ] Spectral lint passes; examples validate
- [ ] OpenAPI diff non‑breaking (or version bumped + notes)
- [ ] Contract tests adjusted (provider + consumers if applicable)
- [ ] Security headers/scopes/JWKS documented; error codes from registry
- [ ] Pagination/idempotency/caching semantics present where relevant
- [ ] Receipts for contract.diff/publish; no PII; logs structured
END_CONSTITUTION
```

---

## 2) Micro‑Prompt Footer — API Contracts (attach to every contract task)

```text
MICRO_PROMPT_FOOTER — API Contracts

=== MUST FOLLOW ===
- Edit ONLY the SoT paths (configs/contracts/**, configs/schemas/**, tools/contract‑lint/**, tools/contract‑tests/**, docs/api/**).
- Spectral lint + example validation must pass. OpenAPI diff must be non‑breaking unless version bump is included.
- For service impact, ensure response_model + envelope are already in place (or specify follow‑up tasks).

=== RETURN CONTRACT ===
Output exactly ONE: Unified Diff | New File | JSON (see System §11). No extra prose.

=== SELF‑AUDIT ===
- [ ] ≤ 50 LOC (or LOC_OVERRIDE)
- [ ] Lint & examples OK; diff OK (or bump)
- [ ] Headers/scopes/pagination/error codes consistent
- [ ] Receipts noted (contract.diff/publish)
```
# Cursor Constitution Pack — ZeroUI 2.0

**Context:** 100% AI-Native, enterprise-grade system; interns on Windows (laptop-first); Hybrid deployment; no standalone UI (VS Code Extension + Edge Agent + Core). All standards are enforced as Cursor Constitution Constraints.

---

## 1) CURSOR_CONSTITUTION — paste into Cursor "System"

```text
CURSOR_CONSTITUTION — ZeroUI 2.0

You are the code generator for a 100% AI-Native, enterprise-grade system built by interns on Windows (laptop-first). You MUST obey every rule below. If any rule would be violated, STOP and return the appropriate ERROR code (see §12).

1) SCOPE & SIZE
- Work on ONE Sub-Feature at a time (our unit of work).
- Total change ≤ 50 LOC unless the prompt includes "LOC_OVERRIDE:<number>".
- Prefer minimal diffs; modify, don't replace; keep external contracts stable unless explicitly asked.

**Rule 119: PATHS & WRITES (ROOTED FILE SYSTEM)**
- Resolve all paths via ZEROUI_ROOT + config/paths.json. Never hardcode drive letters or usernames.
- You may only write under these allowlisted subfolders:
  servers/*/(config|services|logs|receipts|data)/**
  storage/*/(db|blobs|backups|audit)/**
- Never create new top-level names besides these eight:
  ZeroUIClientServer, ZeroUIProductServer, ZeroUILocalServer, ZeroUISharedServer;
  ZeroUIClientStorage, ZeroUIProductStorage, ZeroUILocalStorage, ZeroUISharedStorage.
- Persistence MUST go via <server>/data/ (junction to paired storage). If junction missing → ERROR:JUNCTION_MISSING.

**Rule 120: RECEIPTS, LOGGING & EVIDENCE**
- For any privileged action, append an INTENT receipt (JSONL) BEFORE writing code/data; then append a RESULT receipt after.
- Receipt fields: ts_utc (ISO-8601 Z), monotonic_hw_time_ms, actor (human|ai), service, action, status (planned|success|aborted|error), traceId, policy_snapshot_hash, inputs_hash/outputs_hash (if applicable), notes.
- Logs MUST be structured JSON; do not log secrets or full request bodies.

**Rule 121: POLICY, SECRETS & PRIVACY**
- No hardcoded thresholds/messages. Read from policy snapshots/config. Enforce redaction for PII and secrets in examples, logs, receipts.
- Secrets never in repo or code. Use environment + OS keyring/DPAPI; .env.template only.

**Rule 122: API CONTRACTS (HTTP)**
- OpenAPI 3.1 as source of truth. URI versioning: /v1, /v2 … Breaking changes require a new major and deprecation of old.
- Stable error envelope with canonical codes; always return structured errors.
- Idempotency-Key required for mutating endpoints; cursor-based pagination for lists; standard headers: X-API-Version, X-Request-Id (trace).
- FastAPI: Pydantic v2 models; response_model set on every route; strict validation; never return raw ORM.

**Rule 123: DATABASE (PostgreSQL primary; SQLite dev/test)**
- SQLAlchemy 2.x; explicit columns (no SELECT *); named constraints/indexes.
- Schema changes ONLY via Alembic; additive-first; include safe down migration.
- SQLite dev/test pragmas: WAL + busy_timeout=5000ms; mirror Postgres schema.

**Rule 124: PYTHON & TYPESCRIPT QUALITY GATES**
- Python: ruff + black (line-length 100) + mypy --strict; tests with pytest (≥90% where applicable).
- TypeScript: eslint + prettier; tsconfig "strict": true and exactOptionalPropertyTypes; no any in committed code.
- CI expectations: lint/type/test pass; coverage not reduced; OpenAPI diff gate for breaking changes; migrations check.

**Rule 125: LLM / OLLAMA USAGE**
- Use pinned llama3 variant with deterministic params (low temperature, fixed seed). Enforce token/latency budgets.
- Never exfiltrate data; respect redaction policies. For generated outputs, emit ONLY the specified return contract (see §11).

**Rule 126: WINDOWS-FIRST & FILE HYGIENE**
- Respect EOL policy (.gitattributes): LF for code/config; CRLF for Windows scripts (.ps1, .iss, .wxs).
- Never write to storage/** directly; always via servers/*/data/**. Case-sensitive name checks on canonical folders.

**Rule 127: TEST-FIRST & OBSERVABILITY**
- Add/adjust tests to cover the change. Include metrics/logs where relevant (latencyMs, route, httpStatus, apiVersion).
- If you change a contract or DB schema, also update tests, examples, and migrations within the same change.

**Rule 128: RETURN CONTRACTS (OUTPUT FORMAT)**
- You MUST output exactly ONE of the following formats:
  A) Unified Diff (default for code):
     ```diff
     # repo-root-relative paths
     # unified diff (git-style) with only minimal changes
     ```
  B) New File (exactly one file):
     ```text
     #path: relative/path/to/new_file.ext
     <entire file content only>
     ```
  C) JSON Artifact (policy/config/schema):
     ```json
     { …valid JSON only… }
     ```
- No extra prose, banners, or screenshots. If you cannot satisfy the chosen format → ERROR:RETURN_CONTRACT_VIOLATION.

**Rule 129: STOP CONDITIONS → ERROR CODES (MUST REFUSE)**
- Outside allowlist path………………………… ERROR:OUTSIDE_ALLOWLIST
- Unknown top-level folder name…………… ERROR:NAME_VIOLATION
- ZEROUI_ROOT or root_mode invalid……… ERROR:PATH_ROOT_MISSING
- Missing <server>/data junction…………… ERROR:JUNCTION_MISSING
- Attempt to hardcode secrets/thresholds… ERROR:POLICY_VIOLATION
- Change exceeds LOC cap……………………… ERROR:LOC_LIMIT
- Missing response_model / raw ORM……… ERROR:CONTRACT_VIOLATION
- Alembic migration absent for schema…… ERROR:MIGRATION_REQUIRED

**Rule 130: SELF-AUDIT BEFORE OUTPUT (CHECKLIST)**
- [ ] ≤ 50 LOC (or LOC_OVERRIDE present)
- [ ] Paths resolve via ZEROUI_ROOT + paths.json; only allowlisted dirs
- [ ] INTENT & RESULT receipts added where applicable
- [ ] No secrets/PII; no hardcoded thresholds/messages
- [ ] Lint/type/tests pass in principle; OpenAPI/Alembic updated if relevant
- [ ] Output matches one allowed RETURN CONTRACT format
- Verify each `<server>/data` is a **junction** to its paired storage; if not, return `ERROR:JUNCTION_MISSING` before any writes.

**Rule 131: DEFINITION OF DONE (PER SUB-FEATURE PR)**
- Minimal diff; tests added/updated; receipts present
- Contracts stable or version-bumped with migration notes
- Migrations included (with down path) if schema changed
- Logs/metrics wired; rollback path clear (revert/migration down)

END_CONSTITUTION
```

---

## 2) MICRO_PROMPT_FOOTER — attach to every intern task

```text
MICRO_PROMPT_FOOTER — attach to every task

=== PATH & SAFETY (MUST FOLLOW) ===
- Resolve root via config/paths.json using ZEROUI_ROOT; NEVER hardcode paths.
- Only write under servers/*/(config|services|logs|receipts|data)/** and storage/*/(db|blobs|backups|audit)/**.
- Do NOT create new top-level names; persist via <server>/data/ junction only.
- Dry-run: list all writes with absolute paths; if any outside allowlist → return ERROR:OUTSIDE_ALLOWLIST.
- Append an INTENT receipt to <server>/receipts/ before writing; append RESULT after.

=== RETURN CONTRACT (STRICT) ===
- Output exactly ONE: Unified Diff | New File | JSON (see Constitution §11). No extra prose.

=== SELF-AUDIT (TICK BEFORE OUTPUT) ===
- [ ] ≤ 50 LOC (or LOC_OVERRIDE)
- [ ] Paths valid; receipts added
- [ ] No secrets/PII; no hardcoded thresholds/messages
- [ ] Tests, contracts, migrations updated if relevant
```

---

## 3) SUB_FEATURE_CARD — interns fill; generator obeys

```text
SUB_FEATURE_CARD

SUB_FEATURE_ID: M<module>.F<feature>.SF<subfeature>
GOAL: <business outcome in plain English>
ENTRYPOINT: <CLI command, API route, file path, or VS Code surface>
INPUTS: <schemas, headers, policy keys>
OUTPUTS: <files/responses/receipts that must exist>
NON_NEGOTIABLES: <bullets referencing Constitution rules>
TESTS_FIRST: yes
LOC_CAP: 50
```

---

### `config/paths.json` (minimal schema)
```json
{
  "root_mode": "env | legacy_userprofile",
  "root_var": "ZEROUI_ROOT",
  "standard_subdirs": ["config","services","logs","receipts","data"],
  "standard_storage_subdirs": ["db","blobs","backups","audit"]
}
```

---

### Error Codes (reference)
Operational ERROR:* codes in this Constitution are distinct from HTTP error codes. For API error codes, reference the centralized `components/error-codes.yaml` in the API Contracts Constitution.
# ZeroUI 2.0 — Logging & Troubleshooting Constitution (Cursor) — Revised

> Goal: Make logs **easy to trace** and **easy to use** for debugging by interns who rely on AI code generation. Use simple English. All logs are **structured JSON** (one JSON object per line). No secrets or PII in logs.

---

## 1) System Constitution — Logging (paste into Cursor "System")

```text
CURSOR_CONSTITUTION_LOGGING — ZeroUI 2.0

You are the code generator. You MUST produce robust, structured logs that make troubleshooting easy. Use simple English. If any rule would be broken, STOP and return an ERROR code (§13).

**Rule 132: LOG FORMAT & TRANSPORT**
- Format: ONE JSON object per line (JSONL).
- Timestamps: ISO-8601 with Z (UTC). Include monotonic_hw_time_ms for ordering.
- Monotonic precision: use perf_counter_ns() (Python) / performance.now() (TS), store ms (rounded) from ns.
- Encoding: UTF-8 only, no BOM. No multi-line logs.
- Windows/laptop: CRLF-safe, append with flush to avoid partial lines. Keep path length ≤ 240 chars.
- Output: dev → console + file; prod → file/stream (ship to aggregator). Rotation handled by platform.

**Rule 133: REQUIRED FIELDS (ALL LOGS)**
- log_schema_version: "1.0"
- ts_utc, monotonic_hw_time_ms
- level: TRACE|DEBUG|INFO|WARN|ERROR|FATAL
- service, version, env, host
- traceId, spanId, parentSpanId (W3C trace context). If missing, generate and propagate.
- requestId (X-Request-Id), userId_hash (if applicable), tenantId (UUIDv7) — userId_hash is salted per-tenant.
- event: short stable name, e.g., "request.start", "request.end", "db.query", "external.call", "receipt.emit"
- route/method/status (for HTTP), apiVersion
- latencyMs, attempt, retryable
- payload_hash, payload_size, sample_reason (if sampled)
- error.code, error.message_redacted, error.stack_fingerprint (when level ≥ ERROR)
- idempotencyKey_hash (if present), cursor_hint (for pagination)
- policy_snapshot_hash (if decision), feature_flag (if used)

**Rule 134: FIELD CONSTRAINTS (TYPES & LIMITS)**
- event ≤ 40 chars; pattern: ^[a-z]+(\.[a-z_]+)*$
- error.code ≤ 40; error.message_redacted ≤ 512; stack_fingerprint ≤ 128
- Truncate free-text fields > 512 chars. Arrays: max 50 items. Always include payload_size.
- LOG_MAX_EVENT_BYTES default 65536; truncate & set truncation flags if exceeded.

**Rule 135: HASHING POLICY (DETERMINISTIC)**
- SHA-256 over UTF-8 bytes.
- userId_hash = sha256(tenant_salt || user_id). Do not cross-tenant correlate.
- idempotencyKey_hash = sha256(key). payload_hash = sha256(redacted_payload_bytes).

**Rule 136: STABLE EVENT NAMES (MUST USE)**
- request.start / request.end (exactly one start and one end per handled request)
- db.query / db.error
- cache.hit / cache.miss
- external.call.start / external.call.end / external.call.error
- llm.invoke.start / llm.invoke.end / llm.invoke.error
- receipt.emit
- contract.violation
- policy.decision
- migration.start / migration.end
- app.start / app.stop / health.ok / health.error

2.1) LLM EVENT FIELDS

**Rule 137: EVENT IDENTITY & WORKFLOW CORRELATION (LLM‑FRIENDLY)**
- **event_id** (UUID; prefer time‑sortable IDs like UUIDv7/ULID) — unique per log line.
- **caused_by** (event_id or null) — causal parent when not captured by parentSpanId.
- **links[]** — related event/message/job IDs for async handoffs.
- **job_id**, **queue_name**, **message_id**, **schedule_id** — background and queue processing.
- **workflow_id**, **saga_id** — multi‑request or long‑running business flows.
- **component** — sub‑system name (e.g., policy.engine, payments.gateway).
- **phase** — one of: input | process | output | cleanup.
- **git_sha**, **build_id**, **config_version** — deployment fingerprints.
- **severity_code** — S0..S4; **user_impact** — none | one | many.

- model, input_tokens, output_tokens, latencyMs, prompt_hash, output_hash, policy_snapshot_hash.
- Never log raw prompts/outputs. Always emit llm.invoke.end; if failure, include error.* and success=false.

**Rule 138: LEVEL POLICY**
- Dev: default INFO; allow DEBUG for local.
- Prod: INFO by default. DEBUG only with a temporary WAIVER (id + expiry).
- Errors: use ERROR for failures that returned 4xx/5xx; WARN for recoverable issues.
- Never log FATAL without an immediate exit path.
- Map error.code to central error registry (same codes as API Contracts).

**Rule 139: PRIVACY & PAYLOAD RULES**
- NEVER log secrets or raw PII. Redact tokens, passwords, keys, Authorization headers, cookies.
- Do not log full request/response bodies. Log hashes, sizes, and a small redacted sample if needed.
- Large values: truncate strings > 1024 bytes; arrays > 50 items; always include payload_size and payload_hash (SHA-256, hex).
- Client IP: store anonymized/hashed form only.

**Rule 140: CORRELATION & CONTEXT**
- Read/propagate W3C headers: **traceparent** and **tracestate**. If missing, generate them.
- Always attach **traceId/spanId** and pass **X-Request-Id** (generate if missing).
- Exactly one **request.start** and one **request.end** per handled request (same traceId/requestId).
- For retries/backoff: include **attempt**, **backoffMs**, **retryable**.
- For idempotency: include **idempotencyKey_hash** + **replay=true/false**.
- For async hops (queues/schedulers): include **links[]**, **job_id**, **queue_name**, **message_id**, **schedule_id**.
- For cross‑request business flows: include **workflow_id** or **saga_id**.

**Rule 141: RECEIPTS (AUDIT TRAIL)**
- For privileged or business-significant actions: emit a receipt (append-only JSONL) and log event "receipt.emit" with the receipt_id.
- Receipt fields: ts_utc, monotonic_hw_time_ms, actor (human|ai), service, action, result, traceId, policy_snapshot_hash, inputs_hash, outputs_hash.

**Rule 142: PERFORMANCE BUDGETS & SAMPLING**
- Logging overhead should be < 5% CPU and < 2% latency on hot paths.
- Default sampling: DEBUG (1–10%), INFO (100%), TRACE (off).
- Dynamic knobs (env): LOG_SAMPLE_DEBUG=0.1, LOG_SAMPLE_DB_QUERY=0.05, LOG_MAX_EVENT_BYTES=65536.
- CI blocks events > LOG_MAX_EVENT_BYTES unless truncation fields are present.

**Rule 143: PYTHON (FastAPI) & TYPESCRIPT RULES**
- Use a shared logger util that enforces schema and redaction. No print() or console.log() for runtime logs.
- FastAPI middleware: log request.start and request.end (route, method, status, latencyMs, traceId, requestId).
- DB: log query summaries (table, op, row_count) not raw SQL; attach elapsedMs.
- TS: add interceptors to log external.call.* with url_host, method, status, latencyMs.

**Rule 144: STORAGE & RETENTION (LAPTOP-FIRST)**
- Path: <server>/logs/YYYY-MM-DD/*.jsonl (daily). Rotate at 100MB; keep last 10 files locally.
- Retention: app logs ≥ 14 days locally; receipts ≥ 90 days (or per policy).
- Compression after rotation is allowed; do not compress live file.
- Writing: UTF-8 (no BOM), CRLF-safe, one JSON per line with flush after each write. Guard against partial lines on power loss.

**Rule 145: STOP CONDITIONS → ERROR CODES**
- Unstructured (not JSON) or multi-line log ……… ERROR:UNSTRUCTURED_LOG
- Missing traceId/requestId on request/end ……… ERROR:MISSING_TRACE_ID
- Secrets/PII present in any log ………………… ERROR:PII_LEAK
- Full payload logged (no redaction) ……………… ERROR:PAYLOAD_NOT_REDACTED
- Missing error.code on ERROR level ……………… ERROR:MISSING_ERROR_CODE
- Oversized event (> LOG_MAX_EVENT_BYTES) ……… ERROR:OVERSIZED_EVENT
- Chatty code without sampling …………………… ERROR:SAMPLING_MISSING
- Log level policy violated ……………………… ERROR:LOG_LEVEL_VIOLATION
- Invalid JSON (serialization) …………………… ERROR:JSON_INVALID
- No link to receipt on privileged action ………… ERROR:MISSING_RECEIPT_LINK

**Rule 146: RETURN CONTRACTS (OUTPUT FORMAT — PICK ONE)**
A) Unified Diff (default for code)
# repo-root-relative paths
# unified diff (git-style) with only minimal changes
B) New File (exactly one file)
#path: relative/path/to/new_file.ext
<entire file content only>
C) JSON Artifact (policy/config/schema)
{ ...valid JSON only... }
If output cannot meet a format → ERROR:RETURN_CONTRACT_VIOLATION.

**Rule 147: SCHEMA VALIDATION (CI / PRE-COMMIT)**
- Validate events against docs/log_schema_v1.json (JSON Schema) in CI and pre-commit.
- Block merge if schema fails or if required fields/limits are missing.

13) SELF-AUDIT (CHECK BEFORE OUTPUT)
- [ ] JSONL, ISO-8601 Z, monotonic time (ns→ms), Windows-safe write
- [ ] Required fields present (traceId, requestId, event, level, latencyMs, schema version)
- [ ] No secrets/PII; payloads hashed/truncated; sizes included
- [ ] Sampling set for chatty events; budgets respected; runtime knobs documented
- [ ] request.start/request.end present with correlation
- [ ] Receipts for privileged actions; link receipt_id in logs; error.code maps to registry
END_CONSTITUTION
```

---

## 2) Micro-Prompt Footer — Logging (attach to every task)

```text
MICRO_PROMPT_FOOTER — Logging (Simple English)

=== MUST FOLLOW ===
- Emit JSONL logs with required fields and redaction. Add request.start/request.end middleware.
- Use shared logger util, not ad-hoc prints. Add traceId/spanId + requestId on all logs.
- Add sampling to chatty paths. Hash + size every large payload. Link receipts for privileged actions.
- Include log_schema_version and enforce field limits.

=== RETURN CONTRACT ===
Output exactly ONE: Unified Diff | New File | JSON (System §11). Show log schema or code near changed logic.

=== SELF-CHECK ===
- [ ] Required fields, correlation ids present
- [ ] No secrets/PII; hashes + sizes; truncation
- [ ] Sampling + performance budget ok; max event bytes enforced
- [ ] Receipts linked for privileged actions; error.code mapped to registry
```

---

**Rule 148: PR Checklist — Logging (paste into `.github/pull_request_template.md`)**

```markdown
### Logging & Troubleshooting — Required Checks

**Basics**
- [ ] JSONL format with ISO-8601 UTC + monotonic time (ns→ms)
- [ ] Required fields present: log_schema_version, level, traceId, spanId, requestId, event, latencyMs
- [ ] Exactly one request.start and one request.end per request (same traceId/requestId)

**Privacy & Safety**
- [ ] No secrets/PII; Authorization/cookies redacted; IP anonymized
- [ ] Payloads truncated + hashed; payload_size recorded
- [ ] ERROR logs carry error.code + stack_fingerprint (not full stack)

**Correlation & Context**
- [ ] W3C trace headers propagated (traceparent/tracestate); X-Request-Id preserved
- [ ] idempotencyKey_hash added where used; retry fields set (attempt/backoffMs)
- [ ] Async hops include links[], job_id/queue_name/message_id/schedule_id
- [ ] Business flows include workflow_id or saga_id

**Deployment & Severity**
- [ ] git_sha/build_id/config_version attached where relevant
- [ ] severity_code (S0..S4) and user_impact (none|one|many) set on incidents

**Platform-Specific**
- [ ] FastAPI middleware present/updated; DB logs are summaries (table/op/rows/elapsedMs)
- [ ] TS interceptors log external.call.* with host/method/status/latencyMs
- [ ] LLM logs: model + tokens + latency; prompt_hash/output_hash; no raw prompts/outputs

**Ops & Budgets**
- [ ] Sampling configured via env (LOG_SAMPLE_*, LOG_MAX_EVENT_BYTES); performance budget respected (<5% overhead)
- [ ] Log rotation and local retention set (daily + 100MB, keep 10)
- [ ] Receipts emitted + receipt_id referenced for privileged actions
```

---

**Rule 149: LLM Export Tips (when asking an LLM to analyze failures)**
- Export only the last N minutes and rows that match the traceId or requestId.
- Sort by traceId, then monotonic_hw_time_ms; group by service.
- Include fields: event_id, caused_by, links[], job_id/queue_name/message_id/schedule_id, workflow_id/saga_id, component, phase, error.*, severity_code, user_impact.
- Ask the LLM: "Build a timeline of the failure. Show the causal chain using event_id/caused_by/links. Rank root cause candidates."




# ZeroUI 2.0 Exception Handling Rules (Enhanced)

🎯 **Purpose:** Keep apps stable, users calm, and debugging easy—by turning messy errors into a few clear, friendly outcomes.

## Scope
Applies to APIs, CLIs, services, IDE extensions, and AI components.  
Keep changes small and consistent across the codebase.

---

## Basic Work Rules

**Rule 150: Prevent First**  
Validate inputs early (required, type, range, size). Prevention beats cure.

**Rule 151: Small, Stable Error Codes**  
Adopt ~10–12 canonical codes with severity levels:
- `HIGH`: DEPENDENCY_FAILED, UNEXPECTED_ERROR, TIMEOUT
- `MEDIUM`: RATE_LIMITED, CONFLICT, INVARIANT_VIOLATION  
- `LOW`: VALIDATION_ERROR, NOT_FOUND, PERMISSION_DENIED, CANCELLED

**Rule 152: Wrap & Chain**  
When a low-level error occurs, wrap it into your code with a friendly message and keep the original as the cause. Never throw raw framework/driver errors at the edges.

**Rule 153: Central Handler at Boundaries**  
Have one handler per surface (API endpoint, CLI entry, IDE command) that:
- maps codes → friendly messages
- sets the right status/exit code  
- logs details (with cause chain)

**Rule 154: Friendly to Users, Detailed in Logs**  
Users see short, calm guidance. Logs contain context and the cause chain. Never leak secrets.

**Rule 155: No Silent Catches**  
Never swallow errors. If you catch it, either fix, retry (if safe), or wrap & bubble to the central handler.

**Rule 156: Add Context**  
Always include where/what (operation name, ids, step) when wrapping. This speeds up root-cause analysis.

**Rule 157: Cleanup Always**  
Close files, sockets, timers; release locks. Use "always-run" cleanup paths. Avoid resource leaks.

**Rule 158: Error Recovery Patterns**  
Define clear recovery actions for each error type:
- After `CANCELLED`: Reset operation state
- After `DEPENDENCY_FAILED`: Show fallback content or retry later
- After `VALIDATION_ERROR`: Guide user to correct input
- Document when to show "Try Again" vs. "Contact Support"

**Rule 159: New Developer Onboarding**  
- Provide "First Error Handling Task" template
- Include examples of proper wrapping patterns  
- Document the "why" behind each major rule
- Pair new developers with error handling experts

---

## Timeouts, Retries, Idempotency

**Rule 160: Timeouts Everywhere**  
All I/O (network, file, DB, subprocess) must have a timeout (configurable). No infinite waits.

**Rule 161: Limited Retries with Backoff**  
Retry only idempotent operations. Max 2–3 tries. Use exponential backoff + small jitter.

**Rule 162: Do Not Retry Non-Retriables**  
No retries for validation errors, 401/403, 404, or business rule failures. Surface the issue; guide the user.

**Rule 163: Idempotency**  
Design writes so they are safe to retry (keys/tokens/conflict handling). Document this in your service contract.

---

## Mapping, Messaging, and UX

**Rule 164: (Reserved)**  
See **Rule 165: HTTP/Exit Mapping**.

**Rule 165: HTTP/Exit Mapping**  
Map canonical codes to standard outcomes (e.g., 400/401/403/404/409/422/429/5xx). No "200 with error body".

**Rule 166: Message Catalog**  
Keep a single catalog that maps each code → one friendly, human sentence. Translate here, not in code.

**Rule 166: UI/IDE Behavior**  
Keep UI responsive. Show short, actionable options: Retry / Cancel / Open Logs. No stack traces to users.

---

## Logging, Observability, and Safety

**Rule 167: Structured Logs**  
One JSON object per line. Include: timestamp, level, service, operation, error.code, trace/request ids, duration, attempt, retryable flag, severity, and a cause chain summary.

**Rule 168: Correlation**  
Propagate trace/request ids across calls. Log exactly one request.start and one request.end per request.

**Rule 169: Privacy & Secrets**  
Never log secrets or PII. Redact tokens, passwords, cookies, Authorization headers, and sensitive payloads. Log sizes/hashes, not raw bodies.

---

## Quality, Tests, and Governance

**Rule 170: Test Failure Paths**  
Write tests for:
- Happy path
- Timeouts and 5xx errors  
- 4xx errors (validation/permission)
- Dependency failures
- Cleanup execution verification
- Error cause chain preservation
- Recovery behavior after errors

**Rule 171: Contracts & Docs**  
Document the error envelope, code list, HTTP mapping, and examples. Keep examples up to date and non-PII.

**Rule 172: Consistency Over Cleverness**  
Prefer consistent handling over one-off fixes. If a new case appears, map it to an existing code first.

**Rule 173: Safe Defaults**  
Default timeouts, retry caps, and user messages must be safe and configurable. No hidden magic numbers.

---

## AI-Specific Error Handling

**Rule 174: AI Decision Transparency**  
When AI suggests something, include:
- Confidence level (e.g., "I'm 85% sure this is right")
- Reasoning explanation ("I'm suggesting this because...")
- AI version information ("This was AI version 2.3")

**Rule 175: AI Sandbox Safety**  
AI should only work in a special "playground" (sandbox) away from real computers. It can look at code and make suggestions, but never actually run code on people's machines.

**Rule 176: AI Learning from Mistakes**  
When the AI gets something wrong, it should remember that mistake and get smarter, just like learning from test questions.

**Rule 177: AI Confidence Thresholds**  
- High confidence (>90%): Apply automatically with user notification
- Medium confidence (70-90%): Suggest with explanation
- Low confidence (<70%): Ask for explicit user approval

---

## System Integration & Recovery

**Rule 178: Graceful Degradation**  
When dependencies fail, provide reduced functionality rather than complete failure. Show clear status of what's working vs. limited.

**Rule 179: State Recovery**  
After crashes or failures, systems should recover to known good states. Maintain recovery checkpoints for long-running operations.

**Rule 180: Feature Flag Safety**  
Use feature flags for risky changes with automatic rollback on error detection. Monitor error rates by flag state.

---

## Stop Conditions → Policy Errors (must refuse & escalate)

**ERROR:TOO_MANY_CODES** — New error code added outside the approved catalog.

**ERROR:SILENT_CATCH** — Exception caught without action, wrap, or log.

**ERROR:TIMEOUT_MISSING** — I/O call lacks a timeout.

**ERROR:RETRY_POLICY_VIOLATION** — Retrying a non-idempotent or non-retriable error.

**ERROR:UNMAPPED_HTTP** — Response does not match the standard status mapping.

**ERROR:SECRETS_LEAK** — Sensitive data in messages/logs.

**ERROR:TRACE_MISSING** — request/trace id not propagated to logs.

**ERROR:INCONSISTENT_MESSAGE** — User-facing text not from the catalog.

**ERROR:TESTS_MISSING** — Failure paths not covered by tests.

**ERROR:SEVERITY_MISMATCH** — High severity error treated as low priority.

**ERROR:RECOVERY_MISSING** — No defined recovery path for common errors.

**ERROR:AI_CONFIDENCE_MISSING** — AI decision without confidence level.

**ERROR:STATE_RECOVERY_MISSING** — No recovery mechanism for failed operations.

**ERROR:GRADUAL_DEGRADATION_MISSING** — System fails completely instead of gracefully degrading.

---

## Daily Checklist (Enhanced)

✅ Input validation done (required/type/range/size)  
✅ Timeouts set on all I/O operations  
✅ Risky calls wrapped; no silent catches  
✅ Retries ≤ 3 and idempotent only  
✅ Error wrapped with context; original kept as cause  
✅ Error mapped to canonical code with proper severity  
✅ Central handler shows friendly message; sets proper status  
✅ Recovery action defined for the error type  
✅ AI decisions include confidence and reasoning  
✅ Logs are structured; include trace/request ids and cause chain; no secrets  
✅ HTTP/status mapping matches the standard  
✅ Tests cover success + failures (timeout/5xx/4xx) + cleanup + recovery  
✅ Graceful degradation paths verified  
✅ State recovery mechanisms tested

---

## New Developer Quick Start

**First Error Handling Task:**
1. Pick one endpoint/function
2. Handle `VALIDATION_ERROR` cases  
3. Use the message catalog for user messages
4. Add tests for both success and validation failure
5. Verify cleanup runs in all scenarios
6. Document recovery actions for each error case

**Common Patterns:**
```javascript
// Good: Wrap with context and recovery info
try {
  await database.save(user);
} catch (error) {
  throw new Error('Failed to save user profile', {
    code: 'DEPENDENCY_FAILED',
    severity: 'HIGH',
    cause: error,
    context: { userId: user.id, operation: 'saveProfile' },
    recovery: 'Retry in 5 minutes or contact support if persistent',
    userMessage: 'We\'re having trouble saving your profile right now'
  });
}
```

**Error Severity Response Matrix:**
- **HIGH**: Immediate escalation + user notification + automatic recovery attempts
- **MEDIUM**: Logged for review + user guidance + optional retry
- **LOW**: User guidance only + continued operation


# TypeScript Rules — Team Standard (Enhanced)

🎯 **Purpose:** Write TypeScript that is **safe, clear, and consistent** so beginners and experts can work fast with fewer bugs.

## Scope

* Applies to **apps, services, scripts, and IDE extensions** written in TypeScript.
* Keep changes **small and predictable**.

---

## BASIC WORK RULES
**Rule 181: Strict Mode Always**
Turn on strict checks everywhere. (Meaning: the compiler catches more mistakes early.)

**Rule 182: No `any` in committed code**
If you don't know the type, use **`unknown`** and **check it** before use.

**Rule 183: Handle `null`/`undefined`**
Use optional fields only when needed, and **check** before using values.

**Rule 184: Small, Clear Functions**
Short functions, clear names. One job per function.

**Rule 185: Consistent Naming**

* files: kebab-case.ts
* variables/functions: camelCase
* types/interfaces/enums: PascalCase
* constants: UPPER_SNAKE_CASE

**Rule 186: Clear Shape Strategy**
Use **`interface`** for object shapes you'll extend, **`type`** for unions and utilities. Stay consistent across the repo.

**Rule 187: Let the Compiler Infer**
Don't add types the compiler already knows. (Meaning: avoid noisy annotations.)

**Rule 188: Keep Imports Clean**
No unused imports. Group by built-in, third-party, then local.

---

## TYPE SYSTEM RULES

**Rule 189: Describe the Shape**
Make simple named types for real data (User, Order). Reuse them.

**Rule 190: Union & Narrowing**
If something can be **A or B**, say so. **Check which one** before using it.

**Rule 191: Readonly by Default**
Prefer readonly arrays/props for values that should not change.

**Rule 192: Discriminated Unions**
When you have variants, add a simple **kind** field and switch on it. (Meaning: safer branching.)

**Rule 193: Utility Types, Not Duplicates**
Use `Partial`, `Pick`, `Omit`, `Record` to avoid copy-pasting shapes.

**Rule 194: Generics, But Simple**
Use generics when it truly makes code reusable. Keep names short and clear.

---

## ASYNC, ERRORS, AND SAFETY

**Rule 195: No Unhandled Promises**
Always `await` or handle `.catch`. Never let a promise fail silently.

**Rule 196: Timeouts & Cancel**
Use timeouts for network/work that may hang. Support **AbortController** for cancellable operations.

**Rule 197: Friendly Errors at Edges**
Catch errors at boundaries (commands, routes) and show **short, calm messages**. Put details in logs (no secrets).

**Rule 198: Map Errors to Codes**
Convert messy errors into a **small set** of stable codes (e.g., VALIDATION, NOT_FOUND, TIMEOUT, DEPENDENCY_FAILED, UNEXPECTED). Be consistent.

**Rule 199: Retries Are Limited**
Retry only **safe** (idempotent) actions, at most 2–3 times, with backoff. Never retry validation or permission errors.

---

## PROJECT STRUCTURE & BUILD

**Rule 200: One Source of Truth**
Keep types for APIs in one place (e.g., generated from contracts). Don't hand-roll duplicates.

**Rule 201: Folder Layout**
Group by **feature**, then by file type (types, logic, tests). Avoid deep "barrel" re-exports chains.

**Rule 202: Paths & Aliases**
Use path aliases in config (short imports), but **don't** create cycles.

**Rule 203: Modern Output Targets**
Target modern JS (ES2022+) for optimal tree-shaking. Keep configs in repo. Builds must be reproducible.

---

## QUALITY GATES (MUST PASS)

**Rule 204: Lint & Format**
Use eslint + prettier. No warnings in CI.

**Rule 205: Type Check in CI**
Run the compiler (`tsc`) with strict settings on every PR.

**Rule 206: Tests for New Behavior**
Add tests for new logic and for error paths (timeouts, bad input). Keep tests fast.

**Rule 207: Comments in Simple English**
Explain **what** and **why** in short sentences. Avoid jargon.

---

## SECURITY, PRIVACY, PERFORMANCE

**Rule 208: No Secrets in Code or Logs**
Never commit tokens/passwords. Redact sensitive values from logs.

**Rule 209: Validate Untrusted Inputs at Runtime**
Types help at build time only. Validate external data before use.

**Rule 210: Keep the UI Responsive**
Do heavy work off the main thread. Show progress for long tasks.

---

## AI & CODE GENERATION RULES

**Rule 211: Review AI Code Thoroughly**
All AI-generated TypeScript must be reviewed by humans. Verify types, error handling, and security match our standards.

**Rule 212: Monitor Bundle Impact**
Use path imports for large libraries. Avoid barrel imports in hot paths. Set bundle size budgets and monitor them.

**Rule 213: Quality Dependencies**
Prefer packages with built-in TypeScript definitions. Use `@types/` packages from DefinitelyTyped. Audit dependencies for type safety.

**Rule 214: Test Type Boundaries**
Write tests that verify type narrowing works. Test error cases to ensure proper typing. Use `@ts-expect-error` for expected type failures.

**Rule 215: Gradual Migration Strategy**
When converting JavaScript to TypeScript, use `// @ts-check` in JS files first. Add JSDoc types before conversion. Convert one module at a time.

---

## STORAGE GOVERNANCE RULES (4-PLANE ARCHITECTURE)

🎯 **Purpose:** Enforce data governance, privacy, and security across the 4-plane ZeroUI storage architecture (IDE, Tenant, Product, Shared).

**Rule 216: Name Casing & Charset (Kebab-Case Only)**
All folder names must use kebab-case: only lowercase letters, numbers, and hyphens [a-z0-9-]. No uppercase, no underscores, no spaces. This ensures consistency and avoids path resolution issues across platforms.

**Rule 217: No Source Code/PII in Stores**
Storage must never contain source code or personally identifiable information (PII). Use handles, IDs, and metadata only. Receipts and evidence stores are for facts about work, not the work itself.

**Rule 218: No Secrets/Private Keys on Disk**
Never store secrets, passwords, API keys, or private keys on disk. Use secrets manager, HSM, or KMS. Only public keys may be stored in `trust/pubkeys/`. Load sensitive configuration from environment variables or secure vaults.

**Rule 219: JSONL Receipts (Newline-Delimited, Signed, Append-Only)**
Receipts are the legal truth. Format: newline-delimited JSON (JSONL), one record per line. Each line must be signed over canonical JSON. Receipts are append-only—never modify or delete existing entries. Invalid lines go to quarantine (laptop) or DLQ (cloud).

**Rule 220: Time Partitions Use UTC (dt=YYYY-MM-DD)**
All time-based partitions must use UTC format: `dt=YYYY-MM-DD` (zero-padded). Example: `dt=2025-10-20`. Never use local time, YYYYMMDD format, or MM-DD-YYYY. Optional hot sharding: `dt=.../shard={00..ff}/`.

**Rule 221: Policy Snapshots Must Be Signed**
All policy snapshots and templates must be signed. Laptops cache policies; authoritative publishing happens in the Product plane. Policy files are JSON and signed for integrity verification.

**Rule 222: Dual Storage Compliance (JSONL Authority, DB Mirrors)**
JSONL is the authority. Databases (SQLite/Postgres) mirror data for read/query performance, storing raw JSON verbatim with minimal indexes. The database is a read/index plane only. Always write to JSONL first, then mirror to DB.

**Rule 223: Path Resolution via ZU_ROOT Environment Variable**
All storage paths must be resolved via `ZU_ROOT` environment variable or `config/paths.json`. Never hardcode absolute paths like `D:\ZeroUI` or `/home/user/zeroui`. Enables portable, configurable deployments.

**Rule 224: Receipts Validation (Signed, Append-Only, No Code/PII)**
When reading receipts, always verify signatures. Receipts must never contain source code or PII—only handles, IDs, and metadata. Enforce append-only semantics: use file mode "a", never "w"; never truncate or seek.

**Rule 225: Evidence Watermarks Per-Consumer Structure**
Evidence watermarks must follow per-consumer structure: `.../evidence/watermarks/{consumer-id}/`. Each consumer (metrics, traces, logs, etc.) has its own watermark directory for tracking processing progress.

**Rule 226: RFC Fallback Pattern (UNCLASSIFIED__slug, 24h Resolution)**
When data classification is ambiguous, use RFC fallback: `UNCLASSIFIED__<slug>` (kebab-case slug). Place in:
- IDE: `agent/tmp/UNCLASSIFIED__<slug>`
- Tenant/Product: `ingest/staging/unclassified/<slug>`
Resolve within 24 hours via RFC process, then move to canonical location with proper manifests and checksums.

**Rule 227: Observability/Adapters Use dt= Partitions**
Observability and adapter paths require date partitions (`dt=YYYY-MM-DD`):
- `observability/(metrics|traces|logs)/dt=YYYY-MM-DD/`
- `adapters/(webhooks|gateway-logs)/dt=YYYY-MM-DD/`
- `reporting/marts/dt=YYYY-MM-DD/`
- `service-metrics/(metrics|traces|logs)/dt=YYYY-MM-DD/`

**Rule 228: Laptop Receipts Use YYYY/MM Partitioning**
Laptop (IDE) receipts use month partitioning: `ide/agent/receipts/{repo-id}/{YYYY}/{MM}/`. Example: `ide/agent/receipts/zeroui2-0/2025/10/`. Auxiliary folders (index, quarantine, checkpoints) live under the same repo path.

**Rule 229: (Deprecated)**  
See **Rule 226: RFC Fallback Pattern (UNCLASSIFIED__slug, 24h Resolution)**.

**Rule 230: (Deprecated)**  
See **Rule 227: Observability/Adapters Use dt= Partitions**.

**Rule 231: (Deprecated)**  
See **Rule 228: Laptop Receipts Use YYYY/MM Partitioning**.

---

## STOP CONDITIONS → ERROR CODES (REFUSE & FIX)

* **ERROR:TS_STRICT_OFF** — strict checks are disabled.
* **ERROR:ANY_USED** — `any` found in committed code.
* **ERROR:PROMISE_UNHANDLED** — promise without `await`/`.catch`.
* **ERROR:NULL_UNHANDLED** — missing checks for optional/nullable.
* **ERROR:NARROWING_MISSING** — union used without type checks.
* **ERROR:CYCLE_IMPORTS** — circular imports/barrel chain.
* **ERROR:DUPLICATE_DTOS** — hand-rolled API types instead of shared/generated ones.
* **ERROR:LINT_FAIL** — linter errors or warnings in CI.
* **ERROR:TESTS_MISSING** — new logic without tests.
* **ERROR:SECRETS_LEAK** — secrets/PII in code, samples, or logs.
* **ERROR:EXCEPTION_POLICY_DRIFT** — errors not mapped to the approved code list.
* **ERROR:AI_CODE_UNREVIEWED** — AI-generated TypeScript without human review.
* **ERROR:BUNDLE_BLOAT** — Import patterns that significantly increase bundle size.
* **ERROR:DEPENDENCY_TYPE_UNSAFE** — Using untyped or poorly-typed dependencies.
* **ERROR:TYPE_TEST_MISSING** — Complex types without boundary tests.
* **ERROR:MIGRATION_VIOLATION** — Breaking type safety during JS to TS migration.

---

## DAILY CHECKLIST (30 seconds)

* [ ] Strict mode on; no `any`
* [ ] Optional/nullable values checked
* [ ] Unions narrowed before use
* [ ] Promises awaited/handled
* [ ] Friendly error at edges; details in logs (no secrets)
* [ ] Timeouts/cancel for I/O; small safe retries
* [ ] Lint + type-check pass
* [ ] Tests cover happy + failure paths
* [ ] No circular imports; no duplicate types
* [ ] AI-generated code reviewed
* [ ] Bundle size within limits
* [ ] Dependencies properly typed

---

## QUICK START (apply today)

1. Turn **strict** on.
2. Replace top 3 `any` with real types or `unknown` + checks.
3. Add a **central error handler** at the boundary (command/route).
4. Set a **default timeout** for network/file work.
5. Create a tiny **type library** for your main data shapes and reuse it.
6. **Review all AI code** for type safety and standards compliance.
7. **Set bundle size budgets** and monitor imports.
8. **Audit dependencies** for type definitions.

---

## NEW DEVELOPER ONBOARDING

**First TypeScript Task:**
1. Fix 3 `any` types in existing code
2. Add proper error handling to one async function
3. Write tests for the fixed function
4. Review one AI-generated TypeScript file
5. Verify no new lint warnings
6. Check bundle size impact

**Common Patterns:**
```typescript
// Good: AI-generated code with proper typing
interface User {
  id: string;
  name: string;
}

// Instead of `any`, use specific types
function processUser(user: User) {
  // TypeScript knows user has id and name
}
```

# GSMD — Cursor Enforcement Rules (Appendix)

**Rule 232: GSMD Source of Truth (SOT) Paths**  
Policy snapshots live only under:
```
gsmd/modules/M{NN}/{slug}/v{major}/snapshot.json
```
Treat these files as the **single source of truth** for governance decisions. Do not place snapshots anywhere else.

**Rule 233: Read-Only Policy Assets**  
You MUST NOT edit or overwrite existing files under `gsmd/**`. To change policy, create a **new version folder** (e.g., `v2/`) and add a new `snapshot.json`. Keep older versions intact.

**Rule 234: Versioning Is Append-Only**  
Breaking or behavioral changes require a new `v{major}` directory. Do not mutate prior versions. Use the `deprecates[]` field when formally superseding older snapshots.

**Rule 235: Snapshot Identity & Integrity**  
Every snapshot MUST satisfy:
- `snapshot_id` pattern: `SNAP.M\d{2}.[a-z0-9_.]+.(v|V)\d+`
- `module_id` pattern: `M\d{2}`
- `snapshot_hash` equal to **sha256** of file contents (hex) prefixed with `sha256:`
- `signature` and `kid` present
- `effective_from` ISO-8601  
Use `tools/gsmd-check.ps1` to verify. Fail CI if any check fails.

**Rule 236: Valid Evaluation Points Only**  
Allowed values are exactly:
```
pre-commit | pre-merge | pre-deploy | post-deploy
```
Code and receipts must use only these values.

**Rule 237: Decision Receipts — Required Fields**  
Every GSMD decision MUST emit a signed receipt containing at minimum:
```
decision, rationale, policy_snapshot_hash, policy_version_ids[],
evaluation_point, actor_id, repo_id, timestamps.hw, signature
```
Values for `policy_snapshot_hash` and `policy_version_ids[]` MUST come from the snapshot actually used.

**Rule 238: Receipt Discipline (Append-Only, Signed)**  
Receipts are newline-delimited JSON (JSONL), append-only. Never rewrite. Each receipt is signed; reject or quarantine any receipt missing a signature.

**Rule 239: Tenant Overrides (Strict Contract)**  
Overrides MUST include:
```
tenant_id, scope.module_id[, scope.slug][, scope.evaluation_point],
waiver.reason[, waiver.ticket_id][, waiver.evidence_refs[]],
ttl (ISO-8601), approvals[>=2]{user, role, approved_at (ISO-8601)},
kid, signature
```
Overrides are **time-boxed** (honor `ttl`) and require **two or more approvals**. No permanent overrides.

**Rule 240: Override Storage & Lifecycle**  
Store overrides **outside** `gsmd/` (runtime/config store). Log issuance and expiry via receipts. When `ttl` elapses, the override is invalid without re-approval.

**Rule 241: Decisions & Modes (Status Pill)**  
Implement decisions using the canonical set only:
```
pass | warn | soft_block | hard_block
```
Honor snapshot `messages.status_pill.*` and `rollout.default_mode`. Do not invent new statuses.

**Rule 242: Rollout & Cohorts**  
If `rollout.cohorts` or `rollout.ladder` are present, enforce exactly as declared. If absent, use `rollout.default_mode`. Never assume implied cohorts.

**Rule 243: Privacy & Redaction**  
Apply any rules present under `privacy.redactions` **before** logging or emitting receipts. Never log raw PII or secrets. Log **hashes/sizes** instead of raw payloads.

**Rule 244: Evidence & Required Receipts**  
If `evidence.map[]` or `receipts.required[]` are present in the snapshot, collect the named artifacts (or their hashes) and ensure required receipts exist **before** returning a terminal decision.

**Rule 245: Tests Fixtures Must Match Policy**  
Where `tests.fixtures[]` are present, unit/integration tests MUST prove the declared outcomes (`pass | warn | soft_block | hard_block`). Do not merge if observed outcomes differ from fixtures.

**Rule 246: Mandatory CI Gates**  
Every PR touching policy or enforcement MUST run:
```
./tools/gsmd-check.ps1 -Root ./gsmd -VerboseOutput
```
Block merge on any failure.

**Rule 247: Release Manifests (Merkle Root)**  
Before publishing a policy release, generate a manifest and (optionally) sign it:
```
./tools/manifest-build.ps1   -Root ./gsmd -OutDir ./gsmd/releases -Kid "<KID>"
./tools/manifest-verify.ps1  -Root . -Manifest <path\\to\\manifest.json>
```
Block release if file hashes or Merkle root mismatch.

**Rule 248: Runtime Snapshot Binding**  
At decision time, the engine MUST bind to the exact snapshot referenced by the receipt (`policy_version_ids[]` and `policy_snapshot_hash`). Never apply a different snapshot than the one recorded.

**Rule 249: Cursor Behavior for GSMD**  
Cursor MUST NOT propose edits under `gsmd/**`. It MUST:
- Read the relevant snapshot fields first
- Surface `snapshot_id`, `policy_version_ids[]`, `policy_snapshot_hash`
- Propose **new version** files for policy changes (no in-place edits)
- Suggest running the CI gates above

**Rule 250: Return Contracts for GSMD Artifacts**  
For policy work, output only one of:
- **New File** → for adding `.../v{new}/snapshot.json` (full file content)
- **JSON Artifact** → for overrides/receipts (valid JSON only)
- **Unified Diff** → never used to mutate existing snapshots; use only for non-policy code/config  
Violations → `ERROR:GSMD_RETURN_CONTRACT_VIOLATION`.

**Rule 251: Stop Conditions → GSMD Error Codes**  
- Writing outside SOT tree .......................... `ERROR:GSMD_SOT_VIOLATION`  
- Attempt to modify existing snapshot ............... `ERROR:GSMD_MUTATION_DENIED`  
- Hash mismatch vs `snapshot_hash` .................. `ERROR:GSMD_HASH_MISMATCH`  
- Missing/invalid signature or `kid` ................ `ERROR:GSMD_SIGNATURE_MISSING`  
- Invalid evaluation_point .......................... `ERROR:GSMD_EVALPOINT_INVALID`  
- Receipt missing required fields ................... `ERROR:GSMD_RECEIPT_FIELDS_MISSING`  
- Override missing ttl/approvals/signature .......... `ERROR:GSMD_OVERRIDE_INVALID`  
- Approvals < 2 on override ......................... `ERROR:GSMD_APPROVALS_INSUFFICIENT`  
- Manifest verify (hash/Merkle) fail ................ `ERROR:GSMD_MANIFEST_INVALID`  
- Decision not in allowed set ....................... `ERROR:GSMD_DECISION_INVALID`  
- Privacy redaction not applied ..................... `ERROR:GSMD_PRIVACY_DRIFT`  
- Tests/fixtures absent for declared policy ......... `ERROR:GSMD_TESTS_MISSING`  
- Return contract not honored ....................... `ERROR:GSMD_RETURN_CONTRACT_VIOLATION`

**Rule 252: Self-Audit Before Output (GSMD)**  
- [ ] Not editing existing `gsmd/**`; new version only when needed  
- [ ] Snapshot patterns/fields valid; `snapshot_hash` recomputes  
- [ ] Evaluation point valid; decision ∈ {pass,warn,soft_block,hard_block}  
- [ ] Receipt fields complete and signed; values sourced from snapshot  
- [ ] Overrides time-boxed (ttl) with ≥2 approvals; signed  
- [ ] CI gates added (`gsmd-check`, manifest build/verify)  
- [ ] Privacy redactions applied; no PII/secrets in logs or receipts  
- [ ] Output matches allowed return contract
