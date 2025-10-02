"""
Generate sample Azure Advisor CSV data for testing.

Creates three files:
- sample_small.csv (50 recommendations)
- sample_medium.csv (500 recommendations)
- sample_large.csv (2000 recommendations)
"""

import csv
import random
from pathlib import Path

# Sample data generators
categories = {
    'Cost': 0.35,
    'Security': 0.25,
    'Reliability': 0.20,
    'Operational Excellence': 0.12,
    'Performance': 0.08
}

impacts = ['High', 'Medium', 'Low']
currencies = ['USD']

resource_types = [
    'Microsoft.Compute/virtualMachines',
    'Microsoft.Storage/storageAccounts',
    'Microsoft.Network/loadBalancers',
    'Microsoft.Network/applicationGateways',
    'Microsoft.Network/publicIPAddresses',
    'Microsoft.Sql/servers/databases',
    'Microsoft.Web/sites',
    'Microsoft.Cache/Redis',
    'Microsoft.KeyVault/vaults',
    'Microsoft.Network/virtualNetworks'
]

subscriptions = [
    ('12345678-1234-1234-1234-123456789012', 'Production Subscription'),
    ('87654321-4321-4321-4321-210987654321', 'Development Subscription'),
    ('11111111-2222-3333-4444-555555555555', 'Testing Subscription'),
    ('99999999-8888-7777-6666-444444444444', 'Staging Subscription')
]

resource_groups = [
    'rg-production-web', 'rg-production-data', 'rg-production-network',
    'rg-dev-compute', 'rg-dev-storage', 'rg-dev-network',
    'rg-test-app', 'rg-staging-services'
]

recommendation_templates = {
    'Cost': [
        'Consider using Azure Reserved VM Instances to save money on virtual machines',
        'Right-size underutilized virtual machines to reduce costs',
        'Delete unused {resource} to reduce costs',
        'Optimize storage tier for blob storage to reduce storage costs',
        'Consolidate small databases into elastic pool for better cost efficiency',
        'Remove unattached managed disks to eliminate unnecessary charges',
        'Delete unused public IP addresses to save money',
        'Use Azure Hybrid Benefit for Windows Server to reduce licensing costs'
    ],
    'Security': [
        'Enable Azure Defender for your {resource} to protect against threats',
        'Rotate storage account keys regularly to enhance security',
        'Enable multi-factor authentication for privileged accounts',
        'Update TLS configuration to use modern protocols only',
        'Implement network security groups for traffic filtering',
        'Enable encryption at rest for sensitive data',
        'Configure private endpoints for secure access',
        'Enable Azure AD integration for enhanced authentication'
    ],
    'Reliability': [
        'Configure availability zones for your virtual machines',
        'Implement backup strategy for production databases and resources',
        'Configure health probes for load balancer endpoints',
        'Enable geo-replication for critical storage accounts',
        'Implement resource locks to prevent accidental deletion',
        'Configure auto-failover for databases',
        'Enable zone redundancy for high availability',
        'Implement circuit breaker pattern for resilient services'
    ],
    'Performance': [
        'Upgrade to Premium SSD for improved IOPS performance',
        'Enable caching for frequently accessed content',
        'Enable acceleration for your application gateway',
        'Optimize database query performance with indexing',
        'Configure auto-scaling for web applications',
        'Enable CDN for static content delivery',
        'Optimize network latency with proximity placement groups',
        'Use read replicas for read-heavy database workloads'
    ],
    'Operational Excellence': [
        'Enable diagnostic logs for your {resource} to improve troubleshooting',
        'Tag resources for better cost allocation and management',
        'Implement monitoring and alerting for critical resources',
        'Configure resource naming standards for consistency',
        'Enable Azure Policy for governance and compliance',
        'Implement Infrastructure as Code for consistent deployments',
        'Configure automated patching for virtual machines',
        'Enable Azure Automation for routine tasks'
    ]
}


def get_savings(category, impact):
    """Calculate realistic savings based on category and impact."""
    if category != 'Cost':
        return 0
    if impact == 'High':
        return round(random.uniform(500, 5000), 2)
    elif impact == 'Medium':
        return round(random.uniform(100, 1500), 2)
    else:
        return round(random.uniform(0, 500), 2)


def get_advisor_impact(category):
    """Get advisor score impact based on category."""
    base = {
        'Cost': 4.5,
        'Security': 8.0,
        'Reliability': 7.3,
        'Performance': 5.7,
        'Operational Excellence': 5.1
    }
    return round(base.get(category, 5.0) + random.uniform(-1.5, 1.5), 2)


def generate_recommendation(category, impact):
    """Generate a recommendation text."""
    template = random.choice(recommendation_templates[category])
    resource_options = ['storage accounts', 'virtual machines', 'databases',
                       'resources', 'network resources']
    return template.replace('{resource}', random.choice(resource_options))


def generate_csv(filepath, num_recommendations):
    """Generate a CSV file with the specified number of recommendations."""
    print(f'Generating {filepath.name} with {num_recommendations} recommendations...')

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow([
            'Category', 'Business Impact', 'Recommendation',
            'Subscription ID', 'Subscription Name', 'Resource Group',
            'Resource Name', 'Resource Type', 'Potential Annual Cost Savings',
            'Currency', 'Potential Benefits', 'Advisor Score Impact',
            'Retirement Date', 'Retiring Feature'
        ])

        # Write data rows
        for i in range(num_recommendations):
            category = random.choices(
                list(categories.keys()),
                weights=list(categories.values())
            )[0]
            impact = random.choices(impacts, weights=[0.2, 0.5, 0.3])[0]
            sub_id, sub_name = random.choice(subscriptions)
            rg = random.choice(resource_groups)
            rt = random.choice(resource_types)

            # Generate resource name based on resource group
            rg_suffix = rg.split('-')[-1]
            resource_num = random.randint(1, 999)
            resource_name = f'{rg_suffix}-{rt.split("/")[-1].lower()}-{resource_num:03d}'

            writer.writerow([
                category,
                impact,
                generate_recommendation(category, impact),
                sub_id,
                sub_name,
                rg,
                resource_name,
                rt,
                get_savings(category, impact),
                'USD',
                f'Improve {category.lower()} posture and best practices alignment',
                get_advisor_impact(category),
                '',  # Retirement Date
                ''   # Retiring Feature
            ])

    print(f'Generated {filepath.name} successfully!')


def main():
    """Generate all sample data files."""
    base_path = Path('D:/Code/Azure Reports/azure_advisor_reports/tests/sample_data')
    base_path.mkdir(parents=True, exist_ok=True)

    # Generate three sample files
    generate_csv(base_path / 'sample_small.csv', 50)
    generate_csv(base_path / 'sample_medium.csv', 500)
    generate_csv(base_path / 'sample_large.csv', 2000)

    print('\n✅ All sample data files created successfully!')
    print(f'   Location: {base_path}')


if __name__ == '__main__':
    main()
