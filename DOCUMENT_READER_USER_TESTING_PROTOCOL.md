# Document Reader Workflow - User Testing Protocol

## Overview

This protocol provides a comprehensive framework for conducting user testing sessions with 5 participants to validate the Document Reader workflow redesign.

**Testing Duration**: 60-75 minutes per session
**Number of Participants**: 5 users
**Location**: Remote (video conferencing) or In-person
**Recording**: Screen + audio recording required
**Artifacts**: Session notes, SUS score, task completion metrics

---

## 1. Participant Recruitment

### 1.1 Target User Profile

**Essential Criteria**:
- Regular computer user (30+ hours/week)
- Works with documents regularly (reads/analyzes PDFs, reports, articles)
- Comfortable learning new software
- Age: 25-60 years

**Preferred Criteria** (3 of 5 participants should have):
- Experience with document management systems (Zotero, Mendeley, Paperpile)
- Academic or research background
- Uses AI chat tools (ChatGPT, Claude, etc.)
- Has 100+ documents in personal collection

**Exclusion Criteria**:
- Current PyGPT power users (want fresh perspective)
- Software developers (unrepresentative of target audience)
- Participants who've seen previous versions (avoid preconception bias)

### 1.2 Recruitment Channels

- University email lists (students, faculty)
- LinkedIn professional groups (researchers, analysts)
- Local community boards (remote workers, freelancers)
- Existing customer database (non-power users)
- UserTesting.com or similar platform (screened)

### 1.3 Compensation

- **Standard Rate**: $75 USD for 75 minutes
- **Premium Rate**: $100 USD for industry professionals/academics
- **Students**: $50 USD + extra credit (if applicable)
- **Payment Method**: Gift card, PayPal, or direct deposit

---

## 2. Testing Environment Setup

### 2.1 Hardware Requirements

**Test Facilitator**:
- Computer with screen recording capability
- Reliable internet connection (20+ Mbps upload)
- Secondary monitor for notes
- Quality microphone and headphones

**Participant**:
- Computer (Windows 10+, macOS 11+, Linux Ubuntu 20+)
- Minimum 1920x1080 resolution
- Microphone and webcam (for remote)
- Mouse (touchpad acceptable but note in report)

### 2.2 Software Requirements

**Test System**:
- PyGPT with Document Reader features installed
- Test document library (15 sample documents provided)
- Screen recording software (OBS or equivalent)
- Video conferencing (Zoom, Google Meet, Teams)
- Survey tool (Typeform, Google Forms, Qualtrics)

**Sample Document Library**:
```
Sample_Documents/
├── Research/
│   ├── machine_learning_overview.pdf (45 pages)
│   ├── quantum_computing_basics.pdf (32 pages)
│   └── AI_ethics_research_paper.pdf (28 pages)
├── Reports/
│   ├── Q3_Financial_Report_2024.pdf (78 pages)
│   ├── Project_Status_Summary.docx (12 pages)
│   └── Technical_Specifications.html (24 pages)
├── Personal/
│   ├── Investment_Portfolio_Review.pdf (15 pages)
│   ├── Home_Renovation_Checklist.txt
│   └── Family_Recipe_Collection.pdf (8 pages)
├── Presentations/
│   ├── PyGPT_Document_Viewer_Demo.pptx (36 slides)
│   └── Data_Visualization_Best_Practices.pdf (22 pages)
├── Readings/
│   ├── Philosophy_of_Science_2024.pdf (156 pages)
│   ├── Python_Best_Practices.md (156 lines)
│   └── Climate_Change_Report_2024.pdf (245 pages)
└── Mixed/
    ├── contract_template_with_notes.pdf (annotations)
    └── scanned_document_image.png (OCR text layer)
```

### 2.3 Pilot Test

**Conduct 1-2 pilot sessions** with team members:
- Test script timing (target: 60-75 minutes)
- Identify confusing instructions
- Verify sample documents are appropriate
- Check recording quality
- Refine questions and prompts

---

## 3. Testing Script

### 3.1 Introduction (5 minutes)

**Facilitator Script**:

