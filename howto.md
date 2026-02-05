# Production Factory: User Guide

A step-by-step guide for producers and team members to use the Production Factory system for documentary production.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Setting Up Your Project](#setting-up-your-project)
3. [Phase 1: Research](#phase-1-research)
4. [Phase 2: Archive Collection](#phase-2-archive-collection)
5. [Phase 3: Script Generation](#phase-3-script-generation)
6. [Phase 4: Voiceover](#phase-4-voiceover)
7. [Phase 5: Final Assembly](#phase-5-final-assembly)
8. [Managing Workflow Status](#managing-workflow-status)
9. [Compliance & Export](#compliance--export)
10. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### Accessing the System

1. Open your web browser and navigate to the Production Factory URL
2. You'll see the main dashboard with the navigation sidebar on the left

### Understanding the Interface

The interface has three main areas:

| Area | Purpose |
|------|---------|
| **Left Sidebar** | Navigate between workflow phases (Episodes, Research, Archive, etc.) |
| **Main Content** | View and manage content for the selected phase |
| **Top Bar** | Project selection and user options |

### Workflow Overview

Every episode moves through 5 phases:

```
🔬 Research → 📼 Archive → 📝 Script → 🎙️ Voiceover → 🎬 Assembly
```

Each phase must be approved before the next phase begins.

---

## Setting Up Your Project

### Creating a New Project

1. Click **"Projects"** in the sidebar
2. Click the **"+ New Project"** button
3. Fill in the project details:
   - **Project Name**: e.g., "Arrow Media - Documentary Series 2025"
   - **Description**: Brief overview of the project
4. Click **"Create Project"**

### Creating a Series

Each project contains multiple series. To create a series:

1. Select your project from the project list
2. Click **"+ New Series"**
3. Enter series details:
   - **Series Name**: e.g., "The NASA Files"
   - **Episode Count**: e.g., 30
   - **Episode Duration**: e.g., 45 minutes
   - **Delivery Format**: e.g., "Broadcast HD + streaming"
4. Upload series-level documents:
   - Series bible/format document
   - Brand guidelines
   - Editorial tone guide
   - Archive access credentials (NASA, Getty)
   - Legal compliance checklist
5. Click **"Create Series"**

### Creating Episodes

For each episode in your series:

1. Navigate to the series you created
2. Click **"+ New Episode"** (or **"+ Factory Episode"** for full workflow setup)
3. Enter the episode brief:
   - **Episode Title**: e.g., "Apollo 13 - The Untold Story"
   - **Episode Number**: e.g., 3
   - **Summary**: One-paragraph episode summary
   - **Key Story Beats**: 3-5 main narrative points
   - **Target Interviewees**: Roles needed (e.g., "NASA Engineer", "Flight Controller")
   - **Archive Requirements**: Types of footage needed
   - **Unique Angle**: What makes this episode special
4. Click **"Create Episode"**

The system automatically creates:
- Empty Research Bucket
- Empty Archive Bucket
- Empty Script Workspace
- Compliance Package structure

---

## Phase 1: Research

### Overview

The Research phase gathers and verifies all factual information needed for the episode. This phase should produce:
- Verified timeline of events
- Technical briefing documents
- Character profiles
- Archive requirements list
- Fact-check sources
- Interview question bank

### Step 1: Upload Your Episode Brief

1. Click **"Episodes"** in the sidebar
2. Select your episode to open the Episode Workspace
3. Click the **"Research"** tab
4. Click **"+ Add Document"**
5. Select document type: **"Uploaded"**
6. Upload your episode brief document
7. Click **"Save"**

### Step 2: Run AI Research Agent

The AI Research Agent automatically generates research based on your episode brief:

1. In the Research tab, click **"🤖 AI Research"**
2. The system will generate:
   - 10-15 specific research questions
   - Timeline of key events requiring verification
   - Technical concepts requiring explanation
   - Potential interview subjects with expertise
   - Archive footage categories needed
3. Wait for the agent to complete (you'll see the progress indicator)
4. Review the generated research documents

### Step 3: Review Research Documents

Each research document has a **confidence level**:

| Level | Meaning | Action Required |
|-------|---------|-----------------|
| ✅ **Verified** | Confirmed from primary sources | Ready to use |
| 🟡 **Probable** | Likely accurate, needs confirmation | Verify before script |
| 🔴 **Requires Confirmation** | Unverified, needs interview/research | Must verify |

To update a document's confidence level:
1. Click on the document card
2. Select the new confidence level from the dropdown
3. Add any verification notes
4. Click **"Update"**

### Step 4: Add Additional Research

To manually add research documents:

1. Click **"+ Add Document"**
2. Select the document type:
   - **Uploaded**: Your own research files
   - **Agent Output**: AI-generated content
   - **Fact Check**: Verification sources
   - **NotebookLM**: Source of truth document
3. Enter the document details
4. Set the confidence level
5. Click **"Save"**

### Step 5: Submit for Review

When your research package is complete:

1. Review all documents have appropriate confidence levels
2. Ensure you have:
   - Timeline document with verified dates
   - Technical briefing for complex topics
   - Character profiles for key people
   - Archive requirements list
   - Interview question bank
3. Click **"Submit for Review"** or update the phase status to **"Review"**

### Step 6: Producer Approval

The series producer reviews the research package (48-hour review gate):

1. Producer receives notification of pending review
2. Producer can:
   - Request additional research on specific areas
   - Upload supplementary documents
   - Add notes for the next phase
3. When satisfied, producer clicks **"Approve"**

**Approval triggers Phase 2 (Archive) to begin.**

---

## Phase 2: Archive Collection

### Overview

The Archive phase collects and processes all visual materials:
- Premium archive (Getty, Pond5, NASA)
- Reference footage and B-roll
- Interview recordings
- All footage logged with timecodes

### Step 1: Source Archive Footage

Work with your archive team to identify footage from:

**Track A: Premium Archive (via Quickture)**
- Getty Images/Footage
- Pond5
- NASA high-resolution scans
- Custom digitization of physical archives

**Track B: Reference/B-Roll (Direct Upload)**
- News clips
- Public domain footage
- NASA web downloads
- Interview rushes

### Step 2: Process Footage in Quickture

For premium archive footage:

1. Upload all footage to Quickture
2. Quickture automatically processes:
   - Full transcription/description of visual content
   - Metadata extraction (timecodes, shot descriptions, quality)
   - Scene segmentation
   - Keyword tagging
   - AI-generated content summary
3. Use **"Discuss Mode"** in Quickture to leave comments on specific footage
4. Export the archive log as CSV when complete

### Step 3: Import Quickture CSV

1. In the Episode Workspace, click the **"Archive"** tab
2. Click **"📥 Import Quickture CSV"**
3. Select your exported CSV file
4. The system parses the following columns:
   - Filename
   - Timecode_In
   - Timecode_Out
   - Description
   - Keywords
   - Technical_Notes
   - Getty_ID (if applicable)
5. Review the imported clips
6. Click **"Import"**

### Step 4: Process Interview Recordings

For interview footage:

1. Upload raw interview files to the system
2. The system automatically:
   - Transcribes audio using Gemini 2.0 Flash
   - Identifies speakers
   - Aligns text to timecodes
   - Tags emotional moments and key quotes
3. Review transcripts in the Archive tab

**Interview Transcript Format:**
```
[00:00:00] NASA ENGINEER #1
"When we first heard the explosion, the immediate thought was..."

[00:02:34] NASA ENGINEER #1
"The calculations we had to do in real-time, without computers..."

[Metadata: Emotional moment, technical explanation, suitable for voiceover bed]
```

### Step 5: Add Manual Archive Entries

To add archive footage not from Quickture:

1. Click **"+ Add Archive Log"**
2. Enter:
   - Source name
   - Source type (NASA API, direct upload, etc.)
   - Individual clips with timecodes
3. Click **"Save"**

### Step 6: Review and Approve

1. Verify all required footage is logged:
   - Check against research archive requirements
   - Ensure key moments have coverage
   - Flag any missing footage
2. Update phase status to **"Review"**
3. Producer reviews archive coverage
4. Producer clicks **"Approve"**

**Approval triggers Phase 3 (Script) to begin.**

---

## Phase 3: Script Generation

### Overview

The Script phase uses a 5-agent AI system to generate broadcast-quality scripts:

| Agent | Role |
|-------|------|
| 🔬 Research Specialist | Verifies facts, suggests structure |
| 📼 Archive Specialist | Matches footage to story beats |
| 💬 Interview Producer | Extracts best soundbites |
| 📝 Script Writer | Builds the narrative |
| ✅ Fact Checker | Verifies claims, creates citations |

### Step 1: Upload Reference Template

Before generating a script, upload your reference template:

1. In the Episode Workspace, click the **"Script"** tab
2. Click **"📄 Upload Template"**
3. Select your reference script template (e.g., NASA_Template.docx)
4. The template shows:
   - Ideal structure (VO, Interview, Archive, Gen AI sections)
   - Pacing and tone guidelines
   - Segment length targets

### Step 2: Generate Script with AI

1. Click **"🤖 Generate Script"**
2. The system executes the 5-agent swarm:

   **Agent 1: Research Specialist**
   - Analyzes research bucket
   - Suggests narrative structure
   - Identifies key facts to include

   **Agent 2: Archive Specialist**
   - Reviews archive logs
   - Matches footage to story moments
   - Flags missing visual coverage

   **Agent 3: Interview Producer**
   - Scans interview transcripts
   - Extracts powerful soundbites
   - Identifies emotional peaks

   **Agent 4: Script Writer**
   - Synthesizes all inputs
   - Writes voiceover narrative
   - Structures 5-7 story segments
   - Includes archive and interview references

   **Agent 5: Fact Checker**
   - Verifies every major claim
   - Flags statements needing legal review
   - Generates source citation log

3. Watch the **Agent Activity** panel to track progress
4. When complete, the V1 script appears in the Script tab

### Step 3: Review Generated Script

The script is formatted with clear sections:

```
SEGMENT 1: THE EXPLOSION

[VOICEOVER]
"On April 13, 1970, at 55 hours and 55 minutes into the mission,
the crew of Apollo 13 heard a loud bang..."

[ARCHIVE: Getty_NA_19700413_056A - Oxygen tank explosion simulation]

[ARCHIVE: NASA_Apollo13_MissionControl_Reaction]

[INTERVIEW: NASA Engineer #1 - 00:02:34]
"The calculations we had to do in real-time, without computers,
that was the real miracle..."

[ARCHIVE: NASA_Apollo13_FlightPath_Calculations]

[GEN AI VISUAL: Technical diagram - trajectory correction burn]
```

Review the script for:
- Narrative flow and story arc
- Accurate facts and dates
- Appropriate archive selections
- Strong interview soundbites
- Technical accuracy

### Step 4: Request Revisions (If Needed)

If sections need improvement:

1. Click on the segment needing revision
2. Click **"Request Revision"**
3. Enter your feedback, e.g.:
   - "Segment 3 needs more emotion, less technical detail"
   - "Replace Getty shot with NASA alternative"
   - "Add more interview content here"
4. Click **"Regenerate Section"**

The system responds to feedback:
- Interview Producer finds more emotive soundbites
- Script Writer adjusts tone
- Archive Specialist finds alternative footage
- Only the affected segment is regenerated

### Step 5: Version Control

Scripts progress through versions:

| Version | Description |
|---------|-------------|
| **V1** | Initial AI generation |
| **V2** | Post first producer review |
| **V3** | Post interview additions |
| **V4** | Final locked script |

To create a new version:
1. Make your edits or request regeneration
2. Click **"Save as New Version"**
3. Add version notes describing changes

### Step 6: Lock Final Script

When the script is approved:

1. Ensure all facts are verified
2. All archive references are confirmed
3. Interview selections are finalized
4. Click **"🔒 Lock as Final"**

**This creates version V4_locked and triggers Phase 4 (Voiceover).**

---

## Phase 4: Voiceover

### Overview

The Voiceover phase generates professional narration from the locked script using AI voice synthesis.

### Step 1: Automatic VO Extraction

Once the script is locked, the system automatically:
1. Extracts all [VOICEOVER] sections
2. Identifies segment boundaries
3. Notes timecode targets for pacing

### Step 2: Voice Generation

The Voiceover Specialist Agent:
1. Applies the series-specific voice profile (11 Labs)
2. Generates audio with appropriate pacing and emotion
3. Adds metadata (section reference, timecode target)

**Output:**
- Individual VO clips labeled by segment
- Master VO timeline document
- Audio files ready for Quickture import

### Step 3: Quality Control

Review generated voiceover for:
- Pronunciation of technical terms and names
- Pacing that fits intended archive sequences
- Tone consistency across the episode
- Natural breathing and pause placement

### Step 4: Approve and Deliver

1. Listen to all VO clips
2. Flag any requiring re-generation
3. When satisfied, click **"Approve"**
4. VO files are automatically delivered to Quickture

**Approval triggers Phase 5 (Assembly).**

---

## Phase 5: Final Assembly

### Overview

The Assembly phase brings everything together in Quickture for final editing.

### Step 1: Review Handoff Package

The system prepares a complete production package:

```
Episode_Production_Package/
├── Script_V4_LOCKED.docx
├── Archive_Log_with_timecodes.csv
├── Interview_selects_transcripts.txt
├── Voiceover_audio_files/ (by segment)
├── GenAI_visual_requirements.txt
├── Legal_compliance_checklist.pdf
└── Source_citations_log.csv
```

Access this package:
1. Click the **"Compliance"** tab
2. Click **"📦 Export Package"**
3. Download the complete package

### Step 2: Quickture Assembly

In Quickture:
1. Import the production package
2. Assemble rough cut following script structure
3. Place archive footage at indicated points
4. Insert interview clips at specified timecodes
5. Lay in voiceover audio
6. Add any Gen AI visuals as specified

### Step 3: Producer Review in Discuss Mode

Use Quickture's "Discuss Mode" for efficient feedback:

1. Series producer watches rough cut
2. Leaves frame-accurate comments directly on timeline:
   - "00:12:45 - This interview bite needs tightening"
   - "00:23:10 - Replace this Getty shot with NASA alternative"
3. AI assistant in Quickture can make instant adjustments
4. No traditional editor revision cycles needed

### Step 4: Final Delivery

Complete the following:
1. Lock picture edit
2. Complete audio mix
3. Generate deliverables for broadcast/streaming
4. Export final compliance package
5. Mark episode as **"Complete"**

---

## Managing Workflow Status

### Viewing Episode Status

1. Click **"Episodes"** in the sidebar
2. See all episodes with their current workflow phase
3. Color coding indicates status:
   - 🟢 Green: Completed phases
   - 🟡 Yellow: In review
   - 🔵 Blue: In progress
   - ⚪ Gray: Pending

### Updating Phase Status

To manually update a phase status:

1. Open the Episode Workspace
2. Click on the phase in the workflow progress bar
3. Select new status:
   - **Pending**: Not yet started
   - **In Progress**: Currently being worked on
   - **Review**: Submitted for producer review
   - **Approved**: Producer has approved
   - **Rejected**: Needs revision
4. Add any notes for the team
5. Click **"Update"**

### Workflow Progress Bar

The progress bar at the top of each episode shows:

```
[🔬 Research ✓] → [📼 Archive ✓] → [📝 Script ●] → [🎙️ VO ○] → [🎬 Assembly ○]
     Done            Done         In Progress     Pending       Pending
```

- ✓ = Completed (green)
- ● = In Progress (blue)
- ○ = Pending (gray)

---

## Compliance & Export

### Understanding Compliance Tracking

The system automatically tracks compliance for:

| Category | What's Tracked |
|----------|---------------|
| 📚 **Source Citations** | Every factual claim with source, date, URL |
| 📜 **Archive Licenses** | Clip usage, license type, clearance status |
| 🏷️ **EXIF Metadata** | AI model, prompt, generation date for Gen AI content |
| ⚖️ **Legal Signoffs** | Required approvals for sensitive content |

### Viewing Compliance Status

1. Open the Episode Workspace
2. Click the **"Compliance"** tab
3. View items organized by category
4. Status indicators show:
   - ✅ **Verified**: Confirmed and documented
   - 🟡 **Pending**: Awaiting verification
   - 🔴 **Flagged**: Requires attention

### Adding Compliance Items

To manually add a compliance item:

1. Click **"+ Add Item"**
2. Select type (Source Citation, Archive License, etc.)
3. Enter details:

   **For Source Citations:**
   - Claim text
   - Source document/URL
   - Retrieved date
   - Verification notes

   **For Archive Licenses:**
   - Clip ID
   - Usage location (episode, segment, timecode)
   - License type
   - Cleared by (name)

4. Set status
5. Click **"Save"**

### Exporting Compliance Package

For Fremantle legal/compliance sign-off:

1. Ensure all compliance items are verified
2. Click **"📦 Export Package"**
3. Select export format:
   - PDF (human-readable audit trail)
   - XML (machine-readable for archives)
4. Download the complete compliance package

**The package includes:**
- All AI fingerprints and metadata
- Source citations for every claim
- Archive license documentation
- Legal review status

---

## Tips & Best Practices

### Research Phase

- **Be thorough with the episode brief** - The more detail you provide, the better the AI research will be
- **Verify critical facts early** - Don't leave "requires confirmation" items until late in the process
- **Upload existing research** - If you have prior research, upload it before running the AI agent

### Archive Phase

- **Use Quickture's Discuss Mode** - Leave comments directly on footage for efficient communication
- **Log everything** - Even footage you might not use; it's better to have options
- **Check NASA API** - For NASA-related episodes, the system can auto-populate archive from their API

### Script Phase

- **Trust the swarm** - The 5-agent system is designed to work together; let it complete before making edits
- **Be specific with feedback** - "More emotion in Segment 3" is better than "make it better"
- **Use version control** - Don't overwrite; create new versions to maintain history

### General Workflow

- **Work in parallel** - While one episode is in Script review, start Research on the next
- **Monitor bottlenecks** - The dashboard shows episodes waiting on human review
- **Export compliance early** - Don't wait until the end; verify as you go

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + S` | Save current work |
| `Ctrl + Enter` | Submit for review |
| `Esc` | Close modal/panel |

---

## Troubleshooting

### AI Agent Stuck or Failed

If an AI agent task fails:
1. Check the Agent Activity panel for error messages
2. Try running the agent again
3. If it continues to fail, manually create the content

### CSV Import Errors

If Quickture CSV import fails:
1. Ensure column headers match expected format
2. Check for special characters in descriptions
3. Verify timecodes are in HH:MM:SS format

### Phase Won't Advance

If a phase is stuck:
1. Verify all required items are complete
2. Check for "Flagged" compliance items
3. Ensure the previous phase is fully approved

### Need Help?

Contact the Production Factory support team or check the [workflow.md](workflow.md) technical documentation for detailed API and implementation information.

---

## Quick Reference Card

### Episode Workflow Checklist

**Phase 1: Research**
- [ ] Upload episode brief
- [ ] Run AI Research Agent
- [ ] Review all documents
- [ ] Set confidence levels
- [ ] Submit for producer review
- [ ] Get approval

**Phase 2: Archive**
- [ ] Process footage in Quickture
- [ ] Export and import CSV
- [ ] Process interview recordings
- [ ] Review all clips logged
- [ ] Submit for producer review
- [ ] Get approval

**Phase 3: Script**
- [ ] Upload reference template
- [ ] Run Script Generation
- [ ] Review V1 draft
- [ ] Request revisions if needed
- [ ] Create V2, V3 as needed
- [ ] Lock as V4 final
- [ ] Get approval

**Phase 4: Voiceover**
- [ ] Review generated VO
- [ ] QC pronunciation/pacing
- [ ] Approve delivery to Quickture

**Phase 5: Assembly**
- [ ] Export production package
- [ ] Assemble in Quickture
- [ ] Producer review in Discuss Mode
- [ ] Final adjustments
- [ ] Lock picture and mix
- [ ] Export compliance package
- [ ] Mark complete

---

*Last updated: February 2025*
