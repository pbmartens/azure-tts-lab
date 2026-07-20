# Azure Text-to-Speech Lab

Console app that converts text to natural-sounding speech using the Azure AI Speech SDK for Python.

## Setup

1. Create an Azure AI Speech resource in the Azure Portal and note its **key** and **region**.
2. Fill in `.env` with your values:
   ```
   SPEECH_KEY=<your key>
   SPEECH_REGION=<your region>
   ```
3. Activate the virtual environment and install dependencies:
   ```
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Run the app:
   ```
   python text_to_speech.py
   ```
