# How to Create the Architecture Diagram in Draw.io

This guide walks you through creating a professional architecture diagram for IAM Job Scout using draw.io (free).

## Step 1: Open Draw.io

1. Go to **https://app.diagrams.net** (this is draw.io)
2. Click **"Create New Diagram"**
3. Choose **"Blank Diagram"**
4. Name it: `iam-job-scout-architecture`
5. Click **"Create"**

## Step 2: Set Up Your Canvas

1. Go to **File → Page Setup**
2. Set size to **Landscape** and **Letter** or **A4**
3. Enable **Grid** (View → Grid) for alignment

## Step 3: Create the Layers (Top to Bottom)

Your diagram should have these layers from top to bottom:

```
┌─────────────────────────────────────────┐
│           1. CLIENT LAYER               │  (Blue)
├─────────────────────────────────────────┤
│           2. WEB LAYER                  │  (Green)
├─────────────────────────────────────────┤
│           3. SERVICE LAYER              │  (Purple)
├─────────────────────────────────────────┤
│           4. SEARCH LAYER               │  (Orange)
├─────────────────────────────────────────┤
│           5. DATA LAYER                 │  (Yellow)
├─────────────────────────────────────────┤
│           6. EXTERNAL APIs              │  (Gray)
└─────────────────────────────────────────┘
```

## Step 4: Add Components (Copy These Exactly)

### Layer 1: Client Layer (Use Blue - #3B82F6)
Add these shapes:
- **Rectangle with rounded corners**: "Web Browser"

### Layer 2: Web Layer (Use Green - #10B981)
Add these shapes:
- **Rectangle**: "FastAPI Application"
- **Rectangle**: "Jinja2 Templates"
- **Rectangle**: "Static Files (CSS/JS)"
- **Rectangle**: "Prometheus Metrics"

### Layer 3: Service Layer (Use Purple - #8B5CF6)
Add these shapes:
- **Rectangle**: "JobService"
- **Rectangle**: "SchedulerService (APScheduler)"

### Layer 4: Search Layer (Use Orange - #F59E0B)
Add these shapes:
- **Rectangle**: "APIManager"
- **Rectangle**: "JSearchAPI (18 queries)"
- **Rectangle**: "AdzunaAPI (14 queries)"
- **Rectangle**: "RemoteOKAPI (1 query)"
- **Rectangle**: "JobDeduplicator"
- **Rectangle**: "JobFilter"

### Layer 5: Data Layer (Use Yellow - #FCD34D)
Add these shapes:
- **Cylinder** (database shape): "SQLite / PostgreSQL"
- **Rectangle**: "SQLAlchemy ORM"

### Layer 6: External APIs (Use Gray - #6B7280)
Add these shapes:
- **Cloud shape**: "JSearch (RapidAPI)"
- **Cloud shape**: "Adzuna API"
- **Cloud shape**: "RemoteOK API"

## Step 5: Draw the Connections (Arrows)

Use these arrow connections:

```
Web Browser
    ↓
FastAPI Application ←→ Jinja2 Templates
    ↓                ←→ Static Files
    ↓                ←→ Prometheus Metrics
JobService
    ↓
SchedulerService (triggers scans)
    ↓
APIManager
    ↓
┌───────────┼───────────┐
↓           ↓           ↓
JSearchAPI  AdzunaAPI   RemoteOKAPI
↓           ↓           ↓
JSearch     Adzuna      RemoteOK
(external)  (external)  (external)
    ↓           ↓           ↓
    └───────────┼───────────┘
                ↓
        JobDeduplicator
                ↓
          JobFilter
                ↓
        SQLAlchemy ORM
                ↓
        SQLite/PostgreSQL
```

## Step 6: Style Your Diagram

### Colors to Use:
| Component | Fill Color | Border Color | Text Color |
|-----------|------------|--------------|------------|
| Client | #DBEAFE | #3B82F6 | #1E40AF |
| Web | #D1FAE5 | #10B981 | #065F46 |
| Service | #EDE9FE | #8B5CF6 | #5B21B6 |
| Search | #FEF3C7 | #F59E0B | #92400E |
| Data | #FEF9C3 | #EAB308 | #713F12 |
| External | #F3F4F6 | #6B7280 | #374151 |

### Arrow Style:
- Color: **#374151** (dark gray)
- Style: **Solid line**
- End: **Classic arrow**
- Width: **2pt**

## Step 7: Add a Title and Legend

### Title (Top of diagram):
```
IAM Job Scout - System Architecture
```
Font: **Bold, 24pt**

### Legend (Bottom right corner):
Create small colored squares with labels:
- 🔵 Client Layer
- 🟢 Web Layer
- 🟣 Service Layer
- 🟠 Search Layer
- 🟡 Data Layer
- ⚫ External Services

## Step 8: Export Your Diagram

1. Go to **File → Export as → PNG**
2. Set **Zoom: 200%** (for high quality)
3. Enable **Transparent Background** (optional)
4. Click **Export**
5. Save as `architecture.png`

## Step 9: Add to Your Project

1. Move the PNG file to: `docs/architecture.png`
2. Add to README.md:
```markdown
## Architecture

![IAM Job Scout Architecture](docs/architecture.png)
```

## Quick Reference: Shape Locations in Draw.io

| Shape | Where to Find |
|-------|---------------|
| Rectangle | General → Rectangle |
| Rounded Rectangle | General → Rounded Rectangle |
| Cylinder (Database) | General → Cylinder |
| Cloud | General → Cloud |
| Arrow | Click shape, drag blue arrow to another shape |

## Pro Tips

1. **Align shapes**: Select multiple → Arrange → Align → Center
2. **Same size**: Select multiple → Arrange → Match Size
3. **Group layers**: Select all in a layer → Right-click → Group
4. **Copy style**: Right-click shape → Copy Style, then Paste Style

## Sample Layout Dimensions

```
┌────────────────────────────────────────────────────────────┐
│  Title: IAM Job Scout Architecture        (y: 20px)        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────┐  (y: 80px)      │
│  │         CLIENT LAYER                  │  Height: 60px   │
│  └──────────────────────────────────────┘                  │
│                      ↓                                     │
│  ┌──────────────────────────────────────┐  (y: 160px)     │
│  │         WEB LAYER                     │  Height: 80px   │
│  └──────────────────────────────────────┘                  │
│                      ↓                                     │
│  ┌──────────────────────────────────────┐  (y: 260px)     │
│  │         SERVICE LAYER                 │  Height: 80px   │
│  └──────────────────────────────────────┘                  │
│                      ↓                                     │
│  ┌──────────────────────────────────────┐  (y: 360px)     │
│  │         SEARCH LAYER                  │  Height: 120px  │
│  └──────────────────────────────────────┘                  │
│                      ↓                                     │
│  ┌──────────────────────────────────────┐  (y: 500px)     │
│  │         DATA LAYER                    │  Height: 80px   │
│  └──────────────────────────────────────┘                  │
│                      ↓                                     │
│  ┌──────────────────────────────────────┐  (y: 600px)     │
│  │         EXTERNAL APIs                 │  Height: 80px   │
│  └──────────────────────────────────────┘                  │
│                                                            │
│  [Legend]                                   (y: 700px)     │
└────────────────────────────────────────────────────────────┘
```

## Final Checklist

- [ ] All 6 layers are visible
- [ ] Colors match the scheme above
- [ ] Arrows connect components correctly
- [ ] Title is at the top
- [ ] Legend explains the colors
- [ ] Exported as high-quality PNG
- [ ] Added to README.md

---

Good luck! Your diagram will look professional if you follow these steps.
