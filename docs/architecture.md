# Architecture

## System Overview

User → Telegram → Bot Handler → LLM Interface → Provider → Response

## Components

### Bot Layer
Handles Telegram updates and message routing.

### LLM Interface
Provider-agnostic abstraction layer.

### Providers
- OpenAI
- LangChain
- GigaChat

## Design Goals

- modularity
- provider independence
- scalability
- extensibility