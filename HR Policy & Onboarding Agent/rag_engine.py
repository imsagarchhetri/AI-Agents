import os
import yaml
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core import PromptTemplate
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from config import settings

def load_policies(policy_dir: str = "data/hr_policies") -> VectorStoreIndex:
    """
    Builds a production RAG index from policy markdowns.
    Production: Replace with Qdrant/Weaviate + incremental ingestion pipeline.
    """
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    Settings.llm = OpenAI(model=settings.router_model, temperature=0.0)
    
    # Load documents with custom metadata parser
    documents = SimpleDirectoryReader(policy_dir).load_data()
    nodes = SimpleNodeParser(chunk_size=512, chunk_overlap=64).get_nodes_from_documents(documents)

    # Enforce metadata structure for filtering
    for node in nodes:
        # Extract frontmatter metadata (simplified: Production: Parse full schema)
        content = node.text
        if content.startswith("---"):
            frontmatter, _, body = content.partition("\n---\n")
            meta = yaml.safe_load(frontmatter)
            if isinstance(meta, dict):
                for k, v in meta.items():
                    node.metadata[k] = str(v)

    index = VectorStoreIndex(nodes, show_progress=False)
    index.storage_context.persist(persist_dir=settings.rag_index_path)
    return index

    
def build_query_engine(index: VectorStoreIndex) -> RetrieverQueryEngine:
    """
    Creates a retrieval query engine with metadata filtering & strict response formatting.
    """
    prompt_template = PromptTemplate(
        "You are an HR compliance assistant. Answer using ONLY the provided policy context.\n"
        "If the answer is not in the context, respond with: 'POLICY_NOT_FOUND'.\n"
        "Always cite the policy version and effective_date.\n"
        "Context: {context_str}\n"
        "Question: {query_str}\n"
        "Answer:"
    )
    
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=3,
        vector_store_query_mode="default"
    )
    
    return RetrieverQueryEngine.from_args(
        retriever=retriever,
        text_qa_template=prompt_template,
        streaming=False
    )