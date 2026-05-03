Here is a clean, structured documentation you can directly use in your codebase or share with collaborators.

---

# **Unified Invocation Interface Design (invoke Pattern)**

## **1. Objective**

The goal of this design is to introduce a **consistent execution interface** across the codebase using an `invoke()` pattern.

This enables:

* uniform interaction across components
* better modularity and composability
* easier testing and dependency injection
* scalability for future pipeline extensions

---

## **2. Design Philosophy**

Not all functions should be abstracted.

The system distinguishes between three categories:

### **A. Utility Functions (No `invoke()`)**

**Definition**
Small, stateless helper functions with minimal logic.

**Examples**

* string cleaning (`strip`, normalization)
* path validation
* simple transformations

**Why not `invoke()`?**

* Adds unnecessary abstraction
* Reduces readability
* No composability benefit

**Rule**

> Keep utility functions simple and functional.

---

### **B. Factories / Builders (`invoke()` recommended)**

**Definition**
Components responsible for creating runtime objects or services.

**Examples from current codebase**

* Environment loader
* LLM creator
* Embedding model creator
* Vector store creator

**Why use `invoke()`?**

* Standardizes object creation
* Enables easy swapping of implementations
* Improves testability (mock factories)

**Pattern**

```python
class ChatLLMFactory(Invokable[ChatLLMConfig, ChatOllama]):
    def invoke(self, config: ChatLLMConfig) -> ChatOllama:
        ...
```

---

### **C. Pipeline Components (`invoke()` mandatory)**

**Definition**
Core execution units in workflows (e.g., RAG pipelines).

**Examples**

* Retriever
* Reranker
* Query Rewriter
* Answer Generator
* Relevance Grader

**Why `invoke()` is essential**

* Enables chaining of components
* Creates a uniform execution model
* Matches LangChain / LangGraph style abstraction

**Example**

```python
docs = retriever.invoke(query)
ranked_docs = reranker.invoke(docs)
answer = generator.invoke(ranked_docs)
```

---

## **3. Base Interface**

All invokable components must implement the following interface:

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

class Invokable(ABC, Generic[InputT, OutputT]):
    @abstractmethod
    def invoke(self, input_data: InputT) -> OutputT:
        pass
```

---

## **4. Type Safety with Generics**

The use of `TypeVar` ensures:

* strong typing for inputs and outputs
* better readability and debugging
* clear contracts between components

**Example**

```python
class Retriever(Invokable[str, List[Document]]):
    def invoke(self, query: str) -> List[Document]:
        ...
```

---

## **5. Configuration Pattern (Recommended)**

Avoid passing raw dictionaries.

Instead, define structured config objects:

```python
from dataclasses import dataclass

@dataclass
class ChatLLMConfig:
    model_name: str
    base_url: str
    temperature: float = 0.0
```

**Usage**

```python
llm = chat_factory.invoke(ChatLLMConfig(...))
```

---

## **6. Mapping Current Code**

| Existing Function        | Recommended Structure         |
| ------------------------ | ----------------------------- |
| `load_project_env`       | `EnvLoader.invoke()`          |
| `create_chat_llm`        | `ChatLLMFactory.invoke()`     |
| `create_embedding_model` | `EmbeddingFactory.invoke()`   |
| `create_vector_store`    | `VectorStoreFactory.invoke()` |

---

## **7. Design Rules**

### **DO**

* Use `invoke()` for reusable, swappable components
* Use typed input/output contracts
* Keep each class single-responsibility
* Use config objects instead of loose parameters

### **DO NOT**

* Wrap every small function into a class
* Use `dict` as generic input everywhere
* Mix multiple responsibilities in one component
* Over-engineer simple utilities

---

## **8. Benefits**

* **Consistency** → all components behave the same way
* **Composability** → easy pipeline chaining
* **Extensibility** → swap implementations easily
* **Testability** → mock components cleanly
* **Clarity** → clear contracts between modules

---

## **9. Summary**

This design introduces a disciplined structure:

* Utilities remain simple functions
* Factories adopt `invoke()` for consistency
* Pipeline components strictly follow `invoke()`

> The `invoke()` pattern should represent meaningful execution units, not be applied universally.

---
