# Personal Journal AI - User Flow & Experience Guide

## First Launch Experience

### 1. Initial App Opening
When a user first launches the Personal Journal app:

- **Window Opens**: Clean, minimalist interface (1200x800px)
- **Layout**: Left sidebar (always visible) + main content area
- **First View**: Home page with welcome message
- **No Login Required**: Completely local, instant access

### 2. Home Page (Landing)
**What Users See:**
```
Welcome to Your Journal
Express yourself in three different ways
```

**Three Cards Displayed:**
1. **Raw Transcription** (Indigo accent)
   - Icon: FileText
   - "Your exact words, unfiltered and authentic"
   
2. **Enhanced Style** (Pink accent)  
   - Icon: Sparkles
   - "Improved grammar and tone while preserving your intent"
   
3. **Structured Summary** (Orange accent)
   - Icon: LayoutList
   - "Organized into coherent themes and key points"

**Bottom Tip:**
- Gray card with tip: "💡 Click the plus button or press Ctrl+N to create a new entry"
- Sets expectation for the primary action

**Floating Plus Button:**
- Bottom-right corner
- Primary color (Indigo)
- Subtle shadow effect
- Always visible on every page

## Left Sidebar Navigation

**Always Visible Elements:**

### Top Section - Logo
- "Personal Journal" text
- Clean typography
- Creates brand consistency

### Navigation Items (Ghost buttons, full width):
1. **New Entry** (Plus icon)
   - First option, most important action
   - Redundant with floating button (accessibility)

2. **View Entries** (FileText icon)
   - Browse all journal entries
   - Opens split-view interface

3. **Talk to Your Diary** (MessageSquare icon)
   - AI-powered conversational interface
   - Voice-enabled reflection

4. **Pattern Insights** (Diamond icon)
   - **Initially Hidden**
   - Appears after 30 entries
   - Purple diamond indicates achievement

5. **Memories** (Calendar icon)
   - Date-based entry browsing
   - Export functionality

6. **Settings** (Settings icon)
   - Ollama configuration
   - Hotkey customization

### Bottom Section - Gamification
- "Daily Streak" label
- Badge showing "🔥 5 days" (orange accent)
- Motivates consistent use

## Core User Flows

### Flow 1: Creating First Entry

1. **User Clicks Plus Button** (or sidebar "New Entry")
   - Smooth page transition
   - Main area shows "New Entry" page

2. **New Entry Page Elements:**
   - Large text area with placeholder: "Hold [hotkey] to record one thought or idea..."
   - Microphone button (bottom-right of textarea)
   - Small text under mic: "Hold [hotkey]"
   - **First-time tooltip** near mic: "💡 Pro tip: Record one thought at a time for best results" (dismissible)
   
3. **Voice Recording Flow - Natural Paragraph Guidance:**
   
   **First Thought:**
   - User holds hotkey (or clicks and holds mic button)
   - **State 1**: Button turns red, pulses
   - Message: "Recording... Release [hotkey] to stop"
   - Red dot animation indicates active recording
   - User speaks their first thought
   - User releases hotkey
   - **State 2**: "Processing audio..." with spinner
   - **State 3**: "Converting speech to text..." with spinner
   - First thought appears in textarea
   - Brief success animation (subtle checkmark fade)
   - Message updates: "Great! Press [hotkey] again to add your next thought"
   
   **Subsequent Thoughts:**
   - User holds hotkey again for next idea
   - Same recording states repeat
   - New thought is added with visual separation (subtle line or spacing)
   - Counter shows: "2 thoughts recorded"
   - Encouraging message: "Thought captured! Add another?"
   - User continues adding thoughts as needed
   - Each thought is visually distinct in the text area
   
   **Long Recording Guidance:**
   - If user holds hotkey for 90+ seconds:
   - Gentle reminder appears: "Long thought? Try releasing and continuing with [hotkey]"
   - Not enforced, just suggested
   - Helps users discover the natural rhythm
   
   **Completion:**
   - User sees all their thoughts organized in the textarea
   - Can manually edit if desired
   - Clicks "Create All Three Entries" when satisfied
   
4. **Creating Entries:**
   - **State 4**: "Creating enhanced versions from all thoughts..." with spinner
   - All thoughts are sent together to Ollama for processing
   - **Success State**: 
     - Green checkmark appears
     - Toast notification: "✓ Entries created! Processed 3 thoughts into three formats"
   - Preview cards show all three versions of the complete entry

5. **Educational Reinforcement:**
   - Natural language throughout: "thought," "idea," "moment" instead of "paragraph"
   - Visual separation makes structure clear without being technical
   - Success animations after each thought reinforce the pattern
   - Help text in settings: "Voice recording works best when you pause between thoughts. Hold [hotkey] for each new idea, then release."

6. **Benefits Users Discover:**
   - Natural breaks between thoughts
   - Time to reflect between recordings
   - Better transcription accuracy
   - Organized structure emerges naturally
   - No stress about capturing everything at once

### Flow 2: Viewing & Browsing Entries

1. **User Clicks "View Entries"**
   - Split-view interface opens
   - Left panel: Entry list
   - Right panel: Entry details

