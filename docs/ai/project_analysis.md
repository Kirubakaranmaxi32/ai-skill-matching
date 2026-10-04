# AI Project Analysis Architecture & Real Pipeline Integration (Phase 5 — Step 2)

## 1. Purpose
The Project Analysis module forms the foundational Natural Language Processing (NLP) layer of the **AI Skill Matching** system (*AI-Driven Student Skill Gap Analysis and Project Team Recommendation System Using Deep Learning*). Its primary purpose is to parse, clean, and analyze project specifications submitted by student project leads, extracting technical skill requirements and computing dense semantic representations using a real pretrained Sentence Transformer without mutating database state or hallucinating requirements.

---

## 2. AI Pipeline
The end-to-end recommendation pipeline consists of two distinct machine learning stages:
1. **Unsupervised Pretrained NLP Representation (Phase 5 Steps 1 & 2)**: Converts unstructured project descriptions into clean text tokens and real dense semantic vectors using a pretrained bi-encoder model running on CPU.
2. **Supervised Trainable Deep Learning Matching Model (Future Steps)**: A PyTorch Multi-Layer Perceptron (MLP) trained to compute compatibility scores between student skill profiles and project requirements.

```
+------------------------------------+
| Real Project Description from DB   |
+------------------------------------+
                  |
                  v
+------------------------------------+
|         Text Preprocessor          |  (Normalizes whitespace, strips markdown, preserves C++, .NET, etc.)
+------------------------------------+
                  |
        +---------+---------+
        |                   |
        v                   v
+---------------+   +------------------------------------+
|   Sentence    |   |     Taxonomy-Guided Extractor      |
|  Transformer  |   | (Exact Matches, Aliases, & Unknown)|
| (all-MiniLM)  |   |                                    |
+---------------+   +------------------------------------+
        |                   |
        v                   v
+---------------+   +------------------------------------+
| 384-Dim Real  |   | Candidates Aligned to Taxonomy IDs |
| Vector on CPU |   | & Unmatched Candidate Terms Flags  |
+---------------+   +------------------------------------+
        |                   |
        +---------+---------+
                  |
                  v
+------------------------------------+
|       ProjectAnalysisResult        |  (Non-destructive advisory payload: embedding meta + skills)
+------------------------------------+
                  |
                  v  (Future Phase 5 Steps)
+------------------------------------+
|         Skill-Gap Analysis         |  (Difference between required & student skills)
+------------------------------------+
                  |
                  v
+------------------------------------+
|          PyTorch MLP Model         |  (Trainable Deep Learning compatibility scoring)
+------------------------------------+
                  |
                  v
+------------------------------------+
|     Explainable Recommendations    |  (Ranked candidates with skill gap insights)
+------------------------------------+
```

---

## 3. Text Preprocessing
The `TextPreprocessor` module (`backend/app/services/project_analysis/preprocessor.py`) cleans raw user descriptions for downstream embedding and skill extraction:
- **Unicode Normalization**: Applies NFKC normalization to ensure consistent character encoding.
- **Noise & Formatting Stripping**: Removes markdown headers (`#`), bullet points (`*`, `-`, `•`), bold/italic markers (`**`, `_`), and links (`[label](url)` $\rightarrow$ `label`) while keeping interior tokens intact.
- **Technical Vocabulary Preservation**: Explicitly retains special programming nomenclature, punctuation, and framework symbols, including:
  - Language symbols: `C++`, `C#`, `.NET`
  - Web & framework identifiers: `Node.js`, `React.js`, `Vue.js`
  - Domain abbreviations: `AI/ML`, `CI/CD`, `TCP/IP`
- **Whitespace Normalization**: Collapses carriage returns, line feeds, and multiple spaces into single spaces.
- **Trivial Text Detection**: Flags descriptions under 10 characters or consisting solely of whitespace as `not_ready`.

---

