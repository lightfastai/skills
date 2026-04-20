enum EvalStatus {
  Pass
  Partial
  Fail
}

class EvalCheck {
  criterion string @assert(nonempty_criterion, {{ this|length > 0 }})
  status EvalStatus
  rationale string @assert(nonempty_rationale, {{ this|length > 0 }})
}

class EvalReport {
  overall_status EvalStatus
  summary string @assert(nonempty_summary, {{ this|length > 0 }})
  checks EvalCheck[]
  open_issues string[]
}

class FoundationEvalPacket {
  packet_name string @assert(nonempty_packet_name, {{ this|length > 0 }})
  task_prompt string @assert(nonempty_task_prompt, {{ this|length > 0 }})
  raw_notes string @assert(nonempty_raw_notes, {{ this|length > 0 }})
  expected_criteria string @assert(nonempty_expected_criteria, {{ this|length > 0 }})
}