```
"Thank you for joining today. I'm [name] and I'll be your test facilitator.

Today we're testing a new Document Reader feature in PyGPT, a tool that helps
users read, organize, and work with their documents using AI assistance.

There are no right or wrong answers - we're testing the software, not you.
If something doesn't make sense or doesn't work as you expect, that's valuable
feedback for us.

I'll ask you to complete several tasks while thinking aloud, explaining what
you're looking for and what you're thinking as you use the system.

The session will be recorded for analysis, but your personal information will
be kept confidential. Do you have any questions before we start?"
```

**Participant Consent Form**:
- [ ] I consent to being recorded (screen + audio)
- [ ] I understand my data will be kept confidential
- [ ] I can stop the test at any time
- [ ] I consent to my anonymized feedback being used in product improvements

**Participant Background Questions** (2 minutes):

1. What's your occupation or field of study?
2. How many documents (PDFs, Word files, reports) do you work with each week?
3. What tools do you currently use to organize documents?
4. Have you used AI chat tools before? (ChatGPT, Claude, etc.)

---

### 3.2 Task 1: Document Import & Index (10 minutes)

**Scenario**:
"You've just downloaded 5 research papers from arXiv and want to import them
into your document library so you can search through them and ask questions
using AI."

**Test Documents Provided**:
- `arxiv_paper_1.pdf`
- `arxiv_paper_2.pdf`
- `arxiv_paper_3.pdf`
- `arxiv_paper_4.pdf`
- `arxiv_paper_5.pdf`

**Tasks**:
1. Import all 5 papers into the document library
2. Enable indexing so you can search within them
3. Check that they were imported successfully

**What to Observe**:
- Can user find the import functionality? (drag-drop vs button)
- Does user enable indexing? (clearly visible option)
- Does user verify import? (progress indication, completion notification)
- Any errors or confusion?

**Post-Task Questions**:
- How easy was it to import multiple documents?
- Did you understand what "indexing" means and does?
- What was confusing or unclear?

**Success Criteria**:
- [ ] All 5 documents appear in library
- [ ] Indexing is enabled (status shows "indexed")
- [ ] User can articulate what indexing does

---

### 3.3 Task 2: Document Reading & Navigation (12 minutes)

**Scenario**:
"Open the document 'machine_learning_overview.pdf' and find the section about
neural networks. You want to highlight an important sentence and add a note."

**Tasks**:
1. Open the machine learning document
2. Navigate to the table of contents/bookmarks
3. Find the "Neural Networks" section
4. Highlight a sentence in that section
5. Add a note: "Important for Q3 research"
6. Navigate to the next page (any method)

**What to Observe**:
- How does user open the document? (double-click, context menu, shortcut?)
- Can they find navigation controls? (thumbnails, bookmarks, page controls)
- Do they discover search functionality? (makes task easier)
- Can they figure out highlighting? (intuitive selection + highlight button?)
- How do they add a note? (right-click, annotation panel?)

**Post-Task Questions**:
- How was the reading experience? Smooth? Laggy?
- Were the navigation controls easy to find?
- How did highlighting and notes work for you?
- What would make reading documents easier?

**Success Criteria**:
- [ ] Document opens successfully
- [ ] Navigates to neural networks section
- [ ] Creates at least one highlight
- [ ] Creates at least one note
- [ ] Moves to next page

---

### 3.4 Task 3: In-Document Search (10 minutes)

**Scenario**:
"You're looking for mentions of "gradient descent" in the machine learning
paper to understand a concept better. Find all mentions and read through them."

**Tasks**:
1. Search for "gradient descent" in the current document
2. Navigate through all search results
3. Close the search panel when done

**What to Observe**:
- How does user initiate search? (Ctrl+F, toolbar button, menu?)
- Can they navigate through results? (Next/Previous buttons, Enter key?)
- Are search results clearly highlighted?
- Do they get lost or stuck in search mode?

**Post-Task Questions**:
- How effective was the search?
- Were you able to find all mentions easily?
- Did the search results highlighting help?
- What would improve the search experience?

