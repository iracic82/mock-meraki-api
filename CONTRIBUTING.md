# Contributing

Thank you for your interest in contributing to Mock Meraki API!

## Quick Links

- **[Topology Guide](docs/TOPOLOGY_GUIDE.md)** - Full guide for creating and contributing topologies
- **[Self-Hosting](docs/TOPOLOGY_GUIDE.md#self-hosting-guide)** - Deploy your own instance

## TL;DR

1. Fork the repo
2. Create topology in `seed_data/topologies/your_topology.py`
3. Test locally: `python scripts/validate_topologies.py`
4. Open Pull Request
5. CI validates automatically
6. Maintainer reviews and merges

## Branch Protection

- All PRs require passing CI (`validate` + `lint`)
- All PRs require 1 maintainer approval
- Only `hub_spoke.py` changes auto-deploy to production

## Questions?

Open an issue or contact Igor Racic.
