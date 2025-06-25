# LLM Provider Configuration Specification

**Version**: 1.3  
**Last Updated**: 2025-06-11

## Overview

This specification defines a standardized configuration structure for Large Language Model providers. It supports multiple providers through a consistent map-based data model compatible with TOML, YAML, JSON, and similar formats.

## Configuration Schema

### Provider Configuration

```
provider:                          # Root configuration map
  name: string                     # Required: Provider identifier
  api_key: string                  # Required: Authentication key (supports variables)
  default_model: string            # Optional: Default model selection
  
  connection:                      # Required: Network configuration
    base_url: string              # Required: API endpoint (https:// or http://)
    headers: map[string, string]  # Optional: Non-auth headers
    
  opts:                           # Optional: Provider-specific options
    # Examples by provider:
    organization: string          # OpenAI: org-xxx format
    project: string               # OpenAI: proj-xxx format
    anthropic_version: string     # Anthropic: API version
    beta: list[string]           # Anthropic: Beta features
    api_version: string          # Azure: API version
    resource_name: string        # Azure: Resource identifier
    region: string               # AWS: Region code
    profile: string              # AWS: Profile name
    
  endpoints:                      # Required: API paths
    chat: string                  # Required: Chat completion path (starts with /)
    models: string                # Optional: Model listing path
    
  models: list[                   # Required: Available models
    name: string                  # Required: Internal identifier
    id: string                    # Required: Provider model ID
    capabilities: list[string]    # Required: ["oneshot"|"reasoning"], ["text", "image"]
    
    limits:                       # Required: Resource boundaries
      input_tokens: integer       # Range: [1, 10,000,000]
      output_tokens: integer      # Range: [1, 1,000,000]
      context_window: integer     # Range: [1, 10,000,000]
      rate_limit: integer         # Optional: RPM [1, 1,000,000]
      
    cost:                         # Required: Pricing per 1M tokens
      input: float                # Range: [0.0001, 10,000.00]
      output: float               # Range: [0.0001, 10,000.00]
      per_tokens: integer         # Fixed: 1000000
      currency: string            # Optional: ISO 4217 (default: USD)
      
    opts:                         # Optional: Model parameters
      temperature: float          # Range: [0.0, 2.0]
      top_p: float               # Range: [0.0, 1.0]
      max_output_tokens: integer  # Output length limit
      reasoning_effort: string    # For reasoning models
  ]

profiles: list[                   # Required: Usage presets
  name: string                    # Required: Profile identifier
  description: string             # Optional: Purpose description
  model: string                   # Optional: Model override
  # Additional model opts...
]
```

## Standardized Profiles

Providers must implement these four required profiles with exact names. Additional custom profiles may be added after the required ones.

### Required Profiles

**oneshot**
- Purpose: General-purpose tasks without reasoning
- Model: Largest available non-reasoning model
- Temperature: 0.7-1.0 (provider discretion)
- Standard output token limits

**oneshot-fast**
- Purpose: Rapid responses without reasoning
- Model: Smallest non-reasoning model with acceptable quality
- Temperature: 0.7 recommended
- Limited output tokens (1024-4096)

**reason**
- Purpose: Brief chain-of-thought reasoning
- Model: Smallest reasoning-capable model
- Configuration: Optimized for concise reasoning
- Output tokens: Constrained to encourage brevity

**reason-high**
- Purpose: Extended chain-of-thought reasoning
- Model: Largest reasoning-capable model  
- Configuration: Maximum reasoning effort/depth
- Output tokens: Maximum supported by model

### Custom Profiles

Providers may include additional profiles after the required four. Common patterns include:
- **budget**: Cost-optimized configuration
- **creative**: High temperature (0.9+) for creative content
- **code**: Low temperature (0.1-0.3) for technical output
- **json**: Structured output generation
- **extended**: Maximum output length for non-reasoning models

Custom profiles should include descriptive names and clear purpose descriptions.

## Variable Resolution

Variables enable dynamic values through `${source:path}` syntax in any string field.

**Sources:**
- `${env:NAME}` - Environment variables
- `${self:path.to.value}` - Internal references
- `${self:list[index]}` - Array access
- `\${literal}` - Escaped literal

**Resolution Order:**
1. Parse configuration structure
2. Resolve all `${env:...}` variables
3. Resolve all `${self:...}` references (error on cycles)

**Path Grammar:**
```
path     := segment (accessor)*
accessor := '.' segment | '[' index ']'
segment  := [a-zA-Z_][a-zA-Z0-9_]*
index    := [0-9]+
```

## Data Types

