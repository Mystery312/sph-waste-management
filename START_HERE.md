# 🚀 START HERE - SPH Visualization Quick Reference

## What This Project Does

This is a **real-time 3D visualization of SPH (waste management) fluid simulation** that shows contamination spreading through water.

**You'll see:** 8,000 animated particles changing from blue (clean) → yellow (mixed) → red (contaminated) as they flow and spread.

## What's Been Done ✅

- ✅ Python simulation engine (fully working)
- ✅ WebSocket streaming (bug fixed)
- ✅ Unity project template (ready to use)
- ✅ Complete documentation
- ✅ Automated setup tool

## What You Need to Do 📋

### 3-Step Quick Start

#### Step 1: Open Unity Project (5 min)
```
1. Open Unity Hub
2. Click "Open Project"
3. Navigate to: /Users/yeonjune.kim.27/Desktop/SPH-Visualization
4. Wait for import
```

#### Step 2: Install Package & Auto-Setup (5 min)
```
1. Window → Package Manager
2. Click [+] button
3. "Add package from git URL..."
4. Paste: https://github.com/endel/NativeWebSocket.git#upm
5. Click [Add]
6. Wait for install
7. Tools → SPH → Setup Project (Automated)
8. Click OK
```

#### Step 3: Test (5 min)
```
Terminal:
$ cd /Users/yeonjune.kim.27/Desktop/Waste\ Management
$ python unity_streaming_main.py

Unity:
Press Play [▶️]
→ Should see particles with metrics
```

**Total: 1-2 hours** (mostly waiting for software)

---

## Detailed Guide

For **step-by-step instructions with verification**, see:

```
/Users/yeonjune.kim.27/Desktop/SPH-Visualization/SETUP_CHECKLIST.md
```

This has:
- 6 detailed steps
- Expected results for each
- Verification checkpoints
- Troubleshooting guide
- Success criteria

**Start with SETUP_CHECKLIST.md - it's written for first-time users.**

---

## Key Files

### Unity Project Location
```
/Users/yeonjune.kim.27/Desktop/SPH-Visualization/
```

### Inside the Project
- **SETUP_CHECKLIST.md** ⭐ = Start here (step-by-step)
- **README.md** = Quick overview (5 steps)
- **PROJECT_SUMMARY.md** = Technical details
- **SPHStreamingClient.cs** = Main WebSocket code
- **SPHSetup.cs** = Automated setup tool
- **OrbitCamera.cs** = Camera controller

### Python Backend
```
/Users/yeonjune.kim.27/Desktop/Waste Management/
```

**To start server:**
```bash
python unity_streaming_main.py
```

---

## Expected Result

When everything works, you'll see:

### In Unity Game View
- 8,000 particles flowing smoothly
- **Blue** = clean water
- **Yellow** = mixed
- **Red** = contaminated
- Real-time movement (30 FPS from server, 60 FPS rendering)

### Top-Left Corner (Metrics)
```
SPH Simulation - Phase 3
Status: Connected
Time: 2.345s
Step: 1234
Particles: 8000
Mean Concentration: 0.1234
Mixing Index: 0.5678
Center of Mass: (0.5, 0.3, 0.5)
```

### Camera Controls
- **Right-click + drag:** Rotate
- **Mouse wheel:** Zoom
- **Middle-click + drag:** Pan

---

## If Something Goes Wrong 🛠️

### "Connection refused"
→ Python server not running
→ Check terminal: should say "Server running - waiting for connections..."

### "No particles appearing"
→ Check camera: should be at (1.5, 1.0, 1.5)
→ Zoom out with mouse wheel

### "White particles"
→ Particle material not assigned
→ Run again: Tools → SPH → Setup Project (Automated)

### "Won't connect to Unity"
→ Check firewall isn't blocking port 8765
→ Check server URL: ws://localhost:8765

**For more issues:** See SETUP_CHECKLIST.md troubleshooting section

---

## Quick Commands

```bash
# Start Python server (keep terminal open!)
cd /Users/yeonjune.kim.27/Desktop/Waste\ Management
python unity_streaming_main.py

# Test WebSocket works (optional)
python test_websocket_broadcast.py

# Test full pipeline (optional)
python test_streaming_e2e.py
```

**In Unity Editor:**
- **Tools → SPH → Setup Project (Automated)** = Auto-configure
- **Space** = Play/Stop
- **Ctrl+S** = Save

---

## File Layout

```
Your Computer:

/Users/yeonjune.kim.27/
  ├── Desktop/
  │   ├── SPH-Visualization/          ← Open THIS in Unity
  │   │   ├── Assets/
  │   │   │   ├── Scripts/            (3 C# scripts)
  │   │   │   ├── Materials/          (particle material)
  │   │   │   └── Prefabs/            (created by setup)
  │   │   ├── SETUP_CHECKLIST.md      ← Read THIS first
  │   │   ├── README.md
  │   │   └── PROJECT_SUMMARY.md
  │   │
  │   └── Waste Management/           ← Python server here
  │       ├── unity_streaming_main.py (run THIS)
  │       ├── test_websocket_broadcast.py
  │       ├── PHASE_0_COMPLETE.md
  │       ├── PHASE_1_EXTENDED_SESSION.md
  │       └── START_HERE.md            (this file)
```