**Success Criteria**:
- [ ] Search returns at least 3 results
- [ ] User navigates to at least 2 different matches
- [ ] Successfully closes search panel

---

### 3.5 Task 4: Document Management & Organization (12 minutes)

**Scenario**:
"Your library is getting cluttered. Organize your documents by creating
folders for your projects and moving documents into them."

**Tasks**:
1. Create a new folder called "Research Papers"
2. Create another folder called "Financial Reports"
3. Move the 3 research papers (in Sample_Documents/Research/) to the "Research Papers" folder
4. Move the financial report to the "Financial Reports" folder
5. Delete the "scanned_document_image.png" from your library

**What to Observe**:
- Can user find "create folder" functionality? (button, context menu, shortcut?)
- Do they use drag-drop or menu actions for moving documents?
- Can they select multiple documents at once? (Ctrl+Click, Shift+Click?)
- Do they get confirmation for delete action?
- Any issues with bulk operations?

**Post-Task Questions**:
- How easy was it to organize your documents?
- Did you find the folder structure intuitive?
- How was selecting multiple documents?
- What would make document management easier?

**Success Criteria**:
- [ ] Two folders created with correct names
- [ ] Documents moved to appropriate folders
- [ ] Scanned document deleted
- [ ] User can navigate folder structure

---

### 3.6 Task 5: AI Integration - Chat with Document (10 minutes)

**Scenario**:
"Now you'd like to ask questions about the AI ethics paper. Attach it to your
chat and ask: 'What are the main ethical concerns discussed in this paper?'"

**Tasks**:
1. Find the AI ethics research paper
2. Attach it to the current chat
3. Ask the AI about the main ethical concerns
4. After getting an answer, find a specific quote that supports the answer

**What to Observe**:
- Can user find "attach" functionality? (context menu, toolbar, shortcut?)
- Do they understand what attaching does?
- Can they have a natural conversation with the AI about the document?
- Does the AI provide useful, document-based answers?

**Post-Task Questions**:
- How useful was the AI integration?
- Did the AI understand the document content?
- How helpful were the answers?
- What other AI features would be valuable?

**Success Criteria**:
- [ ] Document successfully attached to chat
- [ ] AI provides relevant answer about ethics
- [ ] User finds supporting quote (shows engagement)

---

### 3.7 Free Exploration (5 minutes)

**Scenario**:
"You now have about 5 minutes to explore the Document Reader feature on your
own. Try out any features we didn't cover, or explore anything that caught your
interest. Please keep talking about what you're trying and what you discover."

**What to Observe**:
- What features do they explore first? (shows priorities)
- Do they discover advanced features on their own?
- Any frustration or confusion?
- What do they comment on positively/negatively?

**Note**: Don't guide or direct - just observe and take notes

---

### 3.8 Post-Testing Questionnaire (5 minutes)

**System Usability Scale (SUS)**

Instructions: Please rate your agreement with these statements on a scale of 1-5:
(1 = Strongly Disagree, 5 = Strongly Agree)

| # | Question | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| 1 | I think that I would like to use this system frequently | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 | I found the system unnecessarily complex | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | I thought the system was easy to use | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 | I think that I would need the support of a technical person to be able to use this system | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | I found the various functions in this system were well integrated | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 | I thought there was too much inconsistency in this system | ☐ | ☐ | ☐ | ☐ | ☐ |
| 7 | I would imagine that most people would learn to use this system very quickly | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 | I found the system very cumbersome to use | ☐ | ☐ | ☐ | ☐ | ☐ |
| 9 | I felt very confident using the system | ☐ | ☐ | ☐ | ☐ | ☐ |
| 10 | I needed to learn a lot of things before I could get going with this system | ☐ | ☐ | ☐ | ☐ | ☐ |

**Calculation**: SUS Score = ((sum of scores) - 10) * 2.5
**Benchmark**: 68 = average, 80+ = excellent

**Task-Based Questions**:

Rate each workflow (1-5, 1 = Very Difficult, 5 = Very Easy):

1. **Import Workflow**: How easy was importing documents?
   - Score: ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5
   - Comments: _________________________________