## 4. Sentence Transformer Model & Embedding Architecture
- **Model Configured**: `sentence-transformers/all-MiniLM-L6-v2` (configured centrally in `backend/app/core/config.py`).
- **Actual Embedding Dimensionality**: **384 dimensions** (verified dynamically at runtime via `get_embedding_dimension()` and vector length).
- **Execution Device**: **CPU** (`device="cpu"`). CUDA is not required and is explicitly disabled to ensure predictable, portable execution across development environments.
- **Why Sentence Transformers is Used**:
  - Encodes the holistic semantic context and intent of project descriptions into fixed-size continuous dense vector space.
  - Efficient bi-encoder architecture optimized for sentence-level semantic representations.
  - Enables downstream cosine similarity computation with student portfolios and domain interests.
- **CRITICAL DISTINCTION**:
  > [!IMPORTANT]
  > The Sentence Transformer is **NOT** trained by us and is **NOT** our primary Deep Learning recommendation model. It serves strictly as an off-the-shelf NLP representation component to convert English text into a 384-dimensional vector space. The trainable Deep Learning model is the downstream **PyTorch Multi-Layer Perceptron (MLP)**.
- **Pluggable Interface**: Abstracted behind the `BaseEmbeddingProvider` protocol (`ai/embeddings/__init__.py`), enabling future replacement with alternative models or local inference runtimes:
```python
class BaseEmbeddingProvider(Protocol):
    @property
    def model_name(self) -> str: ...
    @property
    def embedding_dimension(self) -> Optional[int]: ...
    @property
    def is_available(self) -> bool: ...
    @property
    def status_message(self) -> str: ...
    def embed_text(self, text: str) -> Optional[List[float]]: ...
```
- **Deterministic Inference**: Repeated evaluations on the same normalized project text yield identical embedding vectors within floating-point tolerance ($< 10^{-5}$).
- **Why Embeddings Are Not Yet Stored in Database**:
  - Phase 5 Step 2 focuses strictly on runtime embedding integration, dimension verification, and non-destructive advisory analysis.
  - Storing embeddings would require modifying database tables (e.g. `vector` extensions or JSON columns), which violates phase boundary constraints prohibiting schema mutations.
  - Embeddings remain ephemeral in memory during this step.

---

## 5. Skill Extraction Architecture
The skill extraction layer (`ai/skill_extraction/__init__.py`) detects technical competencies referenced in the project text:
- **`CandidateSkill` Data Structure**:
  - `raw_term`: String matched in source text.
  - `normalized_name`: Canonical skill name.
  - `confidence`: Match fidelity score (0.0 to 1.0).
  - `source`: Extraction technique (`taxonomy_exact`, `taxonomy_alias`, `unmatched_candidate`).
  - `matched_skill_id`: UUID of the existing taxonomy record (or `None` for unmatched candidates).
  - `category`: Skill domain category (e.g., `ai_ml`, `frontend`, `backend`, `unmatched`).
- **Alias Resolution**: Maps real-world terminology variations to canonical taxonomy entries:
  - `"python programming"`, `"python 3"` $\rightarrow$ `"Python"`
  - `"pytorch deep learning"`, `"torch"` $\rightarrow$ `"PyTorch"`
  - `"react.js"`, `"react framework"` $\rightarrow$ `"React"`
  - `"fastapi framework"` $\rightarrow$ `"FastAPI"`
- **Unmatched Candidate Detection**: Distinguishes between recognized master skills and unrecognized candidate technical terms (e.g. `Kubernetes`, `GraphQL`, `ROS2`), ensuring no skills are created or assumed without human approval.
- **Duplicate Prevention**: Consolidates multiple aliases and mentions of the same skill to prevent duplicate suggestions.

---

## 6. Existing Skill Taxonomy Integration
- The extractor queries the **existing Phase 3 master skills taxonomy** (`public.skills` via `get_skills()`).
- **Zero Schema Duplication**: No new skill tables or duplicate rows are created.
- **Non-Destructive**: Identified skills are returned in the analysis payload for user review and are **never** automatically saved or attached to the project.

---

