client<llm> EvalModel {
  provider "openai-responses"
  options {
    api_key env.AI_GATEWAY_API_KEY
    base_url "https://ai-gateway.vercel.sh/v1"
    model "openai/gpt-5.4"
    reasoning {
      effort "medium"
    }
  }
}