2. **Reading Workflow**: How was the document reading experience?
   - Score: ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5
   - Comments: _________________________________

3. **Navigation**: How easy was navigating within documents?
   - Score: ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5
   - Comments: _________________________________

4. **Management**: How easy was managing and organizing documents?
   - Score: ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5
   - Comments: _________________________________

5. **AI Integration**: How useful was the AI integration?
   - Score: ☐ 1 ☐ 2 ☐ 3 ☐ 4 ☐ 5
   - Comments: _________________________________

---

### 3.9 Debrief Interview (5 minutes)

**Open-Ended Questions**:

1. **Overall Impressions**:
   - "What were your first impressions of the Document Reader?"
   - "What did you like most about it?"
   - "What frustrated you the most?"

2. **Workflow-Specific**:
   - "How does this compare to tools you currently use?"
   - "What features would you use most often?"
   - "What features were missing that you'd expect?"

3. **AI Integration**:
   - "How helpful was the AI in understanding documents?"
   - "What other AI features would you want?"
   - "Were you confident the AI understood the document?"

4. **Learning Curve**:
   - "How long do you think it would take to become proficient?"
   - "What would help you learn the features faster?"
   - "Where would you look for help if you got stuck?"

5. **Final Thoughts**:
   - "On a scale of 1-10, how likely are you to use this regularly?"
   - "Who do you think would benefit most from this tool?"
   - "Would you recommend this to a colleague?"

---

## 4. Data Collection & Metrics

### 4.1 Quantitative Metrics

#### Task Completion Rate

| Task | Completion Rate | Avg Time | Min/Max Time | Error Rate |
|---|---|---|---|---|
| Import & Index | X/5 (%) | XM | XS-XL | X/5 (%) |
| Reading & Navigation | X/5 (%) | XM | XS-XL | X/5 (%) |
| In-Document Search | X/5 (%) | XM | XS-XL | X/5 (%) |
| Document Management | X/5 (%) | XM | XS-XL | X/5 (%) |
| AI Integration | X/5 (%) | XM | XS-XL | X/5 (%) |

**Success Criteria**: 80% completion rate for each task

#### Efficiency Metrics

- **Time on Task**: Average time to complete each task
- **Number of Clicks**: Count of clicks/taps to complete task
- **Number of Errors**: Mis-clicks, wrong navigation, etc.
- **Help Requests**: How many times user asked for assistance
- **Backtracks**: Navigation to wrong screen then back

#### SUS Scores

Calculate for each participant:
```
SUS Score = ((sum of 10 responses) - 10) * 2.5
```

**Benchmarks**:
- Individual: 68+
- Median (5 users): 75+
- Range: Should not exceed 25 points (e.g., 60-85)

**Overall Score**:
- Excellent: 85+
- Good: 70-84
- Acceptable: 50-69
- Poor: < 50

### 4.2 Qualitative Observations

#### Problem Areas

| Area | Examples | Severity (1-5) |
|---|---|---|
| Feature Discovery | Couldn't find search, didn't see zoom controls | |
| Conceptual Model | Didn't understand indexing, confused about AI | |
| Navigation | Got lost, couldn't go back, wrong clicks | |
| Terminology | "Index" unclear, "attach" confusing | |
| Visual Design | Icons unclear, contrast issues, too small | |

#### Unexpected Behaviors

Note any behavior that reveals mental models:
- Clicked on non-interactive elements
- Used keyboard shortcuts not documented
- Tried features that don't exist (shows expectations)
- Used workarounds instead of intended path

#### Quotes

Record exact quotes from participants:
- "I thought clicking here would..."
- "Oh, I didn't expect it to..."
- "It would be better if..."
- "I like how it..."

### 4.3 NASA-TLX (Optional - for deeper analysis)

If time permits, include NASA Task Load Index for each major task:

**Scale: 0-100**

1. Mental Demand: How much mental activity was required?
2. Physical Demand: How much physical activity was required?
3. Temporal Demand: How much time pressure?
4. Performance: How successful were you?
5. Effort: How hard did you work?
6. Frustration: How insecure/discouraged were you?

