# Automation Web

Automation Web is an on-growing app aims to help maily the field deprecation process for Tableau CRM Dataflows at Salesforce orgs. But it also offers some interesting additional features focused on the daily journal of a BT Tableau CRM specialyst.

## Features

- Removes Salesforce Object/Field references from Tableau CRM Wave dataflows - Field Deprecation.
- Stores the deprecation operation safely into database for any post verification.
- Connects, downloads and uploads Wave dataflows from and to Salesforce org, respectively.
- Works with Wave dataflow:
-- Extracts partial section of a wave dataflow, given a node api name.
-- Replaces or updates nodes of a wave dataflow based on one or more .json files.
- Works with Tableau CRM Wave Dataset Security predicates:
-- Fixes automatically security predicate syntax (experimental).
-- Generates SAQL sentence from security predicate.
- Formats and sends Slack messages.

## Tech

Automation web is developed leveraging on the following tech stack:

- [Django](https://www.djangoproject.com/) - Python-based web app framework.
- [Bootstrap](https://getbootstrap.com/docs/4.6/getting-started/introduction/) - Bootstrap 4.6
- [Docker](https://www.docker.com) - Containerization utility.
- [Heroku](https://www.heroku.com) - Fast CD/CI and Deploy platform for web apps.

And of course it's open sourced with a [public repository](https://github.com/Bluewine/automation-web.git)
 on GitHub.

## Installation

### Local Installation

Use docker:

- Install docker from [here](https://docs.docker.com/desktop/mac/install/).
-- For Windows users, they have to first activate and install/upgrade the WSL. Refer to [this doc](https://docs.microsoft.com/en-us/windows/wsl/install-win10).
-- Then, install Docker.
- Clone this repository.
- Go into the cloned folder and type: `docker-compose up --build`

### World-wide web accessible:

Open browser and type: [https://automation-web.herokuapp.com](https://automation-web.herokuapp.com/)

## License

Free if no better than that :)
