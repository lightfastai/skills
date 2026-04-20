client<llm> EvalModel {
  provider "openai-responses"
  options {
    api_key env.OPENAI_API_KEY
    model "gpt-5-mini"
    reasoning {
      effort "medium"
    }
  }
}
