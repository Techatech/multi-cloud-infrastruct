import re
from typing import Dict, List, Tuple, Optional

class ASCIIDiagramGenerator:
    """Generates multi-cloud ASCII architecture diagrams with emojis."""

    def __init__(self):
        # Unicode box drawing characters (simplified for reliability)
        self.chars = {
            'horizontal': '─',
            'vertical': '│',
            'arrow_down': '↓',
            'arrow_right': '→'
        }

        # Universal service concepts mapped to emojis
        self.service_icons = {
            'user': '👥', 'internet': '🌐', 'dns': '🌍', 'cdn': '🚀', 
            'load_balancer': '⚖️', 'api_gateway': '🔌', 'compute': '🖥️', 
            'serverless': '⚡', 'database_sql': '🗄️', 'database_nosql': '📊', 
            'cache': '💨', 'storage_object': '📦', 'storage_block': '💾', 
            'queue': '📬', 'notification': '📢', 'vpc': '🏠', 'security': '🔒', 
            'iam': '🔐', 'monitoring': '📈', 'container_registry': '🚢',
            'ci_cd': '⚙️', 'data_warehouse': '🏦', 'analytics': '💡',
            'auth': '🔑'
            # Add more universal concepts as needed
        }

        # Platform-specific service names, patterns, and their universal concept
        self.platform_services = {
            'aws': {
                'user': {'pattern': r'\busers?\b|\bclients?\b|\bcustomers?\b', 'name': 'Users'},
                'internet': {'pattern': r'\binternet\b|\bweb\b|\bpublic\b', 'name': 'Internet'},
                'dns': {'pattern': r'\broute\s?53\b|\bdns\b|\bdomain\b', 'name': 'Route 53'},
                'cdn': {'pattern': r'\bcloudfront\b|\bcdn\b|\bcontent delivery\b', 'name': 'CloudFront'},
                'load_balancer': {'pattern': r'\bload\s?balancer\b|\belb\b|\balb\b|\bnlb\b', 'name': 'ELB/ALB'},
                'api_gateway': {'pattern': r'\bapi\s?gateway\b|\bapi\b', 'name': 'API Gateway'},
                'compute': {'pattern': r'\bec2\b|\bserver\b|\binstance\b|\bcompute\b', 'name': 'EC2 Instance'},
                'serverless': {'pattern': r'\blambda\b|\bfunction\b', 'name': 'Lambda'},
                'database_sql': {'pattern': r'\brds\b|\bdatabase\b|\bmysql\b|\bpostgres\b|\baurora\b', 'name': 'RDS'},
                'database_nosql': {'pattern': r'\bdynamodb\b|\bnosql\b', 'name': 'DynamoDB'},
                'cache': {'pattern': r'\belasticache\b|\bcache\b|\bredis\b|\bmemcached\b', 'name': 'ElastiCache'},
                'storage_object': {'pattern': r'\bs3\b|\bbucket\b|\bobject storage\b', 'name': 'S3 Bucket'},
                'storage_block': {'pattern': r'\bebs\b|\bblock storage\b', 'name': 'EBS Volume'},
                'queue': {'pattern': r'\bsqs\b|\bqueue\b', 'name': 'SQS'},
                'notification': {'pattern': r'\bsns\b|\bnotification\b|\btopic\b', 'name': 'SNS'},
                'vpc': {'pattern': r'\bvpc\b|\bnetwork\b', 'name': 'VPC'},
                'security': {'pattern': r'\bsecurity group\b|\bwaf\b|\bshield\b', 'name': 'Security'},
                'iam': {'pattern': r'\biam\b|\bidentity\b|\brole\b|\buser\b', 'name': 'IAM'},
                'monitoring': {'pattern': r'\bcloudwatch\b|\bmonitor\b|\blog\b|\bmetric\b', 'name': 'CloudWatch'},
                'container_registry': {'pattern': r'\becr\b|\bcontainer registry\b', 'name': 'ECR'},
                'ci_cd': {'pattern': r'\bcodebuild\b|\bcodepipeline\b|\bcodecommit\b|\bcodedeploy\b|\bci/cd\b', 'name': 'CI/CD'},
                'auth': {'pattern': r'\bcognito\b|\bauthentication\b|\bauth\b', 'name': 'Cognito'},
            },
            'gcp': {
                'user': {'pattern': r'\busers?\b|\bclients?\b|\bcustomers?\b', 'name': 'Users'},
                'internet': {'pattern': r'\binternet\b|\bweb\b|\bpublic\b', 'name': 'Internet'},
                'dns': {'pattern': r'\bcloud dns\b|\bdns\b', 'name': 'Cloud DNS'},
                'cdn': {'pattern': r'\bcloud cdn\b|\bcdn\b', 'name': 'Cloud CDN'},
                'load_balancer': {'pattern': r'\bcloud load balancing\b|\bload balancer\b', 'name': 'Load Balancer'},
                'api_gateway': {'pattern': r'\bapi gateway\b|\bapigee\b', 'name': 'API Gateway'},
                'compute': {'pattern': r'\bcompute engine\b|\bvm\b|\binstance\b|\bgce\b', 'name': 'Compute Engine'},
                'serverless': {'pattern': r'\bcloud functions\b|\bcloud run\b|\bfunctions\b', 'name': 'Cloud Functions/Run'},
                'database_sql': {'pattern': r'\bcloud sql\b|\bspanner\b|\bdatabase\b|\bmysql\b|\bpostgres\b', 'name': 'Cloud SQL/Spanner'},
                'database_nosql': {'pattern': r'\bfirestore\b|\bdatastore\b|\bbigtable\b|\bnosql\b', 'name': 'Firestore/Bigtable'},
                'cache': {'pattern': r'\bmemorystore\b|\bcache\b|\bredis\b|\bmemcached\b', 'name': 'Memorystore'},
                'storage_object': {'pattern': r'\bcloud storage\b|\bbucket\b|\bgcs\b', 'name': 'Cloud Storage'},
                'storage_block': {'pattern': r'\bpersistent disk\b|\bdisk\b', 'name': 'Persistent Disk'},
                'queue': {'pattern': r'\bpub/sub\b|\bqueue\b|\btopic\b', 'name': 'Pub/Sub'},
                'notification': {'pattern': r'\bpub/sub\b|\bnotification\b', 'name': 'Pub/Sub'}, # Often same service
                'vpc': {'pattern': r'\bvpc network\b|\bnetwork\b', 'name': 'VPC Network'},
                'security': {'pattern': r'\bfirewall rule\b|\bcloud armor\b|\bsecurity\b', 'name': 'Firewall/Armor'},
                'iam': {'pattern': r'\biam\b|\bidentity\b|\bservice account\b', 'name': 'IAM'},
                'monitoring': {'pattern': r'\bcloud monitoring\b|\bcloud logging\b|\boperations\b', 'name': 'Cloud Monitoring'},
                'container_registry': {'pattern': r'\bartifact registry\b|\bcontainer registry\b', 'name': 'Artifact Registry'},
                'ci_cd': {'pattern': r'\bcloud build\b|\bcloud deploy\b|\bcloud source repositories\b', 'name': 'Cloud Build'},
                'data_warehouse': {'pattern': r'\bbigquery\b|\bdata warehouse\b', 'name': 'BigQuery'},
                'analytics': {'pattern': r'\bdataflow\b|\bdataproc\b|\banalytics\b', 'name': 'Dataflow/Dataproc'},
                'auth': {'pattern': r'\bidentity platform\b|\bfirebase auth\b|\bauthentication\b', 'name': 'Identity Platform'},
            },
            'azure': {
                'user': {'pattern': r'\busers?\b|\bclients?\b|\bcustomers?\b', 'name': 'Users'},
                'internet': {'pattern': r'\binternet\b|\bweb\b|\bpublic\b', 'name': 'Internet'},
                'dns': {'pattern': r'\bazure dns\b|\bdns\b', 'name': 'Azure DNS'},
                'cdn': {'pattern': r'\bazure cdn\b|\bcdn\b', 'name': 'Azure CDN'},
                'load_balancer': {'pattern': r'\bload balancer\b|\bapplication gateway\b', 'name': 'Load Balancer'},
                'api_gateway': {'pattern': r'\bapi management\b|\bapi\b', 'name': 'API Management'},
                'compute': {'pattern': r'\bvirtual machine\b|\bvm\b|\binstance\b', 'name': 'Virtual Machine'},
                'serverless': {'pattern': r'\bazure functions\b|\bfunctions\b|\bcontainer apps\b', 'name': 'Azure Functions'},
                'database_sql': {'pattern': r'\bazure sql database\b|\bsql server\b|\bdatabase\b', 'name': 'Azure SQL DB'},
                'database_nosql': {'pattern': r'\bcosmos db\b|\bnosql\b', 'name': 'Cosmos DB'},
                'cache': {'pattern': r'\bazure cache for redis\b|\bcache\b|\bredis\b', 'name': 'Redis Cache'},
                'storage_object': {'pattern': r'\bblob storage\b|\bcontainer\b|\bobject storage\b', 'name': 'Blob Storage'},
                'storage_block': {'pattern': r'\bmanaged disk\b|\bdisk\b', 'name': 'Managed Disk'},
                'queue': {'pattern': r'\bazure queue storage\b|\bservice bus\b|\bqueue\b', 'name': 'Queue/Service Bus'},
                'notification': {'pattern': r'\bevent grid\b|\bnotification hub\b', 'name': 'Event Grid/Hub'},
                'vpc': {'pattern': r'\bvirtual network\b|\bvnet\b|\bnetwork\b', 'name': 'Virtual Network'},
                'security': {'pattern': r'\bnetwork security group\b|\bnsg\b|\bazure firewall\b|\bwaf\b', 'name': 'NSG/Firewall'},
                'iam': {'pattern': r'\bazure active directory\b|\bentra id\b|\brbac\b|\bidentity\b', 'name': 'Entra ID (AD)'},
                'monitoring': {'pattern': r'\bazure monitor\b|\blog analytics\b|\bmonitor\b', 'name': 'Azure Monitor'},
                'container_registry': {'pattern': r'\bazure container registry\b|\bacr\b', 'name': 'ACR'},
                'ci_cd': {'pattern': r'\bazure devops\b|\bpipelines\b|\bgithub actions\b', 'name': 'Azure DevOps'},
                'data_warehouse': {'pattern': r'\bsynapse analytics\b|\bdata warehouse\b', 'name': 'Synapse Analytics'},
                'analytics': {'pattern': r'\bdata factory\b|\bdatabricks\b|\banalytics\b', 'name': 'Data Factory'},
                'auth': {'pattern': r'\bazure active directory b2c\b|\bentra external id\b|\bauth\b', 'name': 'Entra External ID'},
            }
        }
        
        # Define layer priorities based on universal concepts
        self.layer_priority = {
            'user': 0, 'internet': 0,
            'dns': 1, 'cdn': 1, 
            'load_balancer': 2, 'api_gateway': 2, 'auth': 2,
            'compute': 3, 'serverless': 3, 
            'cache': 4, 'queue': 4, 'notification': 4,
            'database_sql': 5, 'database_nosql': 5, 'data_warehouse': 5, 
            'storage_object': 6, 'storage_block': 6, 'analytics': 6,
            'vpc': 7, 'security': 7, 'iam': 7, 'monitoring': 7, 
            'container_registry': 8, 'ci_cd': 8
        }


    def parse_components(self, plan_text: str, platform: str) -> List[Dict]:
        """Parse components based on platform."""
        components = []
        plan_lower = plan_text.lower()
        platform_patterns = self.platform_services.get(platform.lower())

        if not platform_patterns:
            print(f"Warning: Unknown platform '{platform}'. Using generic parsing.")
            # Fallback to generic terms if platform unknown or add a generic map
            platform_patterns = {
                 'user': {'pattern': r'users?', 'name': 'User'},
                 'load_balancer': {'pattern': r'load balancer', 'name': 'Load Balancer'},
                 'compute': {'pattern': r'server|compute|instance', 'name': 'Compute'},
                 'database_sql': {'pattern': r'database|sql', 'name': 'Database'},
                 'storage_object': {'pattern': r'storage|bucket', 'name': 'Storage'},
            }


        added_concepts = set()
        for concept, details in platform_patterns.items():
            if re.search(details['pattern'], plan_lower):
                if concept not in added_concepts:
                    components.append({
                        'concept': concept,
                        'name': details['name'], # Platform-specific name
                        'icon': self.service_icons.get(concept, '❓'),
                        'layer': self.layer_priority.get(concept, 99) # Assign layer
                    })
                    added_concepts.add(concept)
                    
        # Sort components primarily by layer, then alphabetically by name for consistency
        components.sort(key=lambda x: (x['layer'], x['name']))
        return components

    def build_diagram_text(self, components: List[Dict], title: str) -> str:
        """Builds a layered ASCII diagram text."""
        if not components:
            return f"```text\nNo specific components detected for {title}.\n```"

        diagram_lines = []
        
        # Group components by layer
        layers: Dict[int, List[Dict]] = {}
        for comp in components:
            layer = comp['layer']
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(comp)

        # Determine max width needed (simple estimation)
        max_label_width = 0
        for comps in layers.values():
             layer_width = sum(len(f"{c['icon']} {c['name']}") + 4 for c in comps) # Icon, space, name, padding
             max_label_width = max(max_label_width, layer_width)
        
        box_width = max(len(title) + 4, max_label_width, 40) # Ensure minimum width
        
        # Title Box
        diagram_lines.append("┌" + self.chars['horizontal'] * box_width + "┐")
        diagram_lines.append(f"│ {title.center(box_width-2)} │")
        diagram_lines.append("├" + self.chars['horizontal'] * box_width + "┤")

        # Layer Boxes
        sorted_layers = sorted(layers.keys())
        for i, layer_num in enumerate(sorted_layers):
            layer_components = layers[layer_num]
            
            # --- Draw components in the layer ---
            # Simple approach: list components side-by-side if space allows, 
            # otherwise stack them. For chat, stacking is often clearer.
            
            for comp in layer_components:
                 comp_text = f"{comp['icon']} {comp['name']}"
                 diagram_lines.append(f"│ {comp_text.ljust(box_width-2)} │")

            # --- Draw connector if not the last layer ---
            if i < len(sorted_layers) - 1:
                arrow_line = self.chars['arrow_down'].center(box_width)
                # Ensure the arrow line fits within the box borders
                diagram_lines.append("│" + arrow_line[1:-1] + "│") # Center arrow without borders

        # Bottom Box
        diagram_lines.append("└" + self.chars['horizontal'] * box_width + "┘")

        # Wrap in Markdown code block
        return "```text\n" + "\n".join(diagram_lines) + "\n```"

    def create_architecture_diagram(self, plan_text: str, platform: str, title_prefix: str = "Architecture") -> str:
        """Main entry point to create the diagram string."""
        if not platform:
             return "```text\nError: Target platform not specified.\n```"
             
        platform_name = platform.upper()
        full_title = f"{title_prefix} on {platform_name}"
        
        components = self.parse_components(plan_text, platform)
        diagram_text = self.build_diagram_text(components, full_title)
        return diagram_text

# --- Helper function for ADK tool ---
def generate_ascii_diagram(plan_text: str, target_platform: str) -> str:
    """Generates an ASCII diagram based on the plan and platform."""
    if not plan_text:
        return "```text\nNo architecture plan provided to generate diagram.\n```"
    if not target_platform:
        return "```text\nTarget platform (aws, gcp, azure) must be specified.\n```"
        
    generator = ASCIIDiagramGenerator()
    return generator.create_architecture_diagram(plan_text, target_platform)