#!/usr/bin/env python3
"""
Validate all topology files in seed_data/topologies/

This script is used by CI to ensure all topologies:
1. Can be imported without errors
2. Generate valid data structures
3. Follow Meraki API field requirements
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_topology(name: str, module_path: str, func_name: str) -> list[str]:
    """Validate a single topology and return list of errors."""
    errors = []

    print(f'\n=== Validating {name} topology ===')

    try:
        module = __import__(module_path, fromlist=[func_name])
        generate_func = getattr(module, func_name)

        # Generate topology with fixed seed for reproducibility
        data = generate_func(seed=42)

        # Validate required top-level fields
        required = ['topology_name', 'organizations', 'networks', 'devices', 'vlans']
        for field in required:
            if field not in data:
                errors.append(f'{name}: Missing required field "{field}"')
            elif not data[field]:
                errors.append(f'{name}: Field "{field}" is empty')

        # Print stats
        stats = data.get('stats', {})
        print(f'  Organizations: {stats.get("organizations", len(data.get("organizations", [])))}')
        print(f'  Networks: {stats.get("networks", len(data.get("networks", [])))}')
        print(f'  Devices: {stats.get("devices", len(data.get("devices", [])))}')
        print(f'  VLANs: {stats.get("vlans", len(data.get("vlans", [])))}')
        print(f'  Clients: {stats.get("clients", len(data.get("network_clients", [])))}')

        # Validate Organization fields
        if data.get('organizations'):
            org = data['organizations'][0]
            org_required = ['id', 'name', 'url', 'api', 'cloud']
            for field in org_required:
                if field not in org:
                    errors.append(f'{name}: Organization missing field "{field}"')

        # Validate Network fields (Meraki API compliance)
        if data.get('networks'):
            net = data['networks'][0]
            net_required = ['id', 'organizationId', 'name', 'productTypes', 'timeZone',
                          'tags', 'url', 'isBoundToConfigTemplate']
            for field in net_required:
                if field not in net:
                    errors.append(f'{name}: Network missing field "{field}"')

        # Validate Device fields
        if data.get('devices'):
            dev = data['devices'][0]
            dev_required = ['serial', 'name', 'model', 'networkId', 'mac', 'productType',
                          'firmware', 'lanIp', 'tags', 'lat', 'lng']
            for field in dev_required:
                if field not in dev:
                    errors.append(f'{name}: Device missing field "{field}"')

        # Validate VLAN fields
        if data.get('vlans'):
            vlan = data['vlans'][0]
            vlan_required = ['id', 'networkId', 'name', 'subnet', 'applianceIp']
            for field in vlan_required:
                if field not in vlan:
                    errors.append(f'{name}: VLAN missing field "{field}"')

        # Validate Client fields
        if data.get('network_clients'):
            client = data['network_clients'][0]
            client_required = ['id', 'mac', 'ip', 'description', 'manufacturer',
                             'deviceTypePrediction', 'status']
            for field in client_required:
                if field not in client:
                    errors.append(f'{name}: Client missing field "{field}"')

            # Check deviceTypePrediction format (should contain comma for Meraki format)
            # Exception: Some embedded devices don't have OS info after the comma
            dtp = client.get('deviceTypePrediction', '')
            valid_no_comma_types = [
                'Cisco IP Phone', 'Cisco IP Phone 8845',
                'HP LaserJet Printer', 'HP OfficeJet MFP',
                'Canon Printer', 'Epson Printer',
                'IoT Sensor', 'Environmental Sensor',
                'Axis IP Camera', 'Axis P3245-V',
                'Zebra Scanner', 'Zebra TC52',
                'Honeywell Scanner', 'Honeywell CT60',
                'GE Patient Monitor', 'GE CARESCAPE Monitor',
                'Philips IntelliVue', 'Philips Patient Monitor',
            ]
            if dtp and ',' not in dtp and dtp not in valid_no_comma_types:
                print(f'  Warning: deviceTypePrediction "{dtp}" may not be in Meraki format')

        if not errors:
            print(f'  ✓ Topology "{name}" is valid')

    except Exception as e:
        errors.append(f'{name}: {str(e)}')
        print(f'  ✗ Error: {e}')

    return errors


def discover_topologies() -> list[tuple[str, str, str]]:
    """Discover all topology files in seed_data/topologies/"""
    topologies = []
    topology_dir = Path('seed_data/topologies')

    for py_file in topology_dir.glob('*.py'):
        if py_file.name.startswith('_'):
            continue

        module_name = py_file.stem
        module_path = f'seed_data.topologies.{module_name}'
        func_name = f'generate_{module_name}_topology'

        topologies.append((module_name, module_path, func_name))

    return topologies


def main():
    """Main validation entry point."""
    print("=" * 60)
    print("TOPOLOGY VALIDATION")
    print("=" * 60)

    topologies = discover_topologies()
    print(f"\nDiscovered {len(topologies)} topology files")

    all_errors = []

    for name, module_path, func_name in topologies:
        errors = validate_topology(name, module_path, func_name)
        all_errors.extend(errors)

    print("\n" + "=" * 60)

    if all_errors:
        print("VALIDATION FAILED")
        print("=" * 60)
        for err in all_errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print("ALL TOPOLOGIES VALID")
        print("=" * 60)
        sys.exit(0)


if __name__ == '__main__':
    main()
