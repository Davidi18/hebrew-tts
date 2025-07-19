# 🎤 Hebrew TTS Service

> **Professional Hebrew Text-to-Speech service using Facebook's MMS-TTS model**

A robust REST API service that converts Hebrew text to high-quality MP3 audio files using Facebook's Massively Multilingual Speech (MMS) TTS model.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Hebrew](https://img.shields.io/badge/Language-Hebrew-orange)

## ✨ Features

- 🎯 **High-Quality Hebrew TTS** - Using Facebook's MMS-TTS Hebrew model
- ⚡ **Smart Caching** - Identical texts return instantly from cache
- 🐳 **Docker Ready** - Easy deployment with Coolify/Docker
- 📊 **Health Monitoring** - Built-in health checks and statistics
- 🔄 **REST API** - Simple HTTP interface for easy integration
- 📱 **Mobile Friendly** - Works with WhatsApp, Telegram, and mobile apps

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone <your-repo-url>
cd hebrew-tts-service

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
