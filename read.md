 ZEROUI 2.0 CONSTITUTION 

 🎯 BASIC WORK RULES

 Rule 1: Do Exactly What's Asked
 If your friend asks you to make a peanut butter sandwich, don't add jelly unless they ask for it. Follow instructions exactly without adding your own ideas.

 Rule 2: Only Use Information You're Given  
 If you're baking cookies and the recipe doesn't say how much sugar to use, stop and ask. Don't guess or make up an amount.

 Rule 3: Protect People's Privacy
 Treat everyone's personal information like a secret diary. Don't look at it, don't share it, and definitely don't write it down where others can see it.

 Rule 4: Use Settings Files, Not Hardcoded Numbers
 Instead of writing "use 10 apples" in your recipe, write "use [number] apples" and keep the number 10 in a separate note. This way you can easily change to 12 apples later.

 Rule 5: Keep Good Records
 Like keeping a science lab notebook - write down what you did, when you did it, and what happened. Use the format your teacher asks for, and don't add extra stuff they didn't request.

Where we keep these records:
- Action receipts → Like a shopping list that only gets longer (JSONL files)
- Error and performance notes → Like an organized notebook (SQLite database)
- Everything stays private → Never leaves your computer without permission

 Rule 7: Never Break Things During Updates
 When updating a video game, you should still be able to play while it updates. If the update causes problems, you can instantly switch back to the old version.

"During Updates" means: The time from when you click "update" until the new version is completely ready and working properly.

 Rule 8: Make Things Fast
 
- Programs should start faster than microwaving popcorn (under 2 seconds)
- Buttons should respond instantly when clicked (under 0.1 seconds)
- Don't use too much computer memory - like not hogging all the closet space

 Rule 10: Be Honest About AI Decisions
 When AI suggests something, it should say:
- "I'm 85% sure this is right" (confidence level)
- "I'm suggesting this because..." (explanation)
- "This was AI version 2.3" (which brain version made the decision)

Where this information is stored:
1. Your computer - Private notes about your work
2. Your company's private storage - Team review notes
3. Our cloud (anonymous only) - Just patterns like "suggestion X was 85% confident" - no actual code or personal info

 Rule 11: Check Your Data
 Make sure the AI's training data is like a fair test - balanced questions, up-to-date information, and correct answers.

 Rule 12: Keep AI Safe
 AI should only work in a special "playground" (sandbox) away from real computers. It can look at code and make suggestions, but never actually run code on people's machines.

 Rule 13: Learn from Mistakes
 When the AI gets something wrong, it should remember that mistake and get smarter, just like you learn from getting test questions wrong.

 Rule 14: Test Everything
 Always try things out before saying they work. Don't break things that already work. Test both simple cases and tricky situations.

 Rule 15: Write Good Instructions
 Give people working examples they can try themselves, clear explanations of how to use things, and troubleshooting guides for when things go wrong.

 Rule 16: Keep Good Logs
 Write clear notes that are easy to read, use special tracking numbers to follow requests through the system, and measure both technical numbers and business results.

 Rule 17: Make Changes Easy to Undo
 Prefer adding new features rather than changing old ones. Use on/off switches for features. Write down how to go back if something doesn't work.

 Rule 18: Make Things Repeatable
 Write down exactly what ingredients (versions) you used. Don't depend on special kitchen equipment (computer setups). Include simple steps so others can recreate your work.

 Rule 19: Keep Different Parts Separate
 The display screen (user interface) only shows information. The thinking part (business logic) only does calculations. Never mix these two jobs.

 Rule 20: Be Fair to Everyone
 Use clear, simple language everyone can understand. Don't use tricky designs that might confuse people. Make sure people with disabilities can use everything.

 🏗️ SYSTEM DESIGN RULES

 Rule 21: Use the Hybrid System Design
 Our system has four parts:
- IDE Extension → Only shows information (like a car dashboard)
- Edge Agent → Processes data locally for privacy (like thinking in your head)
- Client Cloud → Stores company's private data (like a company safe)
- Our Cloud → Only gets anonymous, safe data (like public statistics)

 Rule 22: Make All 18 Modules Look the Same
 All 18 tools should use the same buttons, menus, and look. Like different rooms in the same house - they have the same light switches and door handles.

 Rule 23: Process Data Locally First
 
- Source code → Never leaves the company (like secret recipes)
- Development data → Stays in company cloud (like work notes)
- Anonymous patterns → Can go to our cloud (like "people prefer chocolate over vanilla" - no specific info)

 Rule 24: Don't Make People Configure Before Using
 Things should work right out of the box. Like a new video game - you can start playing immediately, and only set up complex controls later if you want.

 Rule 25: Show Information Gradually
 
- Level 1 → Basic status (like a traffic light - red/yellow/green)
- Level 2 → Suggestions when relevant (like a friend saying "try this")
- Level 3 → Full tools when asked (like opening a complete toolbox)

 Rule 26: Organize Features Clearly
 
