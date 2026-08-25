# Approval and capability gates

Read this reference when selected work requests credentials, broad permissions, destructive actions, legal or billing actions, paid execution, persistent automation, unverified publishers, or material scope expansion.

Approval must bind the exact action and scope. Paid model execution additionally names models, a positive maximum call or token budget, and estimated cost with currency. The requested and approved manifests must match.

`ready-for-human` work and applicable decision conflicts pause unconditionally until the human completes the work or explicitly revises the decision boundary.

Record sanitized blockers and the precise next approval action in the existing checkpoint. Keep secrets, provider responses, legal text, billing data, and private identifiers out of it.

Capability work uses a bounded ticket that records source, publisher, immutable version or commit when available, requested permissions, and reason. It consumes the mutation capacity of its registered resource claim. The root proposes and delegates approved capability work; it does not install or apply it directly.

