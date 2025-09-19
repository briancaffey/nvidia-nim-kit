export interface LogprobAlternative {
  token: string
  logprob: number
}

export interface Token {
  text: string
  logprob?: number
  top_logprobs?: LogprobAlternative[]
}

export function parseLogprobsFromResponse(response: any): Token[] {
  // Handle both chat completions and text completions
  const choice = response?.choices?.[0]

  // Try different possible logprobs structures
  let logprobsContent = null

  if (choice?.logprobs?.content) {
    logprobsContent = choice.logprobs.content
  } else if (choice?.logprobs) {
    logprobsContent = choice.logprobs
  } else if (response?.logprobs?.content) {
    logprobsContent = response.logprobs.content
  } else if (response?.logprobs) {
    logprobsContent = response.logprobs
  }

  if (!logprobsContent) {
    console.log('No logprobs content found in response:', response)
    return []
  }

  const tokens: Token[] = []

  // Handle array-based logprobs format (completion responses)
  if (Array.isArray(logprobsContent)) {
    for (const item of logprobsContent) {
      if (item.token) {
        const token: Token = {
          text: item.token,
          logprob: item.logprob
        }

        if (item.top_logprobs && Array.isArray(item.top_logprobs)) {
          token.top_logprobs = item.top_logprobs.map((alt: any) => ({
            token: alt.token,
            logprob: alt.logprob
          }))
        }

        tokens.push(token)
      }
    }
  }
  // Handle object-based logprobs format with separate arrays (completion responses)
  else if (logprobsContent.tokens && Array.isArray(logprobsContent.tokens)) {
    const tokenTexts = logprobsContent.tokens
    const tokenLogprobs = logprobsContent.token_logprobs || []
    const topLogprobs = logprobsContent.top_logprobs || []

    for (let i = 0; i < tokenTexts.length; i++) {
      const token: Token = {
        text: tokenTexts[i],
        logprob: tokenLogprobs[i]
      }

      // Handle top_logprobs array format
      if (topLogprobs[i] && typeof topLogprobs[i] === 'object') {
        token.top_logprobs = Object.entries(topLogprobs[i]).map(([tokenText, logprob]) => ({
          token: tokenText,
          logprob: logprob as number
        }))
      }

      tokens.push(token)
    }
  }

  return tokens
}

export function parseLogprobsFromStreamingChunks(chunks: any[]): Token[] {
  const tokens: Token[] = []
  let currentTokens: Token[] = []

  for (const chunk of chunks) {
    // Check for logprobs in streaming format (delta.logprobs) - chat completions
    if (chunk.choices?.[0]?.delta?.logprobs?.content) {
      // Create a mock response structure for the existing parser
      const mockResponse = {
        choices: [{
          logprobs: chunk.choices[0].delta.logprobs
        }]
      }
      const chunkTokens = parseLogprobsFromResponse(mockResponse)
      currentTokens = [...currentTokens, ...chunkTokens]
    }
    // Check for completion streaming format (logprobs directly in choices) - text completions
    else if (chunk.choices?.[0]?.logprobs) {
      const chunkTokens = parseLogprobsFromResponse(chunk)
      currentTokens = [...currentTokens, ...chunkTokens]
    }
    // Also check for non-streaming format (logprobs.content)
    else if (chunk.choices?.[0]?.logprobs?.content) {
      const chunkTokens = parseLogprobsFromResponse(chunk)
      currentTokens = [...currentTokens, ...chunkTokens]
    }
  }

  return currentTokens
}

export function hasLogprobs(response: any): boolean {
  if (!response) return false

  // Check standard OpenAI format
  if (response.choices?.[0]?.logprobs?.content) return true
  if (response.choices?.[0]?.delta?.logprobs?.content) return true

  // Check alternative formats
  if (response.choices?.[0]?.logprobs) return true
  if (response.logprobs?.content) return true
  if (response.logprobs) return true

  // Check for completion format with separate arrays
  const choice = response.choices?.[0]
  if (choice?.logprobs?.tokens && Array.isArray(choice.logprobs.tokens)) return true

  return false
}

export function hasLogprobsInChunks(chunks: any[]): boolean {
  if (!chunks || chunks.length === 0) return false

  return chunks.some(chunk => {
    // Check for completion streaming format (logprobs directly in choices)
    if (chunk.choices?.[0]?.logprobs) return true
    // Check for chat streaming format (delta.logprobs)
    if (chunk.choices?.[0]?.delta?.logprobs?.content) return true
    return false
  })
}

export function extractTextFromTokens(tokens: Token[]): string {
  return tokens.map(token => cleanTokenText(token.text)).join('')
}

// Clean token text by replacing GPT-2/BPE markers
function cleanTokenText(text: string): string {
  return text
    .replace(/Ġ/g, ' ')  // Replace Ġ with space
    .replace(/Ċ/g, '\n') // Replace Ċ with newline
}
