enum ClaimKind {
  Fact
  Thesis
  Boundary
  Constraint
  OpenQuestion
}

enum Confidence {
  High
  Medium
  Low
}

class Claim {
  statement string @assert(nonempty_statement, {{ this|length > 0 }})
  kind ClaimKind
  confidence Confidence
  sources string[] @assert(has_source, {{ this|length > 0 }})
}