## 7. ProjectAnalysisResult Structure
Defined in `backend/app/schemas/project_analysis.py`:
```json
{
  "project_id": "2d2d541b-d887-4e3b-ad87-66efe705d4a7",
  "normalized_description": "Building a Python backend with FastAPI and Docker containers.",
  "embedding_available": true,
  "embedding_dimension": 384,
  "model_name": "sentence-transformers/all-MiniLM-L6-v2",
  "extracted_skills": [
    {
      "skill_name": "FastAPI",
      "skill_id": "a1000000-0000-0000-0000-000000000006",
      "category": "backend",
      "confidence": 0.95,
      "source": "taxonomy_exact"
    },
    {
      "skill_name": "Python",
      "skill_id": "a1000000-0000-0000-0000-000000000001",
      "category": "ai_ml",
      "confidence": 0.95,
      "source": "taxonomy_exact"
    },
    {
      "skill_name": "Docker",
      "skill_id": "a1000000-0000-0000-0000-000000000008",
      "category": "cloud_devops",
      "confidence": 0.95,
      "source": "taxonomy_exact"
    }
  ],
  "analysis_status": "completed",
  "warnings": []
}
```
### Status Lifecycle:
- `completed`: Description processed, real 384-dim CPU embedding computed, skills extracted.
- `partial`: Skills extracted via taxonomy rules; embedding skipped or pending model weights.
- `not_ready`: Description empty, whitespace, or shorter than 10 characters.

---

## 8. API Design & Security
### `POST /api/v1/projects/{project_id}/analyze`
- **Authentication**: Requires valid Supabase JWT Bearer token via `get_current_user` (`HTTP 401 Unauthorized` if token missing or invalid).
- **Authorization**: Validates that `current_user.id` owns the project (`HTTP 403 Forbidden` if non-owner).
- **Validation**: Rejects non-existent projects with `HTTP 404 Not Found` and invalid UUIDs with `HTTP 422 Unprocessable Entity`.
- **Side Effects**: Pure read-only analytical endpoint; does not mutate `projects`, `project_skills`, or `project_members`.
- **Information Returned**: Returns `project_id`, `normalized_description`, `extracted_skills`, `embedding_available`, `embedding_dimension`, `model_name`, `analysis_status`, and `warnings`. The full dense vector array is intentionally not returned to conserve network bandwidth and match consumer requirements.

---

## 9. Error Handling Matrix
| Condition | Trigger | Handled By | Response / Status |
|:---|:---|:---|:---|
| Unauthenticated | Missing / invalid JWT | `get_current_user` | HTTP 401 Unauthorized |
| Non-owner access | User ID $\neq$ Project `owner_id` | `ProjectAnalysisService` | HTTP 403 Forbidden |
| Project not found | Non-existent UUID | `ProjectAnalysisService` | HTTP 404 Not Found |
| Invalid UUID | Non-UUID path param | FastAPI / Pydantic | HTTP 422 Unprocessable Entity |
| Empty / Short description | `< 10` chars or whitespace | `TextPreprocessor` | `analysis_status="not_ready"` |
| Model weights missing | Package missing / no cache | `SentenceTransformerEmbeddingProvider` | `embedding_available=False`, status `"partial"` |
| Inference error | Unhandled tensor exception | `SentenceTransformerEmbeddingProvider` | Logged, returns `None`, graceful diagnostic warning |

---

## 10. Why Analysis Does Not Mutate Project Skills
1. **Human-in-the-Loop Architecture**: Student project leads retain creative and administrative control over their projects. AI analysis serves strictly as an intelligent assistant, identifying candidate technologies for the owner's review.
2. **Preventing Erroneous Skill Inflation**: Automated addition of detected keywords could lead to noise, false requirements, or inaccurate proficiency targets.
3. **Database Immutability**: Read-only analytical endpoints ensure zero risk of accidental data corruption or schema pollution.

---

## 11. Why MLP / Recommendation Engine Has NOT Been Implemented Yet
1. **Step-by-Step Architecture**: In accordance with system specifications, Phase 5 Step 2 covers **representation only** (text preprocessing, real Sentence Transformer embeddings, and skill taxonomy extraction).
2. **Feature Engineering Prerequisite**: The PyTorch MLP requires input features that combine skill-gap matrices with semantic similarity vectors. Feature vector preparation is scheduled for future Phase 5 steps.
3. **No Premature Optimization or Hallucination**: Model training, weights persistence, and candidate ranking are intentionally reserved for their dedicated phases to maintain verification rigor. No claims of model accuracy or recommendation performance are made at this stage.