Calculation: Average of 6 subscales

---

## 5. Data Analysis Framework

### 5.1 SUS Score Analysis

**Calculate for Each Participant**:

```python
def calculate_sus(responses):
    # responses: list of 10 integers (1-5)
    total = sum(responses)
    sus_score = (total - 10) * 2.5
    return sus_score

# Example
participant_1 = [4, 2, 4, 1, 4, 2, 4, 2, 4, 1]  # Mixed responses
sus_1 = calculate_sus(participant_1)  # 72.5 (Good)
```

**Adjective Rating Scale**:
Convert SUS to qualitative descriptor:

| SUS Score | Adjective | Interpretation |
|---|---|---|
| 90+ | Best Imaginable | Exceptional |
| 85-89 | Excellent | Outstanding |
| 80-84 | Good | Better than average |
| 70-79 | OK | Average |
| 60-69 | Poor | Below average |
| 50-59 | Bad | Needs improvement |
| < 50 | Worst Imaginable | Critical issues |

**Sample Size Adjustments**:
- 5 users: ±20 point confidence interval
- Interpret trends rather than exact numbers
- Focus on patterns across participants

### 5.2 Task Completion Matrix

**Create Matrix**:

| User | T1 Import | T2 Read | T3 Search | T4 Manage | T5 AI |
|---|---|---|---|---|---|
| P1 | ✓ (6min) | ✓ (8min) | ✓ (5min) | ✓ (9min) | ✓ (6min) |
| P2 | ✓ (8min) | ✕ | ✓ (7min) | ✓ (11min) | ✓ (8min) |
| P3 | ✓ (5min) | ✓ (10min) | ✓ (4min) | ✓ (8min) | ✓ (5min) |
| P4 | ✓ (9min) | ✓ (9min) | ✓ (6min) | ✓ (10min) | ✓ (7min) |
| P5 | ✓ (7min) | ✓ (7min) | ✕ | ✓ (12min) | ✓ (9min) |

**Calculate**:
- Completion Rate: Tasks completed / Total tasks
- Avg Time: Average across successful completions
- Error Rate: Failed tasks / Total attempts

### 5.3 Qualitative Analysis - Thematic Coding

**Step 1**: Transcribe observations and quotes
**Step 2**: Identify themes across participants
**Step 3**: Categorize by theme and severity

**Example Themes**:

| Theme | Frequency | Severity | Examples | Priority |
|---|---|---|---|---|
| Indexing confusion | 3/5 (60%) | High | "What does index mean?" | P0 |
| Hidden search | 2/5 (40%) | Medium | Couldn't find Ctrl+F | P1 |
| Zoom frustration | 2/5 (40%) | Low | "Zoom buttons are too small" | P2 |
| Good highlighting | 5/5 (100%) | Positive | "Highlighting is great!" | Keep |

**Priority Matrix**:

| High Impact/High Frequency (P0) | High Impact/Low Frequency (P1) |
|---|---|
| Fix immediately | Consider for next sprint |

| Low Impact/High Frequency (P2) | Low Impact/Low Frequency (P3) |
|---|---|
| Add to backlog | Monitor or ignore |

### 5.4 Affinity Diagramming

**Group Similar Findings**:

```
Indexing Confusion (3 users)
├── "Don't know what index means" (P2, P4)
├── Thought indexing = saving (P1, P5)
└── Expected auto-index by default (P3, P4)

Search Discovery (2 users)
├── Looked for magnifying glass (P3)
├── Tried Ctrl+F without looking (P1)
└── Asked "Where is search?" (P5)

Positive Feedback (5 users)
├── "Love thumbnails" (P1, P2, P3)
├── "Keyboard shortcuts helpful" (P4)
└── "AI answers were accurate" (P5)
```

---

## 6. Reporting & Iteration Plan

### 6.1 Executive Summary Template

**One-Page Summary**:

