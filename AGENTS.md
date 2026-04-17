# Project: Adobe Sign Signature Dashboard

## Project Overview
Status: WIP - Work in Progress
Weekly signature status dashboard. Tracks ~1,500 documents/month via
Adobe Sign API. Exports to dashboard.csv. Stack: Python 3.11+, SQLAlchemy, SQLite, REST API calls.

## Development modules
located in `tests`
ignore code in `src`, `tests/old_modules`, `tests/zscrappping_code`

## Agent Guidelines
use `.opencode/agents/python_coder.md`

## Project TODO List
* Generate an implementation plan for the following tasks:
* fetch all users from Adobe Sign API
* insert only new users in DB Users table. 
    * Use email for comparison of new users vs exisitng users 
    * To improve performance, first obtain the existing email list for all users in the Users table
    * insert to DB only users that are not in the existing email list. insert email and adbe_sing_id ('email' and 'id' in the adobe user api response)

## Agent task:
Analyze this codebase to create a comprehensive AGENTS.md file. Scan the project structure, configuration files (e.g., package.json, tsconfig.json, docker-compose.yml), and existing documentation.
Generate the file with these sections:
Project Overview: A one-sentence summary of the project's purpose and tech stack.
Project Structure: Map key directories and their responsibilities.
Critical Commands: List exact commands for build, lint, test, and typecheck.
Coding Conventions: Identify naming patterns (e.g., camelCase vs PascalCase), preferred libraries, and architectural rules (e.g., use interfaces over types). Use `.opencode/agents/python_coder.md` agent guidelines
Operational Boundaries: Define what files or services I should NOT modify.
Focus only on information that is not obvious from filenames alone. Prioritize brevity for machine parsing