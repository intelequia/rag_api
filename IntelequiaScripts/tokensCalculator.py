import tiktoken

def tokensCalculator(data, embeddingModel):

  totalTokens = 0
  encoding = tiktoken.encoding_for_model(embeddingModel)

  for document in data:
    text = document.page_content
    tokens = encoding.encode(text)
    totalTokens += len(tokens)

  return totalTokens 

def dataCalculator (data):
  dataLength = 0

  for document in data:
    text = document.page_content
    dataLength += len(text)

  return dataLength 
