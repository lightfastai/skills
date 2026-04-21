class ComponentBrief {
  name string @assert(nonempty_name, {{ this|length > 0 }})
  responsibility string @assert(nonempty_responsibility, {{ this|length > 0 }})
}

class AbstractionLayerBrief {
  name string @assert(nonempty_name, {{ this|length > 0 }})
  responsibility string @assert(nonempty_responsibility, {{ this|length > 0 }})
}

class FieldBrief {
  name string @assert(nonempty_name, {{ this|length > 0 }})
  type_expression string @assert(nonempty_type_expression, {{ this|length > 0 }})
  description string @assert(nonempty_description, {{ this|length > 0 }})
  required bool
}

class EntityBrief {
  name string @assert(nonempty_name, {{ this|length > 0 }})
  description string @assert(nonempty_description, {{ this|length > 0 }})
  fields FieldBrief[]
}

class SpecBrief {
  service_name string @assert(nonempty_service_name, {{ this|length > 0 }})
  purpose string @assert(nonempty_purpose, {{ this|length > 0 }})
  operational_problems string[]
  goals string[]
  non_goals string[]
  important_boundaries string[]
  components ComponentBrief[]
  abstraction_layers AbstractionLayerBrief[]
  external_dependencies string[]
  entities EntityBrief[]
  unresolved_questions string[]
  update_request string?
  existing_spec string?
}

class SpecCritique {
  contradictions string[]
  implementation_leaks string[]
  ambiguous_terms string[]
  missing_sections string[]
}