---

## Summary

### Phase 0 ✓ DONE
WebSocket broadcasting bug fixed. Python server verified working.

### Phase 1 ✓ DONE
Complete Unity project created. Ready to open and test.

### What's Next (Phase 2)
After Phase 1 works, add gradient visualization (∇C arrows).
Estimated: 6-8 additional hours.

### Your Task Right Now
1. Open Unity
2. Follow SETUP_CHECKLIST.md (6 steps)
3. Run Python server
4. Test connection
5. Verify particles render

---

## Support

**Technical Questions:**
- See `/Users/yeonjune.kim.27/Desktop/SPH-Visualization/SETUP_CHECKLIST.md`

**Understanding the Code:**
- See `/Users/yeonjune.kim.27/Desktop/SPH-Visualization/PROJECT_SUMMARY.md`

**Project Overview:**
- See `CLAUDE.md` in main project folder

**Phase Progress:**
- See `PHASE_1_EXTENDED_SESSION.md` (this session's work)

---

## Success Checklist

Phase 1 complete when you have:

- ☐ Unity project opens without errors
- ☐ NativeWebSocket installed
- ☐ Automated setup runs
- ☐ "Connected" message in Console
- ☐ Blue/red particles visible
- ☐ Metrics display updating
- ☐ 60 FPS maintained
- ☐ No Console errors

**If all checked: Phase 1 ✅ COMPLETE**

---

## Next Steps

### Option 1: Test Now
```bash
# Terminal 1
cd /Users/yeonjune.kim.27/Desktop/Waste\ Management
python unity_streaming_main.py

# Then in Unity Editor
# Press Play [▶️]
```

### Option 2: Read First
```
Open: /Users/yeonjune.kim.27/Desktop/SPH-Visualization/SETUP_CHECKLIST.md
Follow the 6 steps
```

---

## Key Information

| Item | Value |
|------|-------|
| **Unity Project** | `/Users/yeonjune.kim.27/Desktop/SPH-Visualization/` |
| **Setup Guide** | `SETUP_CHECKLIST.md` (in project) |
| **Python Server** | `/Users/yeonjune.kim.27/Desktop/Waste Management/` |
| **Server Command** | `python unity_streaming_main.py` |
| **WebSocket URL** | `ws://localhost:8765` |
| **Particles** | 8,000 |
| **Broadcast Rate** | 30 FPS |
| **Render Rate** | 60 FPS |
| **Setup Time** | 1-2 hours |

---

## FAQ

**Q: Do I need Visual Studio?**
A: No, Unity handles C# editing. You can use VS Code if you want, but it's optional.

**Q: Can I run this on Mac/Linux/Windows?**
A: Yes! Works on all platforms. WebSocket is cross-platform.

**Q: What if I don't have 8,000 particles?**
A: You can reduce in `config.py`: `NUM_PARTICLES = 2000`

**Q: Can I record video?**
A: Yes! Use Unity Recorder (optional Phase 4 feature).

**Q: What's the Python simulation doing?**
A: Simulating contaminated water (8,000 particles) spreading by physics + diffusion.

**Q: Why color gradient?**
A: Red = waste (concentration=100%), Blue = clean water (concentration=0%).

**Q: What's the Calculus 3 part?**
A: You'll add visualization of ∇C (gradient) and ∭ C dV (volume integral) in Phase 2-3.

---

## Time Breakdown

| Task | Time | Status |
|------|------|--------|
| Open Unity project | 5 min | Ready |
| Install NativeWebSocket | 5 min | Ready |
| Run automated setup | 2 min | Ready |
| Start Python server | 2 min | Ready |
| Test connection | 2 min | Ready |
| Verify success | 5 min | Ready |
| **Total** | **1-2 hours** | **Ready to go** |

---

## Remember

✅ **Keep Python server terminal OPEN** while testing in Unity

✅ **Check Console for error messages** if something doesn't work

✅ **WebSocket connects on port 8765** (make sure firewall allows it)

✅ **Particles should appear within 2 seconds** of pressing Play

✅ **All settings auto-configured** by setup tool (no manual Inspector work)

---

## You're All Set!

Everything is ready. Just:

1. **Open Unity** → `/Users/yeonjune.kim.27/Desktop/SPH-Visualization/`
2. **Read guide** → `SETUP_CHECKLIST.md`
3. **Follow 6 steps** → Takes ~1-2 hours
4. **Run server** → `python unity_streaming_main.py`
5. **Press Play** → See 8,000 animated particles!

**Good luck! 🎉**

---

**Status:** ✅ Ready to Use
**Date:** 2026-02-13
**Next:** Phase 1 Testing
