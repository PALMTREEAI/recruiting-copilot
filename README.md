# Recruiting Co-Pilot

An AI-powered recruiting assistant that helps you manage your pipeline, track candidates, and make data-driven decisions about sourcing priorities.

## Features

- 📊 **Daily Email Digest** — Automated morning brief at 6am with pipeline health, priorities, and stuck candidates
- 💬 **Web Chat Interface** — Ask questions about your pipeline anytime
- 📈 **Pipeline Analytics** — Conversion rates, gap-to-hire calculations, and sourcing allocation
- ⚠️ **Stuck Candidate Detection** — Automatic flagging of candidates who need attention

## Tech Stack

- **Backend**: Python (FastAPI)
- **Frontend**: HTML/CSS/JavaScript
- **APIs**: Ashby, Claude, Resend
- **Deployment**: Render.com

## Getting Started

### Prerequisites

- Python 3.9+
- API keys for:
  - Ashby (pipeline management)
  - Claude (AI responses)
  - Resend (email delivery)

### Installation

1. Clone the repository
2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your API keys
   ```

5. Run the backend:
   ```bash
   python backend/main.py
   ```

6. Open the frontend:
   - Open `frontend/index.html` in your browser
   - Or serve it with a simple HTTP server

## Project Structure

```
recruiting-copilot/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt         # Python dependencies
│   ├── services/               # Business logic
│   │   ├── ashby_service.py    # Ashby API integration
│   │   ├── analysis_service.py # Pipeline analysis
│   │   ├── email_service.py    # Email digest generation
│   │   └── chat_service.py     # Chat responses
│   └── utils/                  # Helper functions
├── frontend/
│   ├── index.html              # Chat interface
│   ├── styles.css              # Styling
│   └── script.js               # Client-side logic
└── SPEC.md                     # Full project specification
```

## Configuration

Environment variables in `.env`:
- `ASHBY_API_KEY` — Your Ashby API key
- `RESEND_API_KEY` — Your Resend API key
- `ANTHROPIC_API_KEY` — Your Claude API key
- `EMAIL_TO` — Email address for daily digest

## Development

### Running locally

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

### Testing

Each service has example output you can verify before deployment.

## Deployment

Deploy to Render.com following the guide in `SPEC.md` Part 5.

## License

Private project
