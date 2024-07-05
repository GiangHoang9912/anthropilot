import axios from 'axios';

type AnthropicPayload = {
  is_stream: boolean
  model: string
  message: string
  open_ai_key: string
  anthropic_api_key: string
  workspace: string
};

export class Anthropilot {
  private model;
  private api_base_url;
  private open_ai_key;
  private anthropic_api_key;

  constructor(payload: { model: string, api_base_url: string, open_ai_key: string, anthropic_api_key: string }) {
    const { model, api_base_url, open_ai_key, anthropic_api_key } = payload;
    this.model = model;
    this.api_base_url = api_base_url;
    this.open_ai_key = open_ai_key;
    this.anthropic_api_key = anthropic_api_key;
  }

  async invoke(message: string, workspace: string): Promise<string> {
    const config: AnthropicPayload = {
      is_stream: false,
      workspace: workspace,
      model: this.model,
      open_ai_key: this.open_ai_key,
      anthropic_api_key: this.anthropic_api_key,
      message: message
    };
    console.log("config", config);
    const response = await axios.post(this.api_base_url, config);
    console.log("response", response);
    return response.data as string;
  }
}