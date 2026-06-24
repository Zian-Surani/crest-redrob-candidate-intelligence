# CREST Database Strategy

## Decision

The competition ranker does not need a database. It must remain able to stream the official JSONL, load local precomputed artifacts, and produce the CSV with no network dependency.

The SaaS product does need persistence for accounts, organizations, JDs, ranking history, audit logs, and usage analytics. SQLite already provides that locally and is the lowest-risk hackathon choice.

## When MongoDB is justified

Use MongoDB for a hosted multi-tenant version when candidate documents are continuously ingested and their nested profile/career/skill/signal structure changes frequently. Do not make MongoDB a required dependency for the competition reproduction command.

MongoDB uses collections and indexes rather than SQL tables.

## Recommended collections

- `organizations`: tenant identity, plan, settings, and retention policy
- `users`: organization membership and role; authentication secrets should remain hashed or delegated to an identity provider
- `jobs`: raw JD, parsed requirements, salary band, location, owner, and status
- `candidates`: the nested released schema plus organization/source metadata
- `ranking_runs`: job, algorithm version, weights, runtime, counts, integrity breakdown, and artifact checksum
- `ranking_results`: run ID, candidate ID, rank, score components, CPH, reasoning, and evidence
- `analytics_events`: past-tense events such as `job_created`, `ranking_completed`, and `ranking_exported`
- `audit_logs`: actor, action, target, timestamp, and redacted change details

## Required indexes

- `organizations.slug`: unique
- `users.{organization_id,email}`: unique compound
- `jobs.{organization_id,status,created_at}`
- `candidates.candidate_id`: unique for the released pool
- `candidates.{profile.country,profile.location,profile.years_of_experience}`
- `candidates.skills.name`: multikey
- `ranking_runs.{organization_id,job_id,created_at}`
- `ranking_results.{run_id,rank}`: unique compound
- `ranking_results.{run_id,candidate_id}`: unique compound
- `analytics_events.{organization_id,event_name,created_at}`
- `audit_logs.{organization_id,created_at}`

## Migration boundary

Keep a repository interface so local SQLite and hosted MongoDB implementations can coexist. Import candidate JSONL with bulk writes in bounded batches, create indexes after the initial load, and store a dataset checksum and algorithm version with every run. Never place MongoDB Atlas or another network service in the offline competition ranking path.

## Current environment

The current machine has no `mongod` or `mongosh` executable and no `MONGODB_URI` environment variable. Creating and populating collections therefore requires either a local MongoDB installation or a user-approved Atlas connection string.
