# IntentCore Quick Start Guide

## 🚀 3-Minute Demo

### Option 1: Run the Demo Script (Recommended First Step)

```bash
# From project root
python3 demo_intentcore.py
```

**What you'll see:**
- Complete $90M NVDA trade scenario
- Reasoning extraction (100% completeness)
- Governance enforcement (high-value review required)
- Human review simulation
- Execution recording
- Database creation (`demo_intentcore.db`)

**Expected output:** ✅ Full flow demonstration in ~5 seconds

---

### Option 2: Full UI Experience

#### Step 1: Start the API
```bash
cd intentcore/ui/backend

# Install dependencies (first time only)
pip install fastapi uvicorn pydantic python-dateutil

# Start server
python3 -m uvicorn api:app --reload
```

**Check:** Visit http://localhost:8000 - should see `{"service": "IntentCore API", ...}`

#### Step 2: Start the Frontend
```bash
# Open new terminal
cd intentcore/ui/frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Check:** Visit http://localhost:3000 - should see IntentCore UI

#### Step 3: Populate with Demo Data
```bash
# Open new terminal, from project root
python3 demo_intentcore.py
```

#### Step 4: View in UI
1. Open http://localhost:3000
2. Click "Review Queue" - see the $90M NVDA decision
3. Click on the decision - see complete reasoning
4. Navigate to "Dashboard" - see metrics
5. Navigate to "History" - see decision audit trail

---

## 📋 What's In Each Component

### Demo Script (`demo_intentcore.py`)
- Simulates FinRobot agent conversation
- Proposes $90M NVDA trade
- Runs through IntentCore pipeline
- Creates `demo_intentcore.db` with complete data

### API (`intentcore/ui/backend/api.py`)
- FastAPI REST server
- Endpoints for reviews, chains, metrics
- Runs on port 8000

### UI (`intentcore/ui/frontend/`)
- React + Vite app
- 4 pages: Queue, Detail, Dashboard, History
- Tailwind CSS styling
- Runs on port 3000

### Core (`intentcore/core/`)
- `reasoning_chain.py` - Data models
- `extractor.py` - Reasoning extraction
- `runtime.py` - Main orchestrator

### Governance (`intentcore/policies/governance.py`)
- Trade limits
- Blacklists
- Timing restrictions
- Policy enforcement

### Database (`intentcore/database/`)
- SQLite schema
- Database manager
- Reasoning chains, patterns, audit log

### Bridge (`intentcore/bridge/finrobot_bridge.py`)
- FinRobot integration
- Tool call interception
- Review workflows

---

## 🔍 Explore the Database

```bash
sqlite3 demo_intentcore.db

# View reasoning chains
SELECT chain_id, agent_role, task, completeness_score, human_decision
FROM reasoning_chains;

# View review queue
SELECT * FROM review_queue;

# View audit log
SELECT event_type, timestamp FROM audit_log;

# Exit
.quit
```

---

## 💻 Code Examples

### Basic Integration

```python
from intentcore import IntentCoreRuntime, FinRobotBridge

# Initialize
runtime = IntentCoreRuntime(db_path="my_app.db")
bridge = FinRobotBridge(runtime=runtime)

# Process a decision
result = runtime.process_decision(
    agent_id="agent_001",
    agent_role="Market_Analyst",
    task="Analyze NVDA",
    messages=[...],  # AutoGen messages
    tool_call={...}  # Tool call to review
)

print(f"Decision: {result['decision']}")
print(f"Completeness: {result['reasoning_chain'].completeness_score}")
```

### Custom Review Callback

```python
def my_review_callback(chain):
    """Custom review logic."""
    print(f"Review needed: {chain.task}")
    print(f"Action: {chain.selected_action}")

    # Your review logic here
    approved = check_with_pm(chain)

    return {
        "reviewer_id": "pm_sarah",
        "decision": "approved" if approved else "rejected",
        "rationale": "Reviewed by PM",
    }

bridge.set_review_callback(my_review_callback)
```

### Query Historical Decisions

```python
# Get recent decisions
chains = runtime.db.query_reasoning_chains(
    agent_id="Market_Analyst",
    requires_review=True,
    limit=10
)

for chain in chains:
    print(f"{chain.timestamp}: {chain.task}")
    print(f"  Decision: {chain.human_decision}")
    print(f"  Completeness: {chain.completeness_score:.0%}")
```

---

## 🎯 Key Features to Test

### 1. Reasoning Extraction
- **What:** Automatically extracts situation, analysis, rationale, risks
- **Test:** Run demo and check `chain.situation`, `chain.rationale`
- **Expected:** 100% completeness score

### 2. Governance Policies
- **What:** Enforces trade limits, blacklists, timing restrictions
- **Test:** Demo shows "$90M requires review" (exceeds $50M threshold)
- **Expected:** `requires_review=True` in output

### 3. Human Review
- **What:** Portfolio manager approves/rejects/modifies
- **Test:** Demo simulates approval with $50M modification
- **Expected:** `human_decision=approved`, `human_modification` set

### 4. Audit Trail
- **What:** Complete immutable record of all decisions
- **Test:** Check `audit_log` table in database
- **Expected:** Events for extraction, governance, review, execution

### 5. React UI
- **What:** Professional review interface
- **Test:** Start UI and navigate through pages
- **Expected:** Clean, responsive interface with real data

---

## 📊 System Architecture

```
User Request
     ↓
FinRobot Agent (analyzes, proposes action)
     ↓
IntentCore Bridge (intercepts tool call)
     ↓
Reasoning Extractor (parses conversation)
     ↓
Governance Engine (enforces policies)
     ↓
[Requires Review?]
     ↓ YES                    ↓ NO
Review Queue          Auto-approve
     ↓                        ↓
Human Review          Execute
     ↓                        ↓
Decision → Database ← Result
```

---

## 🔧 Troubleshooting

### Demo script fails with import error
```bash
# Make sure you're in project root
cd /Users/feifeige/FinRobot-IntentChain

# Run with python3
python3 demo_intentcore.py
```

### API won't start
```bash
# Install dependencies
pip install fastapi uvicorn pydantic

# Check port 8000 isn't in use
lsof -i :8000

# Use different port if needed
python3 -m uvicorn api:app --port 8001
```

### UI build fails
```bash
# Clear and reinstall
cd intentcore/ui/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database locked error
```bash
# SQLite only allows one writer
# Close other database connections
# Or use PostgreSQL for production
```

---

## 📖 Documentation

- **Full README:** `INTENTCORE_README.md`
- **Implementation Details:** `IMPLEMENTATION_COMPLETE.md`
- **Demo Script:** `demo_intentcore.py`
- **API Docs:** http://localhost:8000/docs (when running)

---

## ✅ Validation Checklist

- [ ] Demo script runs successfully
- [ ] Database created: `demo_intentcore.db`
- [ ] Reasoning chain has 100% completeness
- [ ] Policy check shows "review required"
- [ ] Human decision recorded
- [ ] Execution result saved
- [ ] API starts on port 8000
- [ ] UI opens on port 3000
- [ ] Review queue shows decision
- [ ] Dashboard shows metrics

---

## 🎬 Next Steps

1. ✅ **Run demo** - Verify system works
2. 📊 **Explore UI** - See the interface
3. 🔍 **Check database** - Query the data
4. 🔌 **Integrate with FinRobot** - Use in real agents
5. 🎨 **Customize policies** - Adjust for your needs
6. 📈 **Add patterns** - Implement pattern detection
7. 🚀 **Deploy** - Move to production

---

**Time to first demo: <5 minutes**

Just run: `python3 demo_intentcore.py`