```
DOCUMENT READER USER TESTING RESULTS
Test Date: [Date]
Participants: 5 users
Duration: 60-75 minutes each

KEY FINDINGS
• Overall SUS Score: 78/100 (Good)
• Task Completion: 84% average
• Most Difficult: Search feature discovery
• Most Liked: Document highlighting
• Critical Issue: Indexing terminology confusion

RECOMMENDATIONS
1. Rename "Index" to "Make Searchable" (P0)
2. Add search button to main toolbar (P1)
3. Improve onboarding for first-time users (P1)
4. Keep highlighting/annotation system as-is (working well)

NEXT STEPS
• Week 1: Implement P0 fixes
• Week 2: Address P1 feedback
• Week 3: Retest with 3 new users
• Week 4: Launch beta to power users
```

### 6.2 Detailed Report Structure

**Full Report** (5-10 pages):

1. **Executive Summary** (1 page)
   - Key findings and recommendations
   - SUS score and interpretation
   - Go/no-go decision

2. **Methodology** (1 page)
   - Participant demographics
   - Testing environment
   - Tasks performed

3. **Results** (3-5 pages)
   - Task completion rates
   - SUS scores by participant
   - Thematic analysis findings
   - Key quotes

4. **Recommendations** (1-2 pages)
   - Prioritized list of changes
   - Quick wins vs. major changes
   - Timeline estimates

5. **Appendices**
   - Detailed task metrics
   - SUS calculations
   - Transcript excerpts
   - Screenshots/problem areas

### 6.3 Iteration Planning

**Priority 0 (Fix Immediately)**:
- Affects majority of users
- Blocks critical workflows
- High severity (data loss, confusion)
- Quick to fix (< 1 day)

**Priority 1 (Next Sprint)**:
- Affects subset of users
- Moderate impact
- Medium effort (1-3 days)

**Priority 2 (Backlog)**:
- Minor inconvenience
- Low frequency
- Can wait for feature update

**Priority 3 (Monitor)**:
- One user mention
- Subjective preference
- May not be issue for others

**Example Implementation Plan**:

**Week 1 (P0 Fixes)**:
- [ ] Change "Index" to "Make Searchable"
- [ ] Add tooltip explaining indexing with benefits
- [ ] Make search button more prominent in toolbar
- [ ] Fix crash when deleting read-only documents

**Week 2 (P1 Improvements)**:
- [ ] Add "Getting Started" overlay for first-time users
- [ ] Increase size of zoom controls
- [ ] Add keyboard shortcuts to menu items (display)
- [ ] Improve progress bar visibility during import

**Week 3 (Testing)**:
- [ ] Fix any bugs introduced
- [ ] Conduct follow-up tests with 3 users
- [ ] Verify P0/P1 issues resolved
- [ ] Collect SUS scores for comparison

**Week 4 (Deployment Prep)**:
- [ ] Polish UI based on feedback
- [ ] Update documentation
- [ ] Create help articles
- [ ] Beta release to 10 power users

---

## 7. Testing Checklist

### Pre-Test Setup

- [ ] Install PyGPT with Document Reader features
- [ ] Load sample document library (15 documents)
- [ ] Test 5 arXiv PDFs for import task
- [ ] Verify screen recording works
- [ ] Test microphone and audio quality
- [ ] Open test survey/form for SUS
- [ ] Prepare informed consent form
- [ ] Prepare participant payment/gift card

### During Test

- [ ] Record participant consent
- [ ] Record screen and audio
- [ ] Take notes on task completion times
- [ ] Note errors and workarounds
- [ ] Record exact quotes
- [ ] Note non-verbal cues (confusion, frustration, delight)
- [ ] Keep neutral - don't help unless critical
- [ ] Track time to stay within 75 minutes

### Post-Test

- [ ] Save recording with participant ID
- [ ] Transfer files to secure storage
- [ ] Complete observation notes
- [ ] Calculate SUS score
- [ ] Update task completion matrix
- [ ] Send thank you email with payment
- [ ] De-identify data for analysis

### Analysis & Reporting

- [ ] Transcribe key observations
- [ ] Calculate aggregate metrics
- [ ] Identify themes across participants
- [ ] Create affinity diagrams
- [ ] Write executive summary
- [ ] Prioritize issues
- [ ] Create iteration plan
- [ ] Schedule stakeholder review meeting