2. **Entry List (Left Panel):**
   - Filter tabs: All | Raw | Enhanced | Structured
   - Entry cards show:
     - Mode badge
     - Date (e.g., "Jan 15")
     - First 3 lines of text
     - Time and word count

3. **Entry Selection:**
   - Click entry → Card gets primary color ring
   - Right panel updates with full entry
   - Shows all three versions in separate cards
   - Smooth transition animation

### Flow 3: Pattern Discovery (After 30 Entries)

1. **Diamond Icon Appears** in sidebar (with subtle glow animation)

2. **User Clicks Pattern Insights:**
   - Page shows large diamond icon at top
   - "Discovered patterns from your 30+ journal entries"

3. **Pattern Bubbles:**
   - Interactive buttons showing patterns:
     - "Productive mornings" (Brain icon)
     - "Weekend relaxation" (Calendar icon)
     - "Work stress Tuesdays" (TrendingUp icon)
   - Each shows occurrence count

4. **Pattern Selection:**
   - Click pattern → Highlights in primary color
   - Below: Example entries appear
   - Shows how pattern was detected

### Flow 4: Talk to Your Diary

1. **User Clicks "Talk to Your Diary"**
   - Clean interface with large mic button
   - Suggested questions displayed

2. **Voice Interaction:**
   - Click/hold mic button
   - Pulsing circle animation shows audio level
   - "You said:" card appears with transcript
   - "Thinking..." animation
   - "Your diary says:" response with speaker icon

3. **Quick Questions:**
   - Pre-written prompts user can click:
     - "How am I feeling today?"
     - "What patterns do you see?"
     - "Summarize this week"

### Flow 5: Settings Configuration

1. **Ollama Settings Card:**
   - Port input with "Test Connection" button
   - Success: Green checkmark + "✓ Ollama is connected and ready"
   - Model dropdown populated from Ollama

2. **Hotkey Configuration Card:**
   - Shows current hotkey (e.g., "F8")
   - "Change" button → "Press any key combination..."
   - Visual feedback when new hotkey is captured
   - "Save All Settings" button at bottom

### Flow 6: Buy Me a Coffee (Day 7)

1. **Trigger**: User opens app on/after day 7
2. **Popup Appears**:
   - Coffee and heart icons (animated pulse on heart)
   - "Enjoying Your Journal?"
   - "You've been using Personal Journal for 7 days!"
   - Acknowledges open-source nature

3. **User Options:**
   - "Buy Me a Coffee" → Opens donation link
   - "Maybe Later" → Dismisses for 30 days

## Animations & Micro-interactions

### Entry Animations
- Text appearing: Fade in from top
- Card selection: Scale up slightly (1.02x)
- Page transitions: Slide from right
- Success states: Check mark draw animation

### Recording Animations
- Mic button: Pulse when recording
- Audio level: Expanding circles around button
- Processing: Smooth spinner rotation
- Text appearance: Typewriter effect option

### Milestone Animations
- Pattern unlock: Confetti burst
- Streak badge: Flame flicker
- New entry created: Card slide-in

### Hover Effects
- Buttons: Lift up 1px with shadow
- Cards: Subtle shadow increase
- Sidebar items: Background color change

## Error States & Edge Cases

### No Entries Yet
- View Entries shows: "No entries yet. Create your first entry to get started!"
- Pattern Insights hidden until 30 entries

### Failed Transcription
- Error toast: "Failed to transcribe audio. Please try again."
- Text area remains editable for manual input

### Ollama Disconnected
- Settings shows red X
- Entry creation falls back to raw mode only

### Long Recording
- Each paragraph can be up to 2 minutes (plenty for a single thought)
- No limit on total number of paragraphs
- Natural breaks between thoughts prevent fatigue
- Better transcription accuracy with shorter segments

## Accessibility Features

### Keyboard Navigation
- Tab through all interactive elements
- Enter to activate buttons
- Escape to close modals
- Ctrl+N for new entry (global)

### Screen Reader Support
- Proper ARIA labels
- Status announcements for state changes
- Descriptive button text

### Visual Feedback
- High contrast mode option
- Clear focus indicators
- No color-only information

## Progressive Disclosure

### Day 1-6
- Core features available
- No popups or distractions
- Focus on habit building

### Day 7+
- Coffee popup (once)
- Gentle reminder of value

### Entry 30+
- Pattern insights unlock
- Celebration moment
- New depth of interaction

### Entry 100+
- Advanced patterns
- Relationship mapping (future)
- Mood correlation charts (future)

## Success Metrics

### Engagement Indicators
- Daily streak maintenance
- Entry length increasing
- Pattern views after unlock
- "Talk to Diary" usage

### Value Indicators
- 7-day retention
- 30-entry achievement
- Coffee support conversion
- Export usage (backup behavior)

## Emotional Journey

### First Week: Discovery
- "This is simple and private"
- "Voice input is magical"
- "Three perspectives are insightful"

### First Month: Habit
- "Part of my daily routine"
- "Patterns are fascinating"
- "I understand myself better"

### Long Term: Growth
- "My thoughts have evolved"
- "I can see my progress"
- "This diary knows me"

---

This user flow creates a journey from curious user to dedicated journaler, with each interaction designed to build trust, provide value, and encourage reflection.