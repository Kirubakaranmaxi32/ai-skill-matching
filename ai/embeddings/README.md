# Embeddings Module (`ai/embeddings`)

## Phase Implementation Notice
*Scheduled for implementation in **Phase 5: AI Project Analysis**.*

## Planned Functionality
- **Text Representation:** Integrates pretrained Sentence Transformers (`all-MiniLM-L6-v2`) to generate 384-dimensional dense semantic vectors from project descriptions and student bios.
- **Preprocessing:** Normalizes technical text, handles acronym expansion, and prepares text chunks for embedding generation.
- **Architectural Boundary:** Sentence Transformer provides representation features only; it is not the matching model.
