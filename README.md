# CheatSheet

## 1. Introduction + Possible names

Working examples:

- Thesa
- Kihon
- Grok
- Shelf
- CheatSnap
- Cheatsheet
- QuickCheat

Web-application written on python. A tool for development learning. Create, share, store, manage and subscribe to your favourite authors.
Main audience: curious users, students that want to improve there productivity and optimize workflow.

## 2. Requirements

### Guests

- Guest may register and authenticate.
- Guests can view all cheatsheets and author profiles but nothing else.

### Users

- Users must be registered and authenticated.
- Users may be banned for inapropriate content temporarily or permanently.
- Users may subscribe to the authors and add cheatsheets to favourites.
- Users have profile (profile description, refs to social media, profile image).
- Users will get notifications about new cheatsheets from authors they follow.
- Users may download cheatsheets

### Authors

- Authors may create, delete (24 hours to recover), edit there cheatsheets.
- Authors may have and view followers.
- Authors have different grades (achievements for first public cheatsheet, for first 5 likes, 20 likes, ...)

### Cheatsheets

- Cheatsheets have likes and views (stats).
- Cheatsheets may have from one to six tags.
- Cheatsheets may be private or public.

## 3. Technical requirements

- Programming languages: **JavaScript** (React), **Python** (FastAPI).
- API: RESTfull.
- Database: PostgreSQL, Redis.
- Cache: Redis.
- Authentication: -
- Deploy: Nginx, Docker.
- Code coverage: >= 75 %
- Metrics: Prometheus, Grafana
- RPS: 1000
- Response time SLI: 100 ms
- Response success SLI: 99,99 %
