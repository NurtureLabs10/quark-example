# Quark
## A fast indexer for all EVM chains

> This repo is at an experimental stage. Use it at your own risk.

### Idea
It's not that that the current indexing solutions like theGraph protocol arent good, they weren't ideal for our use case so we decided to build our own indexing solution. We at Nurturelabs have been building dapps since a year and indexing was one thing which was always required. A lot of solutions in the market focus on subscription to events/webhooks but that is not ideal. It leaves the task to process and organise on separate system which may down and miss an event corrupting the data integrity. TheGraph got all these things right but we need something where could programatically create new indexes, ensure its uptime ourselves instead on relying on their hosted service, make manifests which scaned multiple contracts across multiple chains at the same time and allowed more complex callbacks to be written. Also we wanted something in Python so that we can comfortably edit it as our needs evolve.

### What can it do?
- A single index definition contains the contracts to scan across all EVM chains, their callbacks for each event, the models those callbacks will save too  
- Index any EVM chain, even the `bsc-tesnet` chain and `nervos` chain not covered in the graph hosted service.
- Can be integrated into your Python/Django backend -- something specific for us
- Large number of blocks can be scanned in one go - Scans blocks at the max blocks per scan limit for each chain and adjusts the scan size accordingly if the call fails 
- Callbacks can be defined for each event so that processesed tables can be kept upto date
- Data integrity is maintained and we ensure callbacks arent executed again for the same event log
- Generic read and write for all EVM chains
- Simple reindexing controls and management of multiple indexes

### Things to do
- [ ] Make a generic python package on pypi
- [ ] Add support for other ORMs
- [ ] Make a hosted version with an GraphQL interface
- [ ] Add parallisation to the event fetching to increase indexing speed
- [ ] Build documentation 

### Running on local
```bash
mkdir app/staticfiles
docker-compose -f local.yml up --build
```