---

## 8. Tools & Templates

### 8.1 Consent Form Template

```
PYGPT DOCUMENT READER USER TESTING CONSENT

Purpose: Test new Document Reader features
Duration: 60-75 minutes
Recording: Screen and audio will be recorded

Your Rights:
✓ You can stop at any time without penalty
✓ Your data will be kept confidential
✓ Only anonymized data will be used in reports
✓ You can request to delete your data

Compensation: $75 (or equivalent) for completion

By signing, I consent to participate in this study:

Participant: _________________ Date: ______
Facilitator: _________________ Date: ______
```

### 8.2 Note-Taking Template

```
Session #: ___ Participant: ___ Date: ___
Duration: ___ Facilitator: ___

PRE-TEST BACKGROUND:
● Occupation: ___
● Document usage: ___ files/week
● Tools mentioned: ___
● AI experience: Y/N

TASK 1: IMPORT (10 min target)
Start: ___ End: ___ Duration: ___
□ Completed □ Partial □ Failed
Notes:
- ___

TASK 2: READING (12 min target)
Start: ___ End: ___ Duration: ___
□ Completed □ Partial □ Failed
Notes:
- ___

[... continue for all tasks ...]

OVERALL OBSERVATIONS:
Major issues: ___
Positive feedback: ___
Quotes to remember: ___

SUS SCORE: ___/100
Qualitative: ___
```

### 8.3 Excel/Google Sheets Template

**Columns**:
Participant ID | Task | Completed | Time | Errors | Help Requests | Notes | Severity

**Pivot Tables**:
- Completion rate by task
- Average time by task
- Error count by type
- Severity distribution

---

## 9. Best Practices

### 9.1 Facilitator Guidelines

**DO**:
- ✓ Read script verbatim for consistency
- ✓ Ask "What are you thinking?" when user is silent
- ✓ Write down exact quotes immediately
- ✓ Note non-verbal cues (facial expressions, hesitation)
- ✓ Thank participant for feedback, positive or negative
- ✓ Keep neutral body language - don't lead user
- ✓ Run a pilot test first

**DON'T**:
- ✗ Help user complete tasks (unless critical)
- ✗ Explain how things work (that's what we're testing!)
- ✗ React visibly to user mistakes or confusion
- ✗ Ask leading questions ("You like the search, right?")
- ✗ Skip tasks due to time (adjust script instead)
- ✗ Record without explicit consent

### 9.2 Participant Comfort

**Build Rapport**:
- Start with casual conversation
- Emphasize we're testing software, not them
- Praise helpful feedback (not performance)
- Offer breaks if session runs long
- Provide water/coffee if in-person

**Handle Frustration**:
- "It's okay, this is helpful feedback"
- "You're doing great - this is very useful"
- Offer to move on if stuck > 3 minutes
- Remind them they can stop anytime

### 9.3 Data Integrity

- Keep recordings secure (encrypted storage)
- Use participant IDs, not names, in analysis
- Backup recordings immediately after session
- De-identify quotes in reports
- Get permission to share specific quotes
- Follow GDPR/CCPA if applicable

---

## 10. References

**SUS (System Usability Scale)**:
- Brooke, J. (1996). "SUS: A 'quick and dirty' usability scale"
- Adjective Rating: Bangor, A., et al. (2009)

**NASA-TLX**:
- Hart, S. G. (2006). "NASA-Task Load Index (NASA-TLX); 20 Years Later"

**Usability Testing Resources**:
- Nielsen, J. (1994). "Guerrilla HCI: Using Discount Usability Engineering"
- Krug, S. (2014). "Don't Make Me Think, Revisited"
- Rubin, J., & Chisnell, D. (2008). "Handbook of Usability Testing"

**Sample Size**:
- Nielsen, J. (2000). "Why You Only Need to Test with 5 Users"

---

Version: 1.0
Date: 2025-01-20
Status: Draft
Next Review: After 2 test sessions
Contact: Document Reader Team
