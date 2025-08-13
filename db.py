from dotenv import load_dotenv
import os
from google import genai
from google.genai import types, errors
from chromadb import Documents, EmbeddingFunction, Embeddings
from google.api_core import retry
import chromadb

Gemini_Key = "AIzaSyB0giFpRn5roQqlOeCNqBTgRD4R_YUfkJg"
load_dotenv()
api_key = os.getenv("GEMINI_KEY")

client = genai.Client(api_key=Gemini_Key)

is_retriable = lambda e: (isinstance(e, errors.APIError) and e.code in {429, 503})


class GeminiEmbeddingFunction(EmbeddingFunction):
    document_mode = True
    batch_size = 16

    @retry.Retry(predicate=is_retriable)
    def __call__(self, input: Documents) -> Embeddings:
        task_type = "retrieval_document" if self.document_mode else "retrieval_query"
        all_embeddings = []
        for i in range(0, len(input), self.batch_size):
            batch = input[i:i + self.batch_size]
            response = client.models.embed_content(
                model="models/gemini-embedding-001",
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=768
                )
            )
            all_embeddings.extend([e.values for e in response.embeddings])
        return all_embeddings


embed_fn = GeminiEmbeddingFunction()


def get_text_db():
    chroma_client = chromadb.Client()
    text_db = chroma_client.get_or_create_collection(
        name="pdfcontent_text",
        embedding_function=embed_fn,
        metadata={"type": "text"})
    return text_db


def get_rag_response(docs, query):
    database = get_text_db()

    if len(database.peek()['ids']) < len(docs):
        database.add(documents=docs, ids=[str(i) for i in range(len(docs))])

    embed_fn.document_mode = False

    n_results = 3
    result = database.query(query_texts=[query], n_results=n_results)
    all_passages = result["documents"][0]

    query_oneline = query.replace("\n", " ")

    prompt = f"""You are a helpful and informative bot that answers questions using text from the reference passages included below.
Be sure to respond in a complete sentence, being comprehensive, including all relevant background information.
However, you are talking to a non-technical audience, so be sure to break down complicated concepts and
strike a friendly and conversational tone. If the passage is irrelevant to the answer, you may ignore it.
After your main answer, provide a summary of the response in 10 words or less, labeled "SUMMARY:".

QUESTION: {query_oneline}
"""

    for i, passage in enumerate(all_passages):
        passage_oneline = passage.replace("\n", " ")
        prompt += f"PASSAGE {i + 1}: {passage_oneline}\n"

    config = types.GenerateContentConfig(temperature=0.2)
    answer = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
        config=config
    )

    full_response_text = answer.text
    summary_prefix = "SUMMARY:"

    if summary_prefix in full_response_text:
        summary = full_response_text.split(summary_prefix)[1].strip()
    else:
        summary = "Summary not available."

    print("User Query:", query)
    print("Summary:", summary)

    return summary