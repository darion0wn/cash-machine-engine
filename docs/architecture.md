# Cash Machine Engine - Architecture

Version: 1.0
Status: Draft

---

# Vision

Cash Machine Engine is an Opportunity Intelligence Platform.

Its goal is to continuously discover business opportunities from the Internet, analyze them using AI and build a searchable knowledge base of startup ideas, problems and market opportunities.

The project must be modular, scalable and provider-agnostic.

---

# High Level Architecture

                Crawlers
                   │
                   ▼
            Opportunity
                   │
                   ▼
      OpportunityRepository
                   │
                   ▼
               Database
                   │
                   ▼
              AI Analyzer
                   │
                   ▼
               Analysis
                   │
                   ▼
       AnalysisRepository

---

# Project Structure

cash-machine-engine/

ai/
    AI providers (Gemini, OpenAI...)

crawler/
    Data sources

database/
    SQLite connection
    Database schema
    Repositories

docs/
    Documentation

models/
    Domain entities

pipeline/
    Workflow orchestration

services/
    Business logic

tests/
    Unit tests

dashboard/
    Future web interface

---

# Responsibilities

## Crawlers

Responsible for:

- collecting data
- parsing external sources

Must NOT:

- access database directly
- call AI directly

Output:

Opportunity

---

## Opportunity

Represents raw information collected from the Internet.

Contains:

- source
- title
- url
- article

Does NOT contain AI analysis.

---

## OpportunityRepository

Responsible only for persistence of Opportunity.

Must contain SQL queries.

Must not contain business logic.

---

## Analyzer

Responsible only for AI analysis.

Input:

Opportunity

Output:

Analysis

Must not access the database.

---

## Analysis

Represents the AI interpretation of an Opportunity.

Contains:

- problem
- customer
- pain level
- market size
- opportunity score
- model
- prompt version

---

## AnalysisRepository

Responsible only for persistence of Analysis.

---

## Engine

The Engine orchestrates the entire workflow.

Responsibilities:

1. receive an Opportunity
2. save Opportunity
3. execute AI analysis
4. save Analysis

The Engine contains NO SQL.

The Engine contains NO prompt.

The Engine contains NO crawling logic.

---

# Dependency Rules

Allowed

Crawler
    ↓
Engine

Engine
    ↓
Repositories

Engine
    ↓
Analyzer

Analyzer
    ↓
AI Provider

Repositories
    ↓
Database

Forbidden

Crawler → Database

Crawler → Gemini

Repository → AI

Analyzer → SQLite

Model → Database

---

# Database

Tables

Opportunity

- id
- source
- title
- url
- article
- created_at

Analysis

- id
- opportunity_id
- model
- prompt_version
- problem
- customer
- pain_level
- market_size
- opportunity_score
- created_at

One Opportunity can have multiple Analyses.

---

# Design Principles

Single Responsibility Principle

Each class has exactly one responsibility.

Dependency Direction

High-level modules do not depend on low-level implementation.

Composition over inheritance.

Business logic never lives inside repositories.

---

# Future Roadmap

Phase 1

- SQLite
- Gemini
- Hacker News

Phase 2

- Reddit
- GitHub
- Better scoring

Phase 3

- FastAPI

Phase 4

- Dashboard

Phase 5

- PostgreSQL

Phase 6

- Authentication

Phase 7

- Opportunity search

Phase 8

- Analytics

---

# Coding Standards

One class per file.

One responsibility per class.

Explicit names.

No duplicated logic.

Repositories only contain persistence.

Services contain business logic.

Models contain data.

Engine orchestrates.