**String Types:**
- `api_key`: 1-512 chars, alphanumeric + `-_.`
- `base_url`: Valid URI with scheme, no trailing slash
- `currency`: ISO 4217 three-letter code

**Capabilities:**
- Model types (one required): `oneshot`, `reasoning`
- Functions (one+ required): `text`, `image`

**Standards:**
- Tokens: Provider-specific, costs per 1M
- Rates: Requests per minute, sliding window
- Time: ISO 8601 dates, RFC 3339 timestamps

## Error Types

- **ConfigParseError**: Invalid syntax
- **VariableResolutionError**: Undefined variable
- **CyclicReferenceError**: Circular reference
- **PathNotFoundError**: Invalid path
- **TypeMismatchError**: Wrong value type
- **ValidationError**: Constraint violation

## Configuration Layout

### Organization

1. Provider metadata
2. Connection settings  
3. Provider options
4. API endpoints
5. Models (by tier: flagship → specialized → budget → legacy)
6. Profiles (required four → custom profiles)

### Documentation

```
# Provider Configuration
# Version: X.Y
# Last Updated: YYYY-MM-DD

[section]
field = value  # Required|Optional: Description

# ===========================
# Section Name
# ===========================
```

### Formatting

- Logical grouping with consistent spacing
- Aligned values within sections
- Comments above or inline with fields
- Single blank lines between sections
- Double blank lines between major sections

## Format Syntax

### TOML
- Maps → `[table]` or `{inline = "table"}`
- Lists → `["array"]` or `[[array.of.tables]]`
- Comments → `#`
- Variables → `"${env:VAR}"` (quoted)

### YAML
- Maps → Indented key-value pairs
- Lists → Dash-prefixed items
- Comments → `#`
- Variables → Quoted or unquoted

### JSON
- Maps → `{"objects": {}}`
- Lists → `["arrays"]`
- Comments → Not supported (use JSON5)
- Variables → `"${env:VAR}"` (escape: `\\$`)

## Complete Example

```toml
# OpenAI Provider Configuration
# Version: 1.3
# Last Updated: 2025-06-11

[provider]
name = "OpenAI"
api_key = "${env:OPENAI_API_KEY}"
default_model = "gpt-4.1"

[provider.connection]
base_url = "https://api.openai.com/v1"

[provider.opts]
organization = "${env:OPENAI_ORG_ID}"     # Optional: org-xxx format
project = "${env:OPENAI_PROJECT_ID}"      # Optional: proj-xxx format

[provider.endpoints]
chat = "/chat/completions"
models = "/models"

# ===========================
# Latest Models
# ===========================

[[provider.models]]
name = "gpt-4.1"
id = "gpt-4.1"
capabilities = ["oneshot", "text", "image"]

[provider.models.limits]
input_tokens = 1_000_000
output_tokens = 32_768
context_window = 1_000_000
rate_limit = 5_000

[provider.models.cost]
input = 3.00
output = 12.00
per_tokens = 1_000_000

[provider.models.opts]
temperature = 1.0
max_output_tokens = 32_768


# ===========================
# Reasoning Models  
# ===========================

[[provider.models]]
name = "o3"
id = "o3"
capabilities = ["reasoning", "text"]

[provider.models.limits]
input_tokens = 200_000
output_tokens = 100_000
context_window = 200_000

[provider.models.cost]
input = 2.00
output = 8.00
per_tokens = 1_000_000

[provider.models.opts]
reasoning_effort = "medium"  # low, medium, high


# ===========================
# Required Profiles
# ===========================

[[profiles]]
name = "oneshot"
description = "General-purpose tasks without reasoning"
model = "gpt-4.1"
temperature = 0.8
max_output_tokens = 8192

[[profiles]]
name = "oneshot-fast"
description = "Rapid responses without reasoning"
model = "gpt-4.1-nano"
temperature = 0.7
max_output_tokens = 2048

[[profiles]]
name = "reason"
description = "Brief chain-of-thought reasoning"
model = "o3-mini"
reasoning_effort = "medium"
max_output_tokens = 10000

[[profiles]]
name = "reason-high"
description = "Extended chain-of-thought reasoning"
model = "o3"
reasoning_effort = "high"
max_output_tokens = 100000

# ===========================
# Custom Profiles
# ===========================

[[profiles]]
name = "budget"
description = "Cost-optimized configuration"
model = "gpt-4.1-nano"
temperature = 0.7
max_output_tokens = 1024

[[profiles]]
name = "creative"
description = "Creative content generation"
model = "gpt-4.1"
temperature = 0.9
top_p = 0.98
max_output_tokens = 8192
```