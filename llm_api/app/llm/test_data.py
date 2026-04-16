# This file contains mock input data.
# It helps test the LLM module without waiting for the real DB / CRAG module.

sample_request = {
    "document_id": "doc_001",
    "question": "Explain infection prevention in simple words",
    "validated_chunks": [
        {
            "chunk_id": "c1",
            "page": 2,
            "text": "Infection prevention includes hand hygiene and proper use of personal protective equipment.",
            "score": 0.93
        },
        {
            "chunk_id": "c2",
            "page": 3,
            "text": "Hand hygiene reduces the spread of harmful microorganisms in healthcare settings.",
            "score": 0.89
        }
    ],
    "retrieval_status": "good"
}