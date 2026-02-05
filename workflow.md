# Production Factory: Complete Workflow Implementation

This document explains how "THE PRODUCTION FACTORY: COMPLETE WORKFLOW SPECIFICATION" is implemented in the UI, mapping each specification requirement to its corresponding implementation.

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Phase 1: Research](#phase-1-research)
4. [Phase 2: Archive](#phase-2-archive)
5. [Phase 3: Script Generation](#phase-3-script-generation)
6. [Phase 4: Voiceover](#phase-4-voiceover)
7. [Phase 5: Assembly](#phase-5-assembly)
8. [Workflow State Management](#workflow-state-management)
9. [AI Agent Architecture](#ai-agent-architecture)
10. [Compliance System](#compliance-system)
11. [API Reference](#api-reference)
12. [UI Components](#ui-components)

---

## Overview

### Specification Goal
The Production Factory is designed to produce **90 episodes** across **3 series** with **18 simultaneous edits** operational. The system reduces human time per episode from 40+ hours to ~4 hours through AI automation.

### UI Implementation
The system is implemented as a Flask web application with a modern dark-themed interface at `/templates/index.html`. Key components:

| Spec Requirement | UI Implementation |
|------------------|-------------------|
| 3 Series x 30 Episodes | Hierarchical navigation: Projects → Series → Episodes |
| 5-Phase Workflow | Visual workflow progress bar with phase tabs |
| Agent Swarm | Backend orchestration via `/api/ai/script-swarm` |
| Compliance Tracking | Dedicated Compliance tab with export functionality |

### Workflow Phases

```
WORKFLOW_PHASES = {
    research:  { order: 1, icon: '🔬', color: 'blue' },
    archive:   { order: 2, icon: '📼', color: 'purple' },
    script:    { order: 3, icon: '📝', color: 'green' },
    voiceover: { order: 4, icon: '🎙️', color: 'orange' },
    assembly:  { order: 5, icon: '🎬', color: 'red' }
}
```

**File:** `templates/index.html:255-261`

---

## Project Structure

### Specification Hierarchy
```
Project
└── Series (×3)
    └── Episodes (×30)
        ├── Research Bucket
        ├── Archive Bucket
        ├── Script Workspace
        └── Compliance Package
```

### UI Implementation

#### Navigation Sidebar
The sidebar provides navigation across all workflow phases:

```javascript
const PHASES = [
    { id: 'episodes', name: 'Episodes', icon: '🎬' },
    { id: 'research', name: 'Research', icon: '🔬' },
    { id: 'archive', name: 'Archive', icon: '📼' },
    { id: 'scripting', name: 'Scripting', icon: '📝' },
    { id: 'interviews', name: 'Interviews', icon: '💬' },
    { id: 'production', name: 'Production', icon: '🎥' },
    { id: 'compliance', name: 'Compliance', icon: '✅' }
];
```

**File:** `templates/index.html:263-271`

#### Episode Creation with Factory Structure
When an episode is created via the factory endpoint, it automatically initializes all buckets:

```python
# POST /api/episodes/factory
episode_data = {
    'workflow': {
        'currentPhase': 'research',
        'phases': {
            'research': {'status': 'in_progress', 'startedAt': timestamp},
            'archive': {'status': 'pending'},
            'script': {'status': 'pending'},
            'voiceover': {'status': 'pending'},
            'assembly': {'status': 'pending'}
        }
    },
    'researchBucket': {
        'uploadedDocuments': [],
        'agentOutputs': [],
        'factCheckSources': [],
        'notebookLMSource': None
    },
    'archiveBucket': {
        'quicktureLogs': [],
        'nasaMetadata': [],
        'interviewTranscripts': [],
        'referenceFootage': []
    },
    'scriptWorkspace': {
        'referenceTemplate': None,
        'currentVersion': None,
        'versionHistory': [],
        'producerFeedback': []
    },
    'compliancePackage': {
        'exifMetadataLogs': [],
        'sourceCitations': [],
        'archiveLicenses': [],
        'legalSignoff': None
    }
}
```

**File:** `app.py:251-291`

---

## Phase 1: Research

### Specification Requirements

| Requirement | Description |
|-------------|-------------|
| Episode Brief Upload | One-paragraph summary, 3-5 key story beats, target interviewees, archive requirements |
| Research Agent | Generates 10-15 research questions, timeline of key events, technical concepts, archive categories |
| Research Execution | Perplexity API, NASA API, NotebookLM integration, web search |
| Research Output | Timeline document, technical briefing, character profiles, archive requirements, fact-check foundation, interview question bank |
| Human Review Gate | 48 hours for series producer review |

### UI Implementation

#### Research Tab Component
Located within the Episode Workspace, the Research tab displays:

```html
<!-- Research Documents List -->
<div class="research-documents">
    <!-- Document cards with type badges -->
    <div class="document-card">
        <span class="type-badge">uploaded | agent_output | fact_check</span>
        <span class="confidence">verified | probable | requires_confirmation</span>
        <div class="document-title">{title}</div>
        <div class="document-content">{content preview}</div>
    </div>
</div>

<!-- Action Buttons -->
<button onclick="triggerResearchAgent()">🤖 AI Research</button>
<button onclick="showAddDocumentModal()">📄 Add Document</button>
```

**File:** `templates/index.html:1306-1353`

#### Research Document Types
```python
RESEARCH_DOC_TYPES = ['uploaded', 'agent_output', 'fact_check', 'notebooklm']
CONFIDENCE_LEVELS = ['verified', 'probable', 'requires_confirmation']
```

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes/{id}/research-bucket` | GET | Get all research documents |
| `/api/research-documents` | POST | Create research document |
| `/api/research-documents/{id}` | PUT | Update confidence level |
| `/api/research-documents/{id}` | DELETE | Remove document |

**File:** `app.py:2852-2897`

#### Research Agent Execution
The Research Specialist agent analyzes the episode brief and generates:

```python
# Agent 1: Research Specialist
{
    'name': 'Research Specialist',
    'role': 'Foundation & Fact Accuracy',
    'responsibilities': [
        'Verify timeline accuracy',
        'Ensure technical explanations are correct',
        'Flag claims requiring interview corroboration',
        'Suggest narrative structure based on story beats'
    ]
}
```

**File:** `app.py:88-113`

---

## Phase 2: Archive

### Specification Requirements

| Requirement | Description |
|-------------|-------------|
| Track A: Premium Archive | Getty Images, Pond5, NASA high-res scans, custom digitization |
| Track B: Reference/B-Roll | News clips, public domain, NASA web downloads, interview rushes |
| Quickture Processing | Full transcription, metadata extraction, scene segmentation, keyword tagging |
| Archive Log Import | CSV with Filename, Timecode_In, Timecode_Out, Description, Keywords, Technical_Notes, Getty_ID |
| Interview Rush Processing | Auto-transcription via Gemini 2.0 Flash, speaker identification, timecode alignment |

### UI Implementation

#### Archive Tab Component

```html
<!-- Archive Logs Display -->
<div class="archive-logs">
    <div class="log-card">
        <div class="log-title">{source_name}</div>
        <div class="clip-count">{clips.length} clips</div>
        <div class="clips-list">
            <!-- Individual clips with timecodes -->
            <div class="clip">
                <span class="timecode">{timecode_in} - {timecode_out}</span>
                <span class="description">{description}</span>
                <span class="keywords">{keywords}</span>
            </div>
        </div>
    </div>
</div>

<!-- Import Actions -->
<button onclick="importQuicktureCsv()">📥 Import Quickture CSV</button>
<button onclick="showAddArchiveModal()">➕ Add Archive Log</button>
```

**File:** `templates/index.html:1355-1394`

#### Quickture CSV Import
The system parses Quickture export files with the following column mapping:

```python
# POST /api/archive-logs/import-csv
csv_columns = ['Filename', 'Timecode_In', 'Timecode_Out',
               'Description', 'Keywords', 'Technical_Notes', 'Getty_ID']

# Clips are grouped by filename into archive log entries
archive_log = {
    'episode_id': episode_id,
    'source_name': filename,
    'source_type': 'quickture',
    'clips': [
        {
            'timecode_in': row['Timecode_In'],
            'timecode_out': row['Timecode_Out'],
            'description': row['Description'],
            'keywords': row['Keywords'].split(','),
            'technical_notes': row['Technical_Notes'],
            'getty_id': row.get('Getty_ID')
        }
    ]
}
```

**File:** `app.py:2899-2977`

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes/{id}/archive-logs` | GET | Get all archive logs |
| `/api/archive-logs` | POST | Create archive log entry |
| `/api/archive-logs/import-csv` | POST | Import Quickture CSV export |
| `/api/archive-logs/{id}` | DELETE | Delete archive log |

#### Interview Transcript Processing
Transcripts are stored with speaker identification and timecodes:

```python
transcript_structure = {
    'episode_id': episode_id,
    'interviewee_name': 'NASA Engineer #1',
    'duration_minutes': 45,
    'transcript_text': '[00:00:00] NASA ENGINEER #1\n"When we first heard..."',
    'segments': [
        {
            'timecode': '00:00:00',
            'speaker': 'NASA Engineer #1',
            'text': 'When we first heard the explosion...',
            'metadata': ['emotional_moment', 'technical_explanation']
        }
    ]
}
```

**File:** `app.py:2979-3025`

---

## Phase 3: Script Generation

### Specification Requirements

| Requirement | Description |
|-------------|-------------|
| 5-Agent Swarm | Research Specialist, Archive Specialist, Interview Producer, Script Writer, Fact Checker |
| Input Documents | Reference template, research package, archive logs, interview transcripts, series bible |
| Generation Process | Structure generation → Content population → Assembly |
| Human Review Gate | 72 hours for producer review |
| Version Control | V1 (initial), V2 (producer review), V3 (interview additions), V4 (locked) |

### UI Implementation

#### Script Tab Component

```html
<!-- Script Versions List -->
<div class="script-versions">
    <div class="version-card" data-status="{status}">
        <div class="version-header">
            <span class="version-number">V{version_number}</span>
            <span class="version-type">{version_type}</span>
            <span class="status-badge">{status}</span>
        </div>
        <div class="script-content">{content rendered as markdown}</div>
        <button onclick="lockAsFinal(id)">🔒 Lock as Final</button>
    </div>
</div>

<!-- Agent Activity Monitor -->
<div class="agent-activity">
    <h4>Recent Agent Activity</h4>
    <div class="task-list">
        <!-- Last 5 agent tasks -->
        <div class="task-item">
            <span class="agent-name">{agent_type}</span>
            <span class="task-status">{status}</span>
            <span class="timestamp">{completedAt}</span>
        </div>
    </div>
</div>

<!-- Generation Actions -->
<button onclick="triggerScriptSwarm()">🤖 Generate Script</button>
<button onclick="showAddVersionModal()">📝 Add Version</button>
```

**File:** `templates/index.html:1396-1481`

#### Script Version Types
```python
SCRIPT_VERSION_TYPES = [
    'V1_initial',           # AI-generated first draft
    'V2_producer_review',   # Post first producer review
    'V3_interview_additions', # After interview content added
    'V4_locked'             # Final locked script
]
```

**File:** `app.py:85`

#### Multi-Agent Script Swarm

The script generation uses a coordinated 5-agent architecture:

```python
# POST /api/ai/script-swarm
async def script_swarm(episode_id, project_id):
    # 1. Gather all input materials
    research_docs = get_research_documents(episode_id)
    archive_logs = get_archive_logs(episode_id)
    transcripts = get_transcripts(episode_id)

    # 2. Execute agents in sequence
    agents = [
        ('research_specialist', 'Analyze research, suggest structure'),
        ('archive_specialist', 'Match archive to story beats'),
        ('interview_producer', 'Extract best soundbites'),
        ('script_writer', 'Generate full script'),
        ('fact_checker', 'Verify claims, generate citations')
    ]

    outputs = {}
    for agent_type, task_description in agents:
        task = create_agent_task(episode_id, agent_type, task_description)
        result = await execute_agent(agent_type, {
            'episode': episode,
            'research': research_docs,
            'archive': archive_logs,
            'transcripts': transcripts,
            'previous_outputs': outputs
        })
        outputs[agent_type] = result
        update_agent_task(task.id, 'completed', result)

    # 3. Create script version from final output
    create_script_version(
        episode_id=episode_id,
        version_type='V1_initial',
        content=outputs['script_writer'],
        agent_outputs=outputs
    )

    # 4. Auto-create compliance items from fact-checker
    for citation in outputs['fact_checker']['citations']:
        create_compliance_item(
            episode_id=episode_id,
            item_type='source_citation',
            content=citation
        )
```

**File:** `app.py:3220-3435`

#### Agent Roles Detail

| Agent | Role | Access To | Responsibilities |
|-------|------|-----------|------------------|
| Research Specialist | Foundation & Fact Accuracy | Research Package | Verify timeline, ensure technical accuracy, flag claims needing corroboration, suggest structure |
| Archive Specialist | Visual Storytelling | Archive logs, NASA metadata, Getty catalog | Match archive to script moments, identify visual sequences, flag missing footage |
| Interview Producer | Human Voices & Emotional Beats | Interview transcripts, question bank | Extract best soundbites, identify emotional peaks, match to script structure |
| Script Writer | Narrative Construction | All above + reference template | Build VO narrative, structure story arc, write to broadcast standards |
| Fact Checker | Verification & Compliance | All research sources + web search | Cross-reference claims, flag legal issues, verify dates/names, generate citation log |

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes/{id}/script-versions` | GET | Get version history |
| `/api/script-versions` | POST | Create new version |
| `/api/script-versions/{id}` | PUT | Update version |
| `/api/script-versions/{id}/lock` | POST | Lock as final (V4) |
| `/api/ai/script-swarm` | POST | Execute multi-agent script generation |

**File:** `app.py:3028-3099`

---

## Phase 4: Voiceover

### Specification Requirements

| Requirement | Description |
|-------------|-------------|
| Trigger | Script is locked (V4_locked) |
| VO Generation | Extract text, apply voice profile (11 Labs), generate audio with pacing/emotion |
| Output | Individual VO clips by segment, master VO timeline, delivery to Quickture |
| Quality Control | Pronunciation check, pacing verification, tone consistency, breathing/pause placement |

### UI Implementation

The Voiceover phase is managed through the workflow state system. When the script phase is marked as approved:

```python
# Automatic phase progression
def update_phase_status(episode_id, phase, new_status, notes=None):
    if new_status == 'approved':
        # Mark current phase complete
        episode.workflow.phases[phase].status = 'approved'
        episode.workflow.phases[phase].completedAt = timestamp
        episode.workflow.phases[phase].reviewNotes = notes

        # Advance to next phase
        next_phase = get_next_phase(phase)  # script -> voiceover
        episode.workflow.currentPhase = next_phase
        episode.workflow.phases[next_phase].status = 'in_progress'
        episode.workflow.phases[next_phase].startedAt = timestamp
```

**File:** `app.py:188-220`

#### Workflow Progress Bar
The visual progress indicator shows the current phase status:

```html
<div class="workflow-progress">
    <!-- Phase indicators -->
    <div class="phase" data-phase="research" data-status="approved">
        <span class="icon">🔬</span>
        <span class="status">✓</span>
    </div>
    <span class="arrow">→</span>
    <div class="phase" data-phase="archive" data-status="approved">
        <span class="icon">📼</span>
        <span class="status">✓</span>
    </div>
    <span class="arrow">→</span>
    <div class="phase" data-phase="script" data-status="approved">
        <span class="icon">📝</span>
        <span class="status">✓</span>
    </div>
    <span class="arrow">→</span>
    <div class="phase" data-phase="voiceover" data-status="in_progress">
        <span class="icon">🎙️</span>
        <span class="status">In Progress</span>
    </div>
    <span class="arrow">→</span>
    <div class="phase" data-phase="assembly" data-status="pending">
        <span class="icon">🎬</span>
        <span class="status">Pending</span>
    </div>
</div>
```

**File:** `templates/index.html:1241-1260`

---

## Phase 5: Assembly

### Specification Requirements

| Requirement | Description |
|-------------|-------------|
| Handoff Package | Locked script, archive log with timecodes, interview selects, VO audio files, GenAI visual requirements, compliance checklist, source citations |
| Quickture Production | Assemble rough cut, series producer review in "Discuss Mode", frame-accurate comments |
| Final Output | Locked picture, audio mix, broadcast/streaming deliverables |

### UI Implementation

The Assembly phase represents the handoff to Quickture for final editing. The system provides an export function that packages all materials:

```python
# GET /api/episodes/{id}/compliance/export
def export_compliance_package(episode_id):
    episode = get_episode(episode_id)
    compliance_items = get_compliance_items(episode_id)

    return {
        'episode': episode,
        'script': get_locked_script(episode_id),
        'compliance': {
            'source_citations': filter_by_type(compliance_items, 'source_citation'),
            'archive_licenses': filter_by_type(compliance_items, 'archive_license'),
            'exif_metadata': filter_by_type(compliance_items, 'exif_metadata'),
            'legal_signoffs': filter_by_type(compliance_items, 'legal_signoff')
        },
        'archive_logs': get_archive_logs(episode_id),
        'generated_at': timestamp
    }
```

**File:** `app.py:3103-3169`

---

## Workflow State Management

### Frontend State Structure

```javascript
const state = {
    // Collection data
    projects: [],
    episodes: [],
    series: [],

    // Current selections
    currentProject: null,
    currentSeries: null,

    // Episode workspace state
    selectedEpisode: null,
    episodeWorkspace: {
        activeTab: 'research',  // research | archive | script | compliance
        workflow: {},           // Current workflow status
        researchDocs: [],       // Research bucket documents
        archiveLogs: [],        // Archive bucket logs
        transcripts: [],        // Interview transcripts
        scriptVersions: [],     // Script version history
        complianceItems: [],    // Compliance tracking items
        agentTasks: []          // AI agent execution history
    }
};
```

**File:** `templates/index.html:226-251`

### Phase Status Values

```python
PHASE_STATUSES = ['pending', 'in_progress', 'review', 'approved', 'rejected']
```

**File:** `app.py:82`

### Workflow Progression Logic

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   pending   │ ──→ │ in_progress │ ──→ │   review    │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                          ┌───────────────────┼───────────────────┐
                          ▼                   │                   ▼
                    ┌─────────────┐           │             ┌─────────────┐
                    │  approved   │           │             │  rejected   │
                    └─────────────┘           │             └─────────────┘
                          │                   │                   │
                          ▼                   │                   ▼
                    [Next Phase]              │          [Revision Loop]
                    starts as                 │          back to in_progress
                    in_progress               │
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects/{id}/workflow-overview` | GET | All episodes with workflow status |
| `/api/episodes/{id}/workflow` | GET | Detailed workflow for single episode |
| `/api/episodes/{id}/workflow/phase` | PUT | Update phase status |
| `/api/projects/{id}/dashboard` | GET | Project statistics including phase analytics |

**File:** `app.py:2780-2848`

---

## AI Agent Architecture

### Agent Types Configuration

```python
AGENT_TYPES = {
    'research_specialist': {
        'name': 'Research Specialist',
        'role': 'Foundation & Fact Accuracy',
        'responsibilities': [
            'Verify timeline accuracy',
            'Ensure technical explanations are correct',
            'Flag claims requiring interview corroboration',
            'Suggest narrative structure based on story beats'
        ]
    },
    'archive_specialist': {
        'name': 'Archive Specialist',
        'role': 'Visual Storytelling',
        'responsibilities': [
            'Match archive to script moments',
            'Identify visual sequences for key story beats',
            'Flag missing footage that needs B-roll generation',
            'Suggest pacing based on available footage'
        ]
    },
    'interview_producer': {
        'name': 'Interview Producer',
        'role': 'Human Voices & Emotional Beats',
        'responsibilities': [
            'Extract best soundbites from interviews',
            'Identify emotional peaks in testimony',
            'Match interview content to script structure',
            'Suggest interview questions for gaps'
        ]
    },
    'script_writer': {
        'name': 'Script Writer',
        'role': 'Narrative Construction',
        'responsibilities': [
            'Build voiceover narrative',
            'Structure story arc (setup, complication, resolution)',
            'Write to broadcast documentary standards',
            'Match tone to series bible'
        ]
    },
    'fact_checker': {
        'name': 'Fact Checker',
        'role': 'Verification & Compliance',
        'responsibilities': [
            'Cross-reference every major claim',
            'Flag statements requiring legal review',
            'Verify dates, names, technical specifications',
            'Generate source citation log for compliance'
        ]
    }
}
```

**File:** `app.py:88-113`

### Agent Task Tracking

Each agent task is recorded for audit and debugging:

```python
agent_task = {
    'id': unique_id,
    'episode_id': episode_id,
    'agent_type': 'script_writer',
    'agent_info': AGENT_TYPES['script_writer'],
    'task_type': 'generate_script',
    'input_context': {
        'research_docs_count': 15,
        'archive_logs_count': 3,
        'transcript_count': 4
    },
    'output': {
        'script_content': '...',
        'segment_count': 7,
        'archive_references': [...]
    },
    'status': 'completed',  # pending | in_progress | completed | failed
    'startedAt': timestamp,
    'completedAt': timestamp,
    'error': None
}
```

**File:** `app.py:308-339`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes/{id}/agent-tasks` | GET | Get all agent task history |
| `/api/agent-tasks` | POST | Create new agent task |
| `/api/agent-tasks/{id}` | PUT | Update task status |
| `/api/ai/script-swarm` | POST | Execute multi-agent script generation |
| `/api/ai/research-agent` | POST | Execute research analysis |

**File:** `app.py:3173-3217`

---

## Compliance System

### Specification Requirements

| Requirement | Description |
|-------------|-------------|
| EXIF/Metadata Fingerprinting | Every AI-generated asset includes model, prompt, reference IDs, generation date, user, license, training disclaimer |
| Source Citation Log | Claim, source, retrieved date, URL, verification cross-reference |
| Archive Asset Tracking | Clip ID, usage location, license type, cleared by, metadata embedding |
| Compliance Export | One-click generation of full production audit trail for Fremantle legal/compliance |

### UI Implementation

#### Compliance Tab Component

```html
<!-- Compliance Categories Grid -->
<div class="compliance-grid">
    <div class="category-card" data-type="source_citation">
        <span class="icon">📚</span>
        <h4>Source Citations</h4>
        <span class="count">{count}</span>
    </div>
    <div class="category-card" data-type="archive_license">
        <span class="icon">📜</span>
        <h4>Archive Licenses</h4>
        <span class="count">{count}</span>
    </div>
    <div class="category-card" data-type="exif_metadata">
        <span class="icon">🏷️</span>
        <h4>EXIF Metadata</h4>
        <span class="count">{count}</span>
    </div>
    <div class="category-card" data-type="legal_signoff">
        <span class="icon">⚖️</span>
        <h4>Legal Signoffs</h4>
        <span class="count">{count}</span>
    </div>
</div>

<!-- Recent Items List -->
<div class="compliance-items">
    <div class="item" data-status="{status}">
        <span class="type-badge">{item_type}</span>
        <span class="status-indicator">{verified | pending | flagged}</span>
        <div class="content">{content}</div>
    </div>
</div>

<!-- Export Action -->
<button onclick="exportCompliancePackage()">📦 Export Package</button>
```

**File:** `templates/index.html:1483-1541`

#### Compliance Item Types

```python
COMPLIANCE_TYPES = ['source_citation', 'archive_license', 'exif_metadata', 'legal_signoff']
COMPLIANCE_STATUSES = ['pending', 'verified', 'flagged']
```

#### Source Citation Structure

```python
source_citation = {
    'episode_id': episode_id,
    'item_type': 'source_citation',
    'content': {
        'claim': 'Apollo 13 explosion occurred at 55:55:55 mission time',
        'source': 'NASA Mission Report Apollo 13, Page 47',
        'retrieved_date': '2025-02-01',
        'url': 'https://nasa.gov/apollo13/mission-report.pdf',
        'verification': 'Cross-checked with Houston Chronicle April 14, 1970'
    },
    'status': 'verified'
}
```

#### Archive License Structure

```python
archive_license = {
    'episode_id': episode_id,
    'item_type': 'archive_license',
    'content': {
        'clip_id': 'Getty_NA_19700413_056A',
        'usage': 'Episode 3, Segment 1, 00:02:34-00:02:51',
        'license_type': 'Getty Images Standard Broadcast License',
        'cleared_by': 'Sarah Dello',
        'cleared_date': '2025-02-03',
        'metadata_embedded': True
    },
    'status': 'verified'
}
```

#### EXIF Metadata Structure (for AI-generated content)

```python
exif_metadata = {
    'episode_id': episode_id,
    'item_type': 'exif_metadata',
    'content': {
        'asset_type': 'gen_ai_visual',
        'model': 'Gemini 2.0 Flash',
        'prompt': 'Technical diagram - trajectory correction burn',
        'reference_images': [],
        'generation_date': '2025-02-05',
        'user': 'Sam Wilkinson / Arrow Media',
        'license': 'AI Generated - Arrow Media Production',
        'training_disclaimer': 'No copyrighted material used as reference'
    },
    'status': 'verified'
}
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes/{id}/compliance` | GET | Get all compliance items |
| `/api/compliance` | POST | Create compliance item |
| `/api/compliance/{id}` | PUT | Update compliance item |
| `/api/episodes/{id}/compliance/export` | GET | Export grouped compliance package |

**File:** `app.py:3103-3169`

---

## API Reference

### Core Endpoints

#### Projects
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects` | GET | List all projects |
| `/api/projects` | POST | Create project |
| `/api/projects/{id}` | GET | Get project details |
| `/api/projects/{id}/dashboard` | GET | Project dashboard with stats |
| `/api/projects/{id}/workflow-overview` | GET | All episodes workflow status |

#### Series
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/series` | GET | List all series |
| `/api/series` | POST | Create series |
| `/api/series/{id}` | GET | Get series details |

#### Episodes
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes` | GET | List episodes (filter by series_id) |
| `/api/episodes` | POST | Create episode |
| `/api/episodes/factory` | POST | Create episode with Production Factory structure |
| `/api/episodes/{id}` | GET | Get episode details |
| `/api/episodes/{id}/workflow` | GET | Get workflow status |
| `/api/episodes/{id}/workflow/phase` | PUT | Update phase status |

#### Research
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes/{id}/research-bucket` | GET | Get research documents |
| `/api/research-documents` | POST | Create research document |
| `/api/research-documents/{id}` | PUT | Update document |
| `/api/research-documents/{id}` | DELETE | Delete document |

#### Archive
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes/{id}/archive-logs` | GET | Get archive logs |
| `/api/archive-logs` | POST | Create archive log |
| `/api/archive-logs/import-csv` | POST | Import Quickture CSV |
| `/api/archive-logs/{id}` | DELETE | Delete archive log |

#### Scripts
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes/{id}/script-versions` | GET | Get version history |
| `/api/script-versions` | POST | Create script version |
| `/api/script-versions/{id}` | PUT | Update version |
| `/api/script-versions/{id}/lock` | POST | Lock as final |

#### Compliance
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes/{id}/compliance` | GET | Get compliance items |
| `/api/compliance` | POST | Create compliance item |
| `/api/compliance/{id}` | PUT | Update item |
| `/api/episodes/{id}/compliance/export` | GET | Export package |

#### AI Agents
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/episodes/{id}/agent-tasks` | GET | Get agent task history |
| `/api/agent-tasks` | POST | Create agent task |
| `/api/agent-tasks/{id}` | PUT | Update task status |
| `/api/ai/script-swarm` | POST | Execute script generation |
| `/api/ai/research-agent` | POST | Execute research analysis |

---

## UI Components

### 1. Project Dashboard
- Visual overview of all episodes (90 total)
- Status indicators: Research / Archive / Script / VO / Quickture
- Bottleneck alerts (episodes waiting on human review)
- Phase distribution charts

**File:** `templates/index.html:1175-1206`

### 2. Episode Workspace
- Tabbed interface: Research / Archive / Script / Compliance
- Upload documents to research bucket
- View archive logs with Quickture "Discuss Mode" links
- Script editor with agent suggestions
- Version comparison view

**File:** `templates/index.html:1208-1280`

### 3. Script Generation Interface
- Reference template viewer (side panel)
- Agent activity monitor (shows which agent is working)
- Segment-by-segment review
- Inline feedback mechanism
- One-click regeneration of specific sections

**File:** `templates/index.html:1396-1481`

### 4. Compliance Dashboard
- Asset usage tracking
- Missing metadata alerts
- Export audit trail (PDF + XML format)
- Legal review status

**File:** `templates/index.html:1483-1541`

### 5. Workflow Progress Bar
Visual indicator showing:
- All 5 phases in sequence with icons
- Current phase highlighted
- Completed phases with green checkmarks (✓)
- In-review phases with yellow labels
- Pending phases with reduced opacity
- Arrows connecting phases

**File:** `templates/index.html:1241-1260`

---

## Data Flow Summary

```
1. Episode Creation
   └─> POST /api/episodes/factory
       └─> Initialize workflow + 4 buckets
           └─> Create empty collections for each bucket

2. Research Phase
   └─> POST /api/ai/research-agent OR manual upload
       └─> Create research_documents
           └─> Set confidence levels (verified/probable/requires_confirmation)
               └─> Producer reviews
                   └─> Mark phase ready for review
                       └─> Approve → triggers Phase 2

3. Archive Phase
   └─> POST /api/archive-logs/import-csv (from Quickture)
       └─> Parse clips and create archive_logs
           └─> Process interview transcripts
               └─> Display in Archive Tab
                   └─> Producer reviews archive coverage
                       └─> Approve → triggers Phase 3

4. Script Phase
   └─> POST /api/ai/script-swarm
       └─> Create 5 agent tasks in sequence
           └─> Agent 1 (Research Specialist) analyzes research
               └─> Agent 2 (Archive Specialist) maps footage
                   └─> Agent 3 (Interview Producer) extracts soundbites
                       └─> Agent 4 (Script Writer) synthesizes V1 script
                           └─> Agent 5 (Fact Checker) verifies claims
                               └─> Create script_version (V1_initial)
                                   └─> Auto-create compliance items
                                       └─> Producer reviews (72hr gate)
                                           └─> Revision loop or approve
                                               └─> Lock as V4_locked
                                                   └─> Approve → triggers Phase 4

5. Voiceover Phase
   └─> Extract VO text from locked script
       └─> Generate audio via 11 Labs API
           └─> Quality control checks
               └─> Deliver to Quickture
                   └─> Approve → triggers Phase 5

6. Assembly Phase
   └─> Export production package
       └─> Quickture assembles rough cut
           └─> Producer review in "Discuss Mode"
               └─> Frame-accurate feedback
                   └─> Final adjustments
                       └─> Locked picture + audio mix
                           └─> Compliance package export
                               └─> Delivery
```

---

## Environment Configuration

### Required Environment Variables

```bash
# Google Cloud
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1

# Vertex AI
MODEL_NAME=gemini-2.0-flash-001

# Storage
STORAGE_BUCKET=your-bucket-name

# Application
APP_VERSION=1.0.0
APP_ENV=dev  # 'dev' or 'prod'
```

### Collection Prefix Logic

The system uses different Firestore collection prefixes based on environment:

```python
if os.getenv('APP_ENV') == 'dev':
    COLLECTION_PREFIX = 'dev_'  # e.g., dev_doc_episodes
else:
    COLLECTION_PREFIX = ''      # e.g., doc_episodes
```

This enables separate development and production data stores.

**File:** `app.py:26-48`

---

## Success Metrics (from Specification)

### Velocity
- Episode research: 24 hours (automated)
- Archive processing: 48 hours (Quickture + import)
- Script generation: 4-6 hours (agent swarm + producer review)
- Total: 5-7 days per episode vs 4-6 weeks traditional

### Quality
- 99%+ fact-check accuracy (verified sources)
- Zero compliance violations (automated metadata)
- 30% fewer revision cycles (Quickture Discuss Mode)

### Scale
- 18 simultaneous edits operational by April
- 90 episodes delivered by June 2025
- System ready for future series without rebuild

---

## Bottleneck Management

| Phase | Processing | Bottleneck |
|-------|------------|------------|
| Phase 1 & 2 | Fully automated | Unlimited parallel processing |
| Phase 3 | AI + Human | Limited by 48-72hr review gates |
| Phase 4 & 5 | Quickture | Limited by 18 edit seat capacity |

### Human Touch Points
- Series producer approves research (once per episode, 30 mins)
- Series producer reviews draft script (once per episode, 1-2 hours)
- Series producer final review in Quickture (once per episode, 1 hour)

**Total human time per episode: ~4 hours vs traditional 40+ hours**