18 Main Areas → Specific Features → Detailed Tools
Like a school: School → Grade Levels → Classrooms → Subjects

 Rule 27: Be Smart About Data

- Never send → Source code, passwords, personal info (like your diary)
- Company cloud only → Team metrics, security scans (like company reports)
- Our cloud allowed → Anonymous patterns, general insights (like "most people work better in the morning")

 Rule 28: Work Without Internet
 Core features must work offline, like being able to write in a notebook when you don't have WiFi. Save actions and sync when you're back online.

 Rule 29: Register Modules the Same Way
 All 18 modules should sign up using the same process, like every student using the same enrollment form.

 Rule 30: Make All Modules Feel Like One Product
 Use the same command names everywhere, make status indicators look the same, handle errors the same way - like different apps made by the same company.

 Rule 31: Design for Quick Adoption

- People should get value in first 30 seconds (like instant fun in a game)
- 80% of users should use each module (like most students using the library)
- 90% should still be using after 30 days (like people sticking with a good habit)

 Rule 32: Test User Experience

- No setup needed before use (like instant-on TV)
- First interaction in under 30 seconds (like quick-start instructions)
- System almost never crashes (like reliable car)
- Buttons respond instantly (like light switches)

 🎯 PROBLEM-SOLVING RULES

 Rule 33: Solve Real Developer Problems
 Every feature must fix a real frustration developers face, like making homework easier by having better tools.

 Rule 34: Help People Work Better

- Mirror → Show people what they're doing now (like a mirror)
- Mentor → Guide them to better ways (like a coach)
- Multiplier → Help them do more of what works (like a turbo boost)

 Rule 35: Prevent Problems Before They Happen
 Stop issues before they become big problems, like fixing a small leak before it floods the house.

 Rule 36: Be Extra Careful with Private Data

- Never look at → Production passwords, user personal data (like bank codes)
- Process locally → Code analysis, performance checks (like thinking privately)
- Share only → Anonymous patterns, general insights (like "students learn better with examples")

 Rule 37: Don't Make People Think Too Hard
 Fix common issues with one click, give suggestions without interrupting, automate boring tasks, teach as you go - like having a helpful friend.

 Rule 38: MMM Engine - Change Behavior
 Help people stop making the same mistakes, increase use of best practices, reduce need for manual fixes, help people solve problems themselves - like a good habit coach.

 Rule 39: Detection Engine - Be Accurate

