![image](https://i.imgur.com/NhuaxOM.png)
# Quark
## A fast indexer for all EVM chains

> This repo is at an experimental stage. Use it at your own risk.

### Idea
It's not that the current indexing solutions like theGraph protocol aren't good, they weren't ideal for our use case so we decided to build our indexing solution. We at Nurturelabs have been building dapps for a year and indexing was one thing that was always required. A lot of solutions in the market focus on subscriptions to events via webhooks but that is not ideal. It leaves the task to process and organize the event logs on a separate system which may go down and miss an event corrupting the data integrity.

TheGraph got all these things right but we needed something
- where we could programmatically create new indexes
- reindex them much more quickly whenever changes were made to the callbacks or the models 
- ensure its uptime ourselves instead of relying on their hosted service
- make manifests that scanned multiple contracts across multiple chains at the same time
- allowed more complex callbacks to be written

Also, we wanted something in Python so that we can comfortably edit it as our needs evolve.

#### Index
In quark an Index is equivalent to a subgraph in theGraph.

A single index definition contains the contracts to scan across all EVM chains, their callbacks for each event, the models(DB tables) those callbacks will save to. 

### What can it do?
- Index any EVM chain, even the `bsc-tesnet` chain and `nervos` chain not covered in the graph hosted service.
- Can be integrated into your Python/Django backend -- something specific for us
- A large number of blocks can be scanned in one go - Scans blocks at the max blocks per scan limit for each chain and adjusts the scan size accordingly if the call fails 
- Callbacks can be defined for each event so that processed tables can be kept up to date
- Data integrity is maintained and we ensure callbacks aren't executed again for the same event log
- Generic read and write for all EVM chains
- Simple reindexing controls and management of multiple indexes

### Things to do
- [ ] Make a generic python package on pypi
- [ ] Add support for other ORMs
- [ ] Make a hosted version with a GraphQL interface
- [ ] Add parallelization to the event fetching to increase indexing speed
- [ ] Build documentation 

### Running on local
```bash
mkdir app/staticfiles
docker-compose -f local.yml up --build
```
