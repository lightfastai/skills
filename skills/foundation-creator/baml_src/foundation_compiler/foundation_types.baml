class FoundationKernel {
  name string @assert(nonempty_name, {{ this|length > 0 }})
  mission string?
  primitive string?
  theses string[]
  problems string[]
  actors string[]
  surfaces string[]
  boundaries string[]
  strategic_bets string[]
  open_questions string[]
}

class FoundationCritique {
  contradictions string[]
  vague_claims string[]
  implementation_leaks string[]
  unsupported_inferences string[]
  missing_boundaries string[]
  leverage_questions string[]
}

class FoundationBrief {
  title string @assert(nonempty_title, {{ this|length > 0 }})
  summary string @assert(nonempty_summary, {{ this|length > 0 }})
  core_theses string[]
  boundaries string[]
  actor_model string[]
  surfaces string[]
  strategic_bets string[]
  unresolved_questions string[]
}