- Wrong alerts → Less than 2% for critical issues (like rarely crying wolf)
- Missed problems → Less than 1% for security (like rarely missing real danger)
- Show confidence levels clearly (like saying "I'm very sure" or "I'm guessing")
- Learn from corrections (like learning from mistakes)

 Rule 40: Risk Modules - Safety First
 Never make situations worse, always provide undo options, support gradual improvements, verify before big changes - like safety rules in science lab.

 Rule 41: Success Dashboards - Show Business Value
 Connect engineering work to company results, show money saved and time gained, track both current and future benefits - like showing how studying leads to better grades.

 🔧 PLATFORM RULES

 Rule 42: Use All Platform Features
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

 Rule 43: Process Data Quickly
 Handle urgent data in less than 1 second (like answering important texts immediately), group less important data (like checking regular mail once a day), check data quality as it comes in.

 Rule 44: Help Without Interrupting
 Give help when needed, not before (like waiting to be asked), match help to how complex the task is (like simple vs complex instructions), let experts turn off basic help.

 Rule 45: Handle Emergencies Well
 Make the right action obvious (like big red stop button), provide one-click solutions, offer multiple ways to recover, show clear progress updates - like good emergency instructions.

 Rule 46: Make Developers Happier
 Reduce time spent switching between tasks, cut down on boring repetitive work, increase time spent on meaningful coding, build confidence in deployments - like making schoolwork more enjoyable.

 Rule 47: Track Problems You Prevent
 Count security issues caught early, track deployment failures avoided, measure knowledge gaps found and fixed, watch technical debt prevented - like counting accidents that didn't happen because of safety measures.

 Rule 48: Build Compliance into Workflow
 Check rules automatically during development, monitor compliance in real-time, generate audit reports easily, assess impact of rule changes - like having built-in spell check while writing.

 Rule 49: Security Should Help, Not Block
 Security tips shouldn't break concentration, automate common security fixes, explain security rules in simple terms, prioritize security risks by importance - like friendly security guards rather than prison guards.

 Rule 50: Support Gradual Adoption
 Let teams start with 3-5 most useful modules, each module should work well on its own, show clear paths to add more modules, provide value at every step - like learning math starting with addition, then multiplication.

 Rule 51: Scale from Small to Huge
 Work for 1 developer or 10,000, handle 100 events per day or 10 million, support simple systems and complex ones, meet basic needs and strict regulations - like a playground that works for both small kids and professional athletes.

 🤝 TEAMWORK RULES

 Rule 52: Build for Real Team Work
 Make collaboration natural and easy, help teams share knowledge automatically, reduce meetings and emails through better tools, make it easy to help each other without interrupting work - like good group project tools.

 Rule 53: Prevent Knowledge Silos
 Automatically identify who knows what, suggest when to share important information, help teams learn from each other's successes, make expertise easy to find when needed - like knowing which friend to ask for help with different subjects.

 Rule 54: Reduce Frustration Daily
 Fix the small annoyances that add up, automate boring repetitive tasks, make hard things easier, celebrate small wins and progress - like making daily chores less annoying.

 Rule 55: Build Confidence, Not Fear
 Make deployments feel safe and controlled, provide safety nets for mistakes, show progress and improvements clearly, help people learn without embarrassment - like training wheels on a bike.

 Rule 56: Learn and Adapt Constantly
 Watch how people actually use the product, learn from what works and what doesn't, make the product smarter over time, adapt to different team styles and needs - like a teacher who adjusts to how students learn best.

 Rule 57: Measure What Matters
 Track real improvements, not just activity, measure time saved and stress reduced, watch for positive behavior changes, count problems prevented, not just fixed - like measuring learning, not just time spent studying.

 Rule 58: Catch Issues Early
 Find problems when they're small and easy to fix, warn about potential issues before they happen, suggest simple fixes for common mistakes, prevent small issues from becoming big problems - like fixing a small leak before it becomes a flood.

 Rule 59: Build Safety Into Everything
 Always have an "undo" button, make dangerous actions hard to do accidentally, provide multiple ways to recover from mistakes, test changes safely before applying them - like safety features in cars.

 Rule 60: Automate Wisely
 Only automate things that are boring or error-prone, always let people review and approve important changes, make automation helpful, not annoying, explain what the automation is doing and why - like a helpful robot assistant.

 Rule 61: Learn from Experts
 Watch how the best developers work, copy their successful patterns, help everyone work like the experts, share best practices across the whole team - like learning sports from professional athletes.

 Rule 62: Show the Right Information at the Right Time
 Don't overwhelm people with too much information, show what's important right now, hide complexity until it's needed, make status and progress clear at a glance - like a good car dashboard.

 Rule 63: Make Dependencies Visible
 Show how different pieces connect and depend on each other, warn when changes might affect other people, help teams coordinate without meetings, make the system's architecture easy to understand - like a map showing how roads connect.

 Rule 64: Be Predictable and Consistent
 Work the same way every time, don't surprise people with unexpected behavior, explain clearly what will happen before it happens, build trust through reliability - like a reliable friend.

 Rule 65: Never Lose People's Work
 Save work automatically and frequently, provide clear recovery options, back up important information, warn before doing anything that can't be undone - like automatic save in video games.

 Rule 66: Make it Beautiful and Pleasant
 Use clean, attractive designs, choose pleasant colors and fonts, make interactions smooth and satisfying, create an experience people enjoy using - like a well-designed park.

 Rule 67: Respect People's Time
 Load quickly and respond instantly, don't make people wait unnecessarily, streamline common tasks, value every second of people's time - like express checkout lines.

 Rule 68: Write Clean, Readable Code
 Make code easy to understand and modify, use clear names and simple structures, document why decisions were made, keep code organized and consistent - like writing clear, neat notes.

 Rule 69: Handle Edge Cases Gracefully
 Plan for things going wrong, handle errors without crashing, provide helpful error messages, recover smoothly from problems - like having a plan B when things don't go as expected.

 Rule 70: Encourage Better Ways of Working
 Suggest improvements to processes, help teams adopt better practices, make good habits easy to form, reward continuous improvement - like a good coach.

 Rule 71: Adapt to Different Skill Levels
 Help beginners learn quickly, support experts with advanced features, don't force one way of working on everyone, grow with people as they learn and improve - like books with different reading levels.

 Rule 72: Be Helpful, Not Annoying
 Offer help when it's actually needed, know when to be quiet and stay out of the way, learn what kind of help each person prefers, get better at helping over time - like a helpful friend who knows when to help and when to let you figure things out.

 Rule 73: Explain AI Decisions Clearly
 Don't be a "black box" - show your reasoning, help people understand why you're making suggestions, be honest about uncertainty and limitations, build trust through transparency - like showing your math work instead of just the answer.

 Rule 74: Demonstrate Clear Value
 Show how the product saves time and money, make benefits obvious and measurable, connect features to real business outcomes, prove your worth every day - like showing how studying leads to better grades.

 Rule 75: Grow with the Customer
 Work well for small teams and huge organizations, adapt to different industries and needs, support both simple and complex situations, scale smoothly as needs grow - like clothes that can expand as you grow.

 Rule 76: Create "Magic Moments"
 Occasionally surprise and delight users, make some tasks feel effortless and magical, exceed expectations in small, meaningful ways, create features that people love to show others - like finding an extra french fry at the bottom of the bag.

 Rule 77: Remove Friction Everywhere
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
