# Decision Log - TTB Label Verification Prototype

## Overview
This document tracks key technical and architectural decisions made during the development of the AI-Powered Alcohol Label Verification App prototype.

## Decision Summary

| Decision # | Title | Link | Outcome |
|------------|-------|------|---------|
| 001 | Programming Language Selection | [Decision 001](#decision-001-programming-language-selection) | ✅ Decided |
| 002 | Web Framework Selection | [Decision 002](#decision-002-web-framework-selection) | ✅ Decided |
| 003 | AI/OCR Service Selection | [Decision 003](#decision-003-aiocr-service-selection) | ✅ Decided |
| 004 | Deployment Platform | [Decision 004](#decision-004-deployment-platform) | ✅ Decided |
| 005 | Sample Label Generator Approach | [Decision 005](#decision-005-sample-label-generator-approach) | ✅ Decided |
| 006 | Deterministic Generation vs AI Image Generation | [Decision 006](#decision-006-deterministic-generation-vs-ai-image-generation) | ✅ Decided |
| 007 | JPEG-Only Output Format | [Decision 007](#decision-007-jpeg-only-output-format) | ✅ Decided |
| 008 | CLI-First Development Approach | [Decision 008](#decision-008-cli-first-development-approach) | ✅ Decided |
| 009 | Graceful Degradation Validation Strategy | [Decision 009](#decision-009-graceful-degradation-validation-strategy) | ✅ Decided |
| 010 | [To Be Determined] | [Decision 010](#decision-010-to-be-determined) | 🔄 Pending |
| 011 | Remove Pretty-Print Option - JSON-Only Output | [Decision 011](#decision-011-remove-pretty-print-option---json-only-output) | ✅ Decided |
| 012 | Docker Strategy with Separate Ollama Service | [Decision 012](#decision-012-docker-strategy-with-separate-ollama-service) | ✅ Decided |
| 013 | Pytest Test Suite with 80% Coverage Target | [Decision 013](#decision-013-pytest-test-suite-with-80%-coverage-target) | ✅ Decided |
| 014 | FastAPI with Open Access and Minimal Observability | [Decision 014](#decision-014-fastapi-with-open-access-and-minimal-observability) | ✅ Decided |
| 015 | Container Registry - GitHub Container Registry (GHCR) | [Decision 015](#decision-015-container-registry---github-container-registry-ghcr) | ✅ Decided |

## Decision Details

---

## Decision 001: Programming Language Selection

**Date:** 2026-02-14  
**Status:** ✅ Decided  
**Decision:** Use Python as the primary programming language

### Context
- Project requires AI/ML integration for OCR and text extraction
- Need rapid development within 6-day timeline
- Focus on rock-solid core features over ambitious scope
- Must integrate with modern AI services (OpenAI, Google Cloud Vision, or Azure)

### Options Considered

#### Option 1: Python ✅ SELECTED
**Pros:**
- Rich AI/ML ecosystem (OpenAI SDK, Google Cloud Vision, Azure CV)
- Excellent image processing libraries (Pillow, OpenCV)
- Strong text processing capabilities (difflib, fuzzywuzzy, regex)
- Rapid web development frameworks (FastAPI, Streamlit, Flask)
- Single language for entire stack possible (reduces context switching)
- Mature libraries for all required functionality

**Cons:**
- May require separate frontend if not using Streamlit
- Deployment may need more consideration than JS-based solutions

#### Option 2: Node.js/JavaScript
**Pros:**
- Single language for full-stack development
- Fast deployment to Vercel/Netlify
- Large ecosystem of web frameworks

**Cons:**
- AI/ML libraries less mature than Python
- OCR integration more complex
- Image processing libraries less robust
- Less natural fit for ML/AI workload

#### Option 3: .NET/C#
**Pros:**
- Aligns with TTB's current COLA system (.NET)
- Azure integration might be smoother

**Cons:**
- Slower development time
- Less mature AI/ML ecosystem
- Steeper learning curve for rapid prototyping
- Not ideal for 6-day timeline

### Decision Rationale

Python selected because:

1. **AI/ML Best Fit:** The core requirement is AI-powered text extraction. Python has the most mature, well-documented, and actively maintained libraries for:
   - OpenAI GPT-4 Vision API
   - Google Cloud Vision API
   - Azure Computer Vision API
   - Tesseract OCR

2. **Rich Ecosystem:** Python libraries handle all project requirements:
   - Image processing: Pillow, OpenCV
   - Text comparison: difflib (built-in), fuzzywuzzy
   - String validation: regex (built-in)
   - Web frameworks: FastAPI, Streamlit, Flask

3. **Rapid Development:** With 6 days for implementation:
   - Python's concise syntax enables faster development
   - Frameworks like Streamlit can create full UI in hours, not days
   - Less boilerplate code than compiled languages

4. **Industry Standard:** Most modern AI/ML work and research happens in Python
   - Better documentation and community support
   - More examples and tutorials for similar use cases
   - Easier to find solutions to implementation challenges

5. **Focus on Business Logic:** Python allows spending more time on:
   - Label verification algorithms
   - Comparison logic for field matching
   - Government warning validation
   - Less time on language/framework mechanics

### Implications

- **Framework Selection:** Next decision will be Python web framework (Streamlit vs FastAPI vs Flask)
- **Deployment:** Will need Python-friendly hosting (Railway, Render, Heroku, Streamlit Cloud, PythonAnywhere)
- **Dependencies:** Will use pip/poetry for dependency management
- **Testing:** Will use pytest for unit tests
- **Code Quality:** Will use black/ruff for formatting, mypy for type checking

### Success Metrics
- Successfully integrate with chosen AI service (OpenAI/Google/Azure)
- Process label images and extract text in < 5 seconds
- Clean, maintainable Python codebase
- Straightforward deployment process

### References
- OpenAI Python SDK: https://github.com/openai/openai-python
- Pillow Documentation: https://pillow.readthedocs.io/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Streamlit Documentation: https://docs.streamlit.io/

---

## Decision 002: Web Framework Selection

**Date:** 2026-02-14  
**Status:** ✅ Decided  
**Decision:** Use FastAPI as the web framework

### Context
- Need API backend for label verification service
- Must support file uploads (images)
- Need to expose endpoints for frontend consumption
- Should be production-ready and well-documented
- Must support async operations for AI/OCR calls

### Options Considered

#### Option 1: Streamlit
**Pros:**
- Fastest development time (single Python file)
- Built-in UI components (file upload, forms, display)
- Perfect for internal tools
- Instant deployment to Streamlit Cloud

**Cons:**
- Less separation of concerns
- Limited API flexibility
- Not ideal for Lambda deployment
- Less "production-like" architecture

#### Option 2: FastAPI ✅ SELECTED
**Pros:**
- Modern, fast, production-ready
- Automatic API documentation (OpenAPI/Swagger)
- Native async/await support for AI API calls
- Type hints and validation built-in (Pydantic)
- Easy to deploy to AWS Lambda (with Mangum adapter)
- Clean separation of API and frontend
- Excellent for RESTful API design

**Cons:**
- Requires separate frontend implementation
- More initial setup than Streamlit

#### Option 3: Flask
**Pros:**
- Mature, well-known framework
- Large ecosystem and community

**Cons:**
- Less modern than FastAPI
- No native async support (need Flask-Async)
- More boilerplate code
- Manual API documentation

### Decision Rationale

FastAPI selected because:

1. **AWS Lambda Compatible:** Works well with Lambda via Mangum adapter
2. **Async Support:** Native async/await perfect for AI API calls that may take seconds
3. **Production Quality:** Automatic validation, serialization, and API docs
4. **Type Safety:** Pydantic models reduce bugs and improve maintainability
5. **Performance:** Built on Starlette and Uvicorn (fast ASGI server)
6. **Developer Experience:** Automatic interactive API docs at /docs endpoint

### Implications
- Need to build separate frontend (React/Vue/vanilla JS)
- API-first architecture with clear endpoints
- Can test API independently of frontend
- Documentation generated automatically
- Easy to add authentication later if needed

### Success Metrics
- API responds in < 5 seconds per label verification
- Clean API contract with proper request/response models
- Automatic API documentation available
- Successful deployment to AWS Lambda

### References
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Mangum (Lambda adapter): https://mangum.io/

---

## Decision 003: AI/OCR Service Selection

**Date:** 2026-02-14  
**Status:** ✅ Decided  
**Decision:** Use Ollama with vision-capable model (llama3.2-vision or llava)

### Context
From interview with Marcus Williams (IT Systems Administrator):
> "Our network blocks outbound traffic to a lot of domains... During the scanning vendor pilot, half their features didn't work because our firewall blocked connections to their ML endpoints."

**Key Requirements:**
- No external API dependencies that could be blocked by government firewalls
- Must work in isolated network environment
- < 5 second processing time (critical requirement)
- Must extract text from label images accurately
- Must handle structured data extraction (brand name, ABV, warnings, etc.)

### Options Considered

#### Option 1: Cloud APIs (OpenAI GPT-4 Vision, Google Cloud Vision, Azure)
**Pros:**
- State-of-the-art accuracy
- Fast processing (typically 1-3 seconds)
- Minimal setup and maintenance
- Strong structured data extraction

**Cons:**
- ❌ Requires external API calls (blocked by TTB firewall per Marcus)
- ❌ Won't work in production environment
- Ongoing API costs
- Network dependency

#### Option 2: Ollama + Vision Model ✅ SELECTED (with concerns)
**Pros:**
- ✅ Fully self-contained, runs locally
- ✅ No external dependencies or API calls
- ✅ Works in isolated network
- Supports vision-capable models (llama3.2-vision, llava, etc.)
- Free to run

**Cons:**
- ⚠️ **CRITICAL: Performance concern** - May not meet 5-second requirement
- ⚠️ **Lambda incompatible** - Models are too large (GBs) for Lambda
- Requires significant compute resources
- Accuracy may be lower than GPT-4 Vision
- Setup complexity for deployment

#### Option 3: Tesseract OCR + GPT-based text parsing
**Pros:**
- Tesseract is self-contained and lightweight
- Fast OCR processing (< 1 second)
- Lambda-compatible
- Could use smaller Ollama model for text structuring

**Cons:**
- Two-stage process (OCR then parsing)
- Tesseract accuracy varies with image quality
- More complex pipeline

#### Option 4: Hybrid Approach (Tesseract + Rule-based extraction)
**Pros:**
- ✅ Fast (< 1 second for OCR)
- ✅ Fully self-contained
- ✅ Lambda-compatible
- ✅ Predictable performance
- No AI model hosting needed

**Cons:**
- Less intelligent text extraction
- Requires manual parsing logic
- May miss edge cases
- Less impressive technically

### Decision Rationale

**Selected Ollama with EC2 deployment:**

1. **Meets Core Requirement:** Self-contained, no external APIs blocked by firewall
2. **Vision Capabilities:** Can process images and extract structured data
3. **Realistic for TTB:** Mirrors on-premise deployment scenario
4. **No Ongoing Costs:** Free to run (unlike cloud APIs)
5. **Prototype Appropriate:** Demonstrates AI capability in constrained environment

**Resolution of Lambda Conflict:**
- Moved to EC2 deployment (see Decision 004)
- EC2 can handle 4-8GB Ollama models
- Allows persistent model loading (no cold starts)

**Ollama Model Selection:**
- **Primary:** llama3.2-vision (11B parameters, vision + text)
- **Alternative:** llava (smaller, faster if performance issues)
- Will benchmark both on EC2 to meet 5-second requirement

### Performance Strategy

**Meeting the 5-Second Requirement:**
1. Pre-load model at container startup (not per request)
2. Keep Ollama service warm
3. Optimize prompts for structured output
4. Use appropriate instance size (t3.xlarge minimum)
5. Consider GPU instance (g4dn.xlarge) if CPU inference too slow

**Fallback Plan:**
If Ollama cannot meet 5-second requirement:
- Switch to Tesseract OCR + rule-based extraction
- Document in README that this was a performance-driven decision
- Note that production deployment could use specialized OCR hardware

### Implications

**Technical:**
- FastAPI will call Ollama API at http://localhost:11434
- Use ollama Python library for integration
- Design prompts for JSON-structured output extraction
- Handle Ollama errors gracefully

**Deployment:**
- Docker Compose with two services: ollama + api
- Model downloaded during container build or first run
- Persistent volume for model storage

**Development:**
- Can develop locally with Ollama installed
- Use same Docker Compose for local testing
- Mock Ollama responses for fast iteration if needed

### Success Metrics
- Image processing completes in < 5 seconds
- Accurate text extraction (>90% accuracy on clear labels)
- Works without external API calls
- Deployable to chosen AWS service

### References
- Ollama: https://ollama.ai/
- Ollama Python SDK: https://github.com/ollama/ollama-python
- Tesseract OCR: https://github.com/tesseract-ocr/tesseract
- AWS Lambda Limits: https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html

---

## Decision 004: Deployment Platform

**Date:** 2026-02-14  
**Status:** ✅ Decided  
**Decision:** AWS EC2 deployment (dropping Lambda approach)

### Context
- AWS is the chosen cloud provider
- Lambda was initial consideration
- Choice depends on AI/OCR service selection

### Options Considered

#### Option 1: AWS Lambda + API Gateway
**Pros:**
- Serverless, auto-scaling
- Pay per request
- Easy to deploy with SAM/CDK
- No server management

**Cons:**
- ❌ Incompatible with Ollama (model size limits)
- 15-minute timeout limit
- Cold start latency
- 10GB storage limit

#### Option 2: AWS EC2 (t3.xlarge or larger)
**Pros:**
- ✅ Can run Ollama with vision models
- Full control over environment
- Persistent storage
- Can use GPU instances if needed

**Cons:**
- More expensive (running 24/7)
- Manual scaling
- More deployment complexity

#### Option 3: AWS ECS Fargate
**Pros:**
- Container-based deployment
- Better scaling than EC2
- No server management
- Can run Ollama in container

**Cons:**
- More expensive than Lambda
- Requires container registry setup
- More complex than Lambda

#### Option 4: AWS App Runner
**Pros:**
- Easy container deployment
- Auto-scaling
- Built-in load balancing

**Cons:**
- Limited to 4 vCPU / 12GB RAM
- May not be sufficient for Ollama

### Decision Rationale

**EC2 selected to support self-contained Ollama deployment:**

1. **Enables Ollama:** EC2 can handle 4-8GB vision models that Lambda cannot
2. **Self-Contained Requirement:** Meets TTB's firewall constraints (no external APIs)
3. **Performance Control:** Can select instance type to meet 5-second requirement
4. **Flexibility:** Can add GPU if needed for faster inference
5. **Prototype Realistic:** Mirrors how TTB would actually deploy (on-premise or gov cloud)

**Trade-offs Accepted:**
- More complex deployment than Lambda
- Higher baseline cost (running instance vs. pay-per-request)
- Manual scaling (but acceptable for prototype)
- Requires instance management

**Deployment Plan:**
- Use EC2 instance (t3.xlarge or larger based on performance testing)
- Docker container with FastAPI + Ollama
- nginx reverse proxy for production serving
- Elastic IP for stable endpoint
- Security group for port 80/443 only

### Implementation Details

**Instance Selection:**
- Start with t3.xlarge (4 vCPU, 16GB RAM)
- Monitor Ollama performance with vision model
- Scale up if needed (t3.2xlarge or g4dn for GPU)

**Docker Setup:**
```yaml
# docker-compose.yml structure
services:
  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
  
  api:
    build: ./backend
    depends_on:
      - ollama
    environment:
      - OLLAMA_HOST=ollama:11434
```

**Frontend Hosting:**
- Option A: Serve static frontend from same EC2 (nginx)
- Option B: Host frontend on S3 + CloudFront (recommended for separation)

### Next Steps
1. Set up EC2 instance with Docker
2. Install and test Ollama with llama3.2-vision or llava
3. Benchmark performance with sample label images
4. Optimize instance size if needed
5. Document deployment process

---

## Decision 005: Sample Label Generator Approach

**Date:** 2026-02-14  
**Status:** ✅ Decided  
**Decision:** Build a Python script (`gen_samples.py`) to generate realistic synthetic alcohol beverage labels for testing

### Context
- Need test data to validate the label verification system
- Can't use real TTB COLA data (privacy, permissions)
- Need both GOOD (compliant) and BAD (non-compliant) labels
- Labels must reflect actual 27 CFR regulatory requirements
- Need ground truth data (JSON metadata) for validation testing

### Options Considered

#### Option 1: Use Real Labels from TTB Public COLA Registry
**Pros:**
- Authentic real-world labels
- Already approved/verified by TTB
- No generation needed

**Cons:**
- Can't create BAD examples (all are approved)
- No ground truth metadata
- May have copyright/usage restrictions
- Limited control over test scenarios
- Can't test specific violation types

#### Option 2: Manually Create Labels in Design Software
**Pros:**
- Full creative control
- Can create specific test cases
- Professional appearance

**Cons:**
- Time-consuming (would take days for 100+ labels)
- Not scalable
- Hard to ensure regulatory accuracy
- Manual metadata creation error-prone

#### Option 3: Generate Synthetic Labels with Python Script ✅ SELECTED
**Pros:**
- Scalable - generate hundreds of labels quickly
- Fully automated with command-line control
- Can create specific violation types systematically
- Generates ground truth metadata automatically
- Ensures regulatory accuracy (based on CFR analysis)
- Randomization creates realistic variety
- Reproducible test data

**Cons:**
- Initial development time (~6-7 hours)
- May not look as polished as manual design
- Limited to programmatic design elements

### Decision Rationale

**Selected synthetic generation approach because:**

1. **Testing Requirements:** Need systematic test coverage of both compliant and non-compliant cases
   - GOOD labels test baseline functionality
   - BAD labels test specific violation detection (15+ types)
   - Need many examples to test robustness

2. **Ground Truth Essential:** For validation testing, need to know:
   - What text SHOULD be extracted from each label
   - Which regulations each label violates
   - Expected validation outcome (COMPLIANT/NON_COMPLIANT)
   - Manual labels would require manual metadata creation (error-prone)

3. **Scalability:** Command-line generation allows:
   - Quick iteration: regenerate all samples if requirements change
   - Large test sets: easily create 100+ labels
   - Specific scenarios: target specific violation types
   - Batch processing testing: generate many labels at once

4. **Regulatory Accuracy:** Script enforces requirements from TTB_REGULATORY_SUMMARY.md:
   - Type size calculations based on container size
   - Exact government warning text
   - Proper format requirements (bold, all caps, etc.)
   - Product-specific requirements (spirits vs wine vs malt)

5. **Development Time Acceptable:** ~6-7 hours to build generator is worthwhile because:
   - Saves days of manual label creation
   - Enables unlimited regeneration
   - Provides foundation for future test expansion

### Implementation Details

**Architecture:**
- Single Python file: `gen_samples.py`
- Minimal dependencies: Pillow + standard library
- Component-based design:
  - `FieldRandomizer` - generate valid field values
  - `Label` - data structure
  - `ViolationGenerator` - apply specific violations
  - `LabelRenderer` - draw label to image (PIL)
  - `LabelGenerator` - orchestrate + CLI

**Design Philosophy: Keep it simple!**
- Randomize all parameters within regulatory bounds
- Realistic but not overly complex designs
- Standard canvas sizes based on actual bottle labels
- No intentional image degradation (labels are exports from design software, not photos)

**Command Line Interface:**
```bash
python scripts/gen_samples.py --good 50 --bad 50
python scripts/gen_samples.py --good 100 --bad 0
python scripts/gen_samples.py --seed 42  # optional reproducibility
```

**Output per Label:**
- `label_good_001.jpg` - JPEG image (< 750 KB per TTB requirement)
- `label_good_001.tif` - TIFF image (< 750 KB)
- `label_good_001.json` - Metadata with ground truth

**Violation Types Supported:**
- Missing required fields (warning, brand, ABV, net contents, etc.)
- Warning format violations (not all caps, body bold, wrong text)
- Value mismatches (ABV outside tolerance, wrong net contents)
- Format violations (type size too small, missing import phrase)
- Mix of single and multiple violations per label

### Implications

**For Development:**
- Separate work stream for sample generator
- Develop before main verification system
- Can test generator output manually before integration

**For Testing:**
- Comprehensive test coverage of regulations
- Ground truth enables automated validation testing
- Can regenerate samples if requirements change
- Supports batch processing testing

**For Documentation:**
- `SAMPLE_GENERATOR.md` provides complete specification
- Implementation plan with 8 phases (~6-7 hours)
- Clear testing strategy and success criteria

**For Future:**
- Can extend with more violation types
- Can add image quality variations if needed
- Foundation for continuous test data generation

### Success Metrics

**Generator Functionality:**
- [✅] Script runs without errors
- [✅] Generates specified number of GOOD and BAD labels
- [✅] All output files created (JPEG, TIFF, JSON)
- [✅] All files < 750 KB

**Label Quality:**
- [✅] GOOD labels comply with all 27 CFR requirements
- [✅] BAD labels have documented violations
- [✅] Labels are visually realistic
- [✅] Text is readable (proper contrast and size)
- [✅] Type sizes meet regulatory minimums (GOOD labels)

**Testing Support:**
- [ ] GOOD labels validate as COMPLIANT in main system (pending main system build)
- [ ] BAD labels validate as NON_COMPLIANT with correct violations (pending main system build)
- [✅] Ground truth metadata is accurate and complete
- [✅] Can generate 100+ labels in reasonable time

### References
- `SAMPLE_GENERATOR.md` - Complete technical specification
- `TTB_REGULATORY_SUMMARY.md` - Regulatory requirements
- 27 CFR XML files in `cfr_regulations/` directory

---

## Decision 006: Deterministic Generation vs AI Image Generation

**Date:** 2026-02-15  
**Status:** ✅ Decided  
**Decision:** Use deterministic programmatic generation (PIL/Pillow) rather than AI image generation tools for creating sample labels

### Context
- External documentation suggested: "AI image generation tools work well for this"
- Need to choose between AI-generated images vs programmatic rendering
- Must have accurate ground truth for validation testing
- Need control over specific regulatory violations
- Want to generate labels that look realistic but are deterministic

### Options Considered

#### Option 1: AI Image Generation (DALL-E, Midjourney, Stable Diffusion)
**Pros:**
- More realistic/varied visual designs
- Can generate diverse artistic styles
- Less programming complexity
- Potentially more professional appearance
- Follows suggestion in external docs

**Cons:**
- ❌ **No control over text accuracy** - AI might misspell, alter text
- ❌ **Ground truth uncertain** - would need OCR to extract what AI actually wrote
- ❌ **Violation generation challenging** - hard to prompt for specific violations
- ❌ **Expensive/slow** - API costs and generation time per image
- ❌ **Inconsistent** - AI might not follow regulatory requirements exactly
- ❌ **Two-step process** - Generate image, then OCR it to get ground truth
- No guarantee of regulatory accuracy

#### Option 2: Programmatic Generation with PIL/Pillow ✅ SELECTED
**Pros:**
- ✅ **Complete control** over every element
- ✅ **Guaranteed regulatory accuracy** - we render exactly what we specify
- ✅ **Known ground truth** - we know precisely what text is on each label
- ✅ **Deterministic output** - same parameters = same result
- ✅ **Fast generation** - seconds per label, no API calls
- ✅ **No API costs** - free after Pillow installation
- ✅ **Violation control** - can create specific regulatory violations systematically
- ✅ **Works offline** - no network dependency

**Cons:**
- Labels may look somewhat "synthetic" or template-like
- Limited visual variety in design styles
- Requires careful PIL/Pillow programming
- Less impressive visually than AI-generated images

#### Option 3: Hybrid Approach
**Pros:**
- Use programmatic for guaranteed accuracy
- Use AI for additional visual variety
- Best of both worlds

**Cons:**
- More complex implementation
- Two different generation pipelines
- Still have ground truth issues with AI-generated labels

### Decision Rationale

**Selected programmatic generation (Option 2) because:**

1. **Ideal vs. Practical Reality:**
   - **In a perfect world**, we would use REAL label images that had been validated by human experts in the 27 CFR regulations
   - Real labels validated by TTB experts would provide:
     - Authentic visual complexity
     - Real-world edge cases and variations
     - Confidence in regulatory compliance
     - No risk of programmatic errors in interpretation
   - **However, this is not possible for this POC** because:
     - We don't have access to a corpus of pre-validated labels with ground truth
     - Getting expert validation would take weeks/months (outside POC timeline)
     - Real TTB COLA database only has approved labels (can't get BAD examples)
     - Building such a dataset is beyond the scope of a 6-day prototype
   - **Therefore**, deterministic generation was the pragmatic choice given constraints

2. **Ground Truth is Critical:** For testing the verification system, we MUST know exactly what text should be extracted
2. **Ground Truth is Critical (Continued):** For testing the verification system, we MUST know exactly what text should be extracted
   - With AI generation: AI might write "Goverment Warning" or "45.2% ABV" when we wanted "45.0% ABV"
   - With programmatic: We render exactly "GOVERNMENT WARNING:" and "45.0% ABV"
   - Ground truth is essential for automated validation testing

3. **Violation Control:** Need to systematically test specific violations
   - Must create labels with "warning not all caps" violation
   - Must create labels with "ABV outside tolerance" violation
   - Very difficult to prompt AI to generate these specific regulatory violations
   - Programmatic generation: simply set `warning_header_all_caps = False`

4. **Regulatory Accuracy:** Labels must follow precise 27 CFR requirements
   - Type sizes must be exactly 1mm, 2mm, or 3mm based on container size
   - Warning text must be word-for-word exact
   - AI models aren't trained on TTB regulations
   - Programmatic: we implement exact requirements from CFR

5. **Human Expertise Requirements:** Deterministic methods were necessary for sample generation so that we could KNOW with some degree of certainty that we were generating definitively GOOD or BAD samples
   - With AI-generated samples, a human well-versed in the regulations would have to either:
     a) Train the AI to reliably generate GOOD and BAD samples (requires extensive prompt engineering and validation), OR
     b) Manually sort images created by an AI-based sample generator into GOOD and BAD categories
   - Given the time constraints, it seemed unlikely for the human operator to become conversant enough in the 27 CFR regulations (spanning 1,400+ pages) to make accurate compliance determinations
   - The regulations contain subtle requirements (e.g., "GOVERNMENT WARNING:" must be bold but body text must not be bold, ABV tolerances vary by product type) that are difficult for humans to quickly master
   - Programmatic generation embeds regulatory knowledge directly in code, removing human judgment from the classification process

6. **Speed & Scale:** Can generate 100+ labels in minutes
   - Programmatic: ~2 seconds per label, no API latency
   - AI generation: 10-30 seconds per label + API costs
   - For testing, need ability to regenerate entire test set quickly

7. **Deterministic Testing:** Same seed = same labels
   - Critical for reproducible test results
   - Debugging: can regenerate exact same problematic label
   - AI generation is inherently non-deterministic

8. **Cost & Availability:**
   - Programmatic: Free after Pillow installation
   - AI APIs: $0.02-$0.20+ per image, adds up for 100+ labels
   - No API keys or accounts needed

### Implementation Approach

**Programmatic rendering with PIL/Pillow:**
- Use `ImageDraw` to create canvas and draw text
- Calculate type sizes: `mm * 300 DPI / 25.4 ≈ mm * 11.8 pixels`
- Load system fonts with fallback to default
- Render text with bold/regular weights
- Add decorative elements (borders, lines, corners)
- Ensure contrast (light backgrounds, dark text)

**Visual Quality Improvements:**
- Randomize background colors from palette
- Randomize layout positions slightly
- Add decorative elements (borders, corner ornaments)
- Vary font sizes within regulatory bounds
- Different canvas sizes for different container sizes

**Result:** Labels look "designed" rather than "photographed" - appropriate for the use case (labels are design exports, not photos of bottles)

### Implications

**For Testing:**
- 100% accurate ground truth for validation
- Can test specific violation types systematically
- Reproducible test sets with seeds
- Fast iteration when requirements change

**For Development:**
- More initial programming (vs AI prompting)
- Need to handle font loading, text rendering
- But: Complete control over output

**For Future:**
- Could add AI generation as supplementary tool later
- Could use AI for additional visual variety
- Foundation is solid programmatic generation with known ground truth

### Success Metrics

- [✅] Generated 40 labels (20 GOOD + 20 BAD) successfully
- [✅] All files < 750 KB
- [✅] Ground truth JSON matches rendered images exactly
- [✅] Specific violations render correctly (warning not caps, missing fields, etc.)
- [✅] Labels are visually acceptable (readable, contrasting, organized)
- [✅] Generation speed: ~2 seconds per label

### References
- PIL/Pillow Documentation: https://pillow.readthedocs.io/
- `gen_samples.py` - Implementation (~1,100 lines)
- `SAMPLE_GENERATOR.md` - Technical specification

---

## Decision 007: Sample Label Output Format — JPEG + TIFF

**Date:** 2026-02-16 (revised 2026-02-20)
**Status:** ✅ Revised  
**Decision:** Generate both JPEG and TIFF files for sample labels; accept both JPEG and TIFF for label uploads

### Context
- TTB COLA submission requirements specify "JPEG or TIFF, < 750 KB"
- Initial implementation generated both JPEG and TIFF per label
- An intermediate revision briefly considered JPEG-only to simplify file management
- However, the verification API must accept both formats to match real TTB workflow (applicants may submit either)

### Final Decision

**Accept both JPEG and TIFF** for label uploads throughout the system:
- `POST /verify`, `POST /verify/async`: accept `.jpg`, `.jpeg`, `.tif`, `.tiff`
- Sample generator: produces both `.jpg` and `.tif` per label for comprehensive testing
- Batch ZIP files: may contain either format

### Rationale

1. **TTB Compliance:** Real COLA submissions are JPEG or TIFF — the verifier must handle both
2. **Test Coverage:** Generating both formats from `gen_samples.py` exercises both upload paths
3. **No PNG:** PNG is not an accepted TTB COLA format and is explicitly rejected by the API

### Implementation

```python
# api.py — accepted MIME types and extensions
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/tiff"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff"}
```

### Success Metrics

- [✅] API accepts JPEG and TIFF uploads; rejects PNG and other formats
- [✅] Sample generator produces both `.jpg` and `.tif` per label
- [✅] All files < 750 KB

### References
- TTB COLA Requirements: JPEG or TIFF, < 750 KB
- `app/api.py` — `validate_upload_file()` function

---

## Decision 008: CLI-First Development Approach

**Date:** 2026-02-16  
**Status:** ✅ Decided  
**Decision:** Build verification engine as command-line tool first, wrap with FastAPI later

### Context
- Need to build label verification system with OCR + validation logic
- Could start with web app (FastAPI + frontend) or CLI tool
- Want to focus on core verification logic without UI distractions
- Need rapid iteration and testing capability

### Options Considered

#### Option 1: FastAPI Web App First
**Pros:**
- Matches final deliverable format
- User-friendly interface from start
- Demo-ready immediately

**Cons:**
- Frontend/backend coordination overhead
- Slower iteration on core logic
- Harder to test and debug
- UI concerns distract from verification accuracy

#### Option 2: CLI Tool First ✅ SELECTED
**Pros:**
- Focus purely on verification logic
- Fast iteration and testing (just run command)
- Easy to test against 40-label golden dataset
- Clean separation: build core, then wrap in API
- Follows Unix philosophy: do one thing well
- Same JSON output works for both CLI and API

**Cons:**
- Requires second step to add web interface
- Less immediately impressive for demos

### Decision Rationale

**Selected CLI-first approach because:**

1. **Focus on Core Logic:** Verification accuracy is the critical requirement
   - Build OCR extraction properly
   - Get validation logic correct
   - Meet 5-second performance requirement
   - No UI distractions

2. **Rapid Testing:** With golden dataset ready:
   ```bash
   # Test immediately
   python verify_label.py samples/label_good_001.jpg
   
   # Batch test all 40 labels
   ./test_all_samples.sh
   ```
   - Instant feedback on accuracy
   - Easy to iterate on validation rules
   - No need to click through web forms

3. **Clean Architecture:**
   ```
   CLI (verify_label.py)
     ↓
   Core Logic (label_validator.py) ← Returns JSON
     ↓
   FastAPI (app.py) ← Wraps same function
   ```
   - Single source of truth for verification
   - No duplication between CLI and API
   - Test core once, both interfaces work

4. **JSON Output is Universal:**
   - CLI returns JSON to stdout
   - FastAPI returns same JSON as HTTP response
   - Consistent results regardless of interface
   - Easy to test programmatically

5. **Matches Development Workflow:**
   - Build verifier (this phase)
   - Test thoroughly with CLI
   - Wrap in FastAPI (next phase)
   - Add frontend (final phase)

### Implementation Details

**CLI Interface:**
```bash
# Basic usage - returns JSON to stdout
python verify_label.py samples/label_good_001.jpg

# With ground truth for full validation
python verify_label.py label.jpg --ground-truth application.json

# Batch mode
python verify_label.py samples/*.jpg

# Choose OCR backend
python verify_label.py label.jpg --ocr ollama  # default
python verify_label.py label.jpg --ocr tesseract  # fallback
```

**Output Format (JSON only):**
```json
{
  "status": "COMPLIANT",
  "validation_level": "full",
  "extracted_fields": { ... },
  "validation_results": { ... },
  "violations": [],
  "processing_time_seconds": 2.3
}
```

**Future FastAPI Integration:**
```python
@app.post("/verify")
async def verify_label(image: UploadFile, ...):
    # Call same core function
    result = verify_label_file(image_path, expected_fields)
    return result  # Same JSON
```

### Implications

**For Development:**
- Start with `ocr_backends.py`, `label_extractor.py`, `label_validator.py`
- CLI is thin wrapper: parse args, call validator, print JSON
- Can test immediately against golden dataset
- Iterate quickly without web server overhead

**For Testing:**
- Simple bash script tests all 40 labels
- Easy to measure accuracy (20 GOOD should pass, 20 BAD should fail)
- Performance testing: just time the command
- No browser/HTTP testing needed yet

**For FastAPI Migration:**
- Core logic already returns JSON
- FastAPI just wraps: accept upload, call function, return JSON
- No rewrite needed - literally import and call
- Can build frontend against CLI JSON structure first

### Success Metrics

- [✅] CLI tool accepts image path and returns JSON
- [✅] Ollama installed with llama3.2-vision model
- [ ] Verifier correctly identifies 20 GOOD labels as compliant
- [ ] Verifier correctly identifies 20 BAD labels as non-compliant  
- [ ] Processing time < 5 seconds per label
- [ ] JSON output structure documented

### References
- Unix Philosophy: https://en.wikipedia.org/wiki/Unix_philosophy
- Golden dataset: `samples/` directory (40 labels with ground truth)

---

## Decision 009: Graceful Degradation Validation Strategy

**Date:** 2026-02-16  
**Status:** ✅ Decided  
**Decision:** Support two-tier validation: structural checks (always) + accuracy checks (optional, requires ground truth)

### Context
- Real TTB workflow: verify label matches COLA application data
- Need to compare extracted text against claimed values
- Users may not always have complete application data
- Should provide useful feedback even with partial information

### Problem Statement

**Core Question:** Can we validate a label from the image alone, or do we need application data?

**Answer:** Depends on what we're validating:
- **Structural compliance** (required fields present, warning formatted correctly) - YES, image only
- **Accuracy verification** (does brand match claim, is ABV correct) - NO, need ground truth

### Options Considered

#### Option 1: Require Ground Truth (Strict)
**Pros:**
- Complete validation always
- Matches TTB workflow exactly
- No ambiguous results

**Cons:**
- Can't validate without application data
- Not useful for quick structural checks
- Rigid - all or nothing

#### Option 2: Image-Only Validation (Lenient)
**Pros:**
- Always works regardless of input
- Fast structural checks
- No external data needed

**Cons:**
- Can't verify accuracy (main use case)
- Misleading - might say "compliant" when fields are wrong
- Doesn't match real TTB workflow

#### Option 3: Graceful Degradation ✅ SELECTED
**Pros:**
- Works with any amount of ground truth (none, partial, full)
- Transparent about what was/wasn't validated
- Useful in all scenarios
- Guides users to provide more data
- Mirrors real-world flexibility

**Cons:**
- More complex output (three states: pass/fail/unknown)
- Need to track what was checked vs skipped

### Decision Rationale

**Selected graceful degradation because:**

1. **Matches Real-World Usage:**
   - Sometimes user has full application data
   - Sometimes only partial (just brand and ABV)
   - Sometimes none (quick structural check)
   - System should be useful in all cases

2. **Two-Tier Validation System:**

   **Tier 1: Structural (Always Performed)**
   - Government warning present? ✅
   - "GOVERNMENT WARNING:" in all caps? ✅
   - Warning text matches exact wording? ✅
   - Brand name present? ✅
   - ABV present? ✅
   - Net contents present? ✅
   - Bottler info present? ✅
   
   **Tier 2: Accuracy (Requires Ground Truth)**
   - Brand matches application? (need expected brand)
   - ABV matches within tolerance? (need expected ABV)
   - Net contents matches? (need expected net contents)
   - Bottler info matches? (need expected bottler)
   - Country of origin matches? (need expected country)

3. **Transparent Communication:**
   ```json
   {
     "status": "PARTIAL_COMPLIANCE",
     "validation_level": "structural_only",
     "structural_checks": { "passed": 8, "failed": 0 },
     "accuracy_checks": { "skipped": 6, "reason": "no_ground_truth" },
     "warnings": [
       "Cannot verify field accuracy without application data"
     ]
   }
   ```

4. **Guides Users:**
   - When ground truth missing: "Provide application data for complete validation"
   - Shows what was checked vs what wasn't
   - User understands limitations

5. **Flexible Workflow:**
   ```bash
   # Quick structural check
   python verify_label.py label.jpg
   # → "Structure OK, but can't verify accuracy"
   
   # Full validation
   python verify_label.py label.jpg --ground-truth app.json
   # → "COMPLIANT - all fields match"
   
   # Partial validation
   python verify_label.py label.jpg --brand "X" --abv "13.5%"
   # → "Brand matches, ABV matches, other fields not verified"
   ```

### Implementation Details

**Validation Function Signature:**
```python
def verify_label_file(
    image_path: str,
    expected_fields: Optional[Dict[str, str]] = None,
    ocr_backend: str = "ollama"
) -> Dict[str, Any]:
    """
    Verify label compliance.
    
    Args:
        image_path: Path to label image
        expected_fields: Optional dict with expected values
            {
                'brand_name': 'Stone\'s Throw',
                'alcohol_content': '13.5% alc./vol.',
                'net_contents': '750 mL',
                # ... any subset of fields
            }
        ocr_backend: 'ollama' or 'tesseract'
    
    Returns:
        {
            'status': 'COMPLIANT' | 'NON_COMPLIANT' | 'PARTIAL_COMPLIANCE',
            'validation_level': 'full' | 'partial' | 'structural_only',
            'extracted_fields': {...},
            'validation_results': {
                'structural': {'passed': N, 'failed': M, 'checks': [...]},
                'accuracy': {'passed': X, 'failed': Y, 'skipped': Z, 'checks': [...]}
            },
            'violations': [...],
            'warnings': [...]
        }
    """
```

**Three Validation Levels:**
1. **full** - All expected fields provided, complete validation
2. **partial** - Some expected fields provided, validate what we can
3. **structural_only** - No expected fields, only check structure

**Status Determination:**
- `COMPLIANT` - All checks passed (structural + accuracy where applicable)
- `NON_COMPLIANT` - Any checks failed (violations found)
- `PARTIAL_COMPLIANCE` - All performed checks passed, but some skipped

### Implications

**For CLI:**
```bash
# No ground truth
python verify_label.py label.jpg
# Returns: status=PARTIAL_COMPLIANCE, warnings about missing data

# Full ground truth
python verify_label.py label.jpg --ground-truth app.json
# Returns: status=COMPLIANT or NON_COMPLIANT

# Partial ground truth
python verify_label.py label.jpg --brand "X" --abv "13.5%"
# Returns: status varies, shows which checks ran
```

**For FastAPI (Future):**
```html
<form>
  <input type="file" name="label" required>
  
  <!-- Optional fields with warning -->
  <p class="warning">
    💡 Providing application data enables full validation.
    Without it, we can only check structural compliance.
  </p>
  
  <input name="brand_name" placeholder="Brand Name (optional)">
  <input name="alcohol_content" placeholder="ABV (optional)">
  <!-- ... -->
</form>
```

**For Users:**
- Always get useful feedback
- Understand what was/wasn't validated
- Encouraged to provide complete data
- No binary "works/doesn't work" frustration

### Success Metrics

- [ ] Structural validation works without ground truth
- [ ] Accuracy validation works with ground truth
- [ ] Partial ground truth correctly skips missing fields
- [ ] Output clearly indicates validation level
- [ ] Warnings guide users to provide more data

### References
- Graceful degradation pattern: https://en.wikipedia.org/wiki/Graceful_degradation
- TTB workflow: REQUIREMENTS.md

---

## Decision 010: OCR Backend Strategy — Ollama-Only

**Date:** 2026-02-16 (revised 2026-02-20)
**Status:** ✅ Revised  
**Decision:** Use Ollama (llama3.2-vision) as the sole OCR backend; Tesseract was evaluated and rejected due to unacceptable accuracy

**Revision note:** An earlier draft of this decision proposed a hybrid approach (Tesseract default, Ollama optional). After further implementation and evaluation the hybrid was abandoned: Tesseract accuracy (~60-70%) was judged insufficient for regulatory compliance checking, and the async queue architecture (see deployment) makes the Ollama latency acceptable. The system now uses Ollama exclusively.

### Context

During implementation, discovered a **fundamental tension** between two critical requirements:

1. **5-Second Performance Requirement:**
   - Sarah Chen (Deputy Director): *"If we can't get results back in about 5 seconds, nobody's going to use it. We learned that the hard way."*
   - Based on failed vendor pilot (30-40 second processing times)
   - Stated as critical dealbreaker

2. **AI-Powered Verification:**
   - Project title: "AI-Powered Alcohol Label Verification App"
   - Marcus Williams mentioned previous vendor's "ML endpoints"
   - Implies use of modern AI/ML technology

3. **Local Execution Constraint:**
   - Marcus Williams: *"our network blocks outbound traffic... firewall blocked connections to their ML endpoints"*
   - Must run completely locally (no cloud APIs)

**These requirements are in direct conflict** with available technology.

### The Testing Results

Evaluated three OCR approaches on our golden dataset:

#### Option 1: Tesseract OCR (Traditional Computer Vision)
**Test Results:**
- **Speed:** ✅ ~1 second per label (meets 5-second requirement)
- **Accuracy:** ⚠️ Problematic
  - Missing brand names (decorative fonts)
  - Text corruption: "Black Brewing" → "Black ibealtl se"
  - OCR errors: "ability" → "epulty"
  - Overall: ~60-70% field accuracy estimate
- **Technology:** Traditional pattern-matching OCR (not AI)
- **Local:** ✅ Yes

**Example output:**
```
Hefeweizen
7.5% ABV
Imported by Black ibealtl se Francisco, CA  ← OCR ERROR
```

#### Option 2: Ollama llama3.2-vision (AI Vision Model)
**Test Results:**
- **Speed:** ❌ ~58 seconds per label (exceeds 5-second requirement by 12x)
- **Accuracy:** ✅ Excellent
  - Correctly extracted all fields including decorative fonts
  - Handled markdown formatting well
  - Overall: ~95%+ field accuracy estimate
- **Technology:** Modern AI vision transformer (7.9 GB model)
- **Local:** ✅ Yes

**Example output:**
```
**Ridge & Co.**
**Hefeweizen**
**7.5% ABV**
**Imported by Black Brewing, San Francisco, CA**  ← CORRECT
```

#### Option 3: Ollama llava (Smaller AI Model)
**Test Results:**
- **Speed:** ❌ Timed out after 60 seconds (or had errors)
- **Accuracy:** ❓ Could not complete testing
- **Technology:** Medium AI vision model (4.7 GB)
- **Local:** ✅ Yes
- **Conclusion:** Not viable - slower or error-prone

#### Option 4: Cloud AI APIs (OpenAI, Google Cloud Vision)
- **Speed:** ✅ ~2 seconds
- **Accuracy:** ✅ Excellent
- **Local:** ❌ NO - blocked by government firewall
- **Conclusion:** Not viable for TTB environment

### Options Considered

#### Option 1: Tesseract Only (Meet Speed Requirement)
**Pros:**
- Meets critical 5-second requirement
- Works in TTB's firewall-restricted environment
- Fast enough for batch processing (200-300 labels)
- Production-ready and stable

**Cons:**
- Misses "AI-Powered" aspect of project title
- Lower accuracy on decorative fonts (~60-70%)
- May produce false positives/negatives due to OCR errors
- Doesn't demonstrate modern AI capability

#### Option 2: Ollama Only (AI-Powered but Slow)
**Pros:**
- Truly "AI-Powered" using modern vision transformers
- Excellent accuracy (~95%+)
- Demonstrates cutting-edge ML capability
- Better handles complex label layouts

**Cons:**
- Fails critical 5-second requirement (58 seconds)
- Sarah Chen explicitly said this is a dealbreaker
- Mirrors failed vendor pilot (30-40 seconds)
- Impractical for batch processing (200 labels = 3+ hours)

#### Option 3: Hybrid Approach ✅ SELECTED
**Pros:**
- ✅ Meets 5-second requirement (Tesseract default)
- ✅ Demonstrates AI capability (Ollama optional)
- ✅ User choice: speed vs accuracy tradeoff
- ✅ Honest about technological constraints
- ✅ Shows good engineering judgment
- ✅ Practical for different use cases

**Cons:**
- More complex implementation (two backends)
- Documentation must explain tradeoff clearly
- User must understand speed/accuracy choice

### Decision Rationale

**Selected hybrid approach because:**

1. **Acknowledges Reality of Conflicting Requirements:**
   - Both requirements (5-second + AI) are legitimate
   - Current local AI technology cannot meet both simultaneously
   - Providing both options respects both requirements

2. **Matches Real-World Use Cases:**
   - **Routine processing (90% of use):** Tesseract (fast, good enough)
   - **Complex/disputed cases (10%):** Ollama (slow, highly accurate)
   - Dave Morrison's quote: *"there's nuance... you need judgment"*
   - Agents can choose appropriate tool for the situation

3. **Demonstrates Engineering Maturity:**
   - Recognizes when requirements conflict
   - Makes reasoned tradeoffs with data
   - Documents decision transparently
   - Provides flexibility rather than rigid solution

4. **Respects Critical Requirements:**
   - **Default = Tesseract:** Respects Sarah Chen's 5-second dealbreaker
   - **Optional = Ollama:** Honors "AI-Powered" project title
   - **Both local:** Respects Marcus Williams' firewall constraint

5. **Production-Ready Architecture:**
   - Easy to add new OCR backends later
   - Can swap defaults as technology improves
   - Users vote with their usage patterns

### Implementation Details

**CLI Interface:**
```bash
# Default: Fast mode with Tesseract (~1 second)
python verify_label.py label.jpg --ground-truth app.json

# Accurate mode: Use AI for better accuracy (~60 seconds)
python verify_label.py label.jpg --ground-truth app.json --accurate

# Explicit backend selection
python verify_label.py label.jpg --ocr tesseract  # fast
python verify_label.py label.jpg --ocr ollama     # accurate
```

**Web UI (Future FastAPI):**
```html
<form>
  <input type="file" name="label" required>
  
  <!-- Speed vs Accuracy Choice -->
  <label>
    <input type="checkbox" name="use_ai" value="true">
    Use AI for higher accuracy (slower, ~60 seconds)
  </label>
  <p class="help-text">
    Default uses fast OCR (~1 second). 
    AI mode provides better accuracy but takes longer.
  </p>
  
  <!-- Application data fields... -->
</form>
```

**Metadata Output:**
```json
{
  "ocr_backend": "tesseract",
  "processing_time_seconds": 0.98,
  "confidence": 0.91,
  "note": "For higher accuracy, use --accurate flag (AI mode)"
}
```

### Performance Comparison

| Backend | Speed | Accuracy | Use Case | Default? |
|---------|-------|----------|----------|----------|
| **Tesseract** | ~1 sec | ~70% | Routine screening, batch processing | ✅ YES |
| **Ollama** | ~58 sec | ~95% | Complex cases, disputed labels | Optional |

### Documentation Strategy

**In README.md:**
```markdown
## OCR Technology Choice

This verifier uses a **hybrid OCR approach** to balance speed and accuracy:

### Default: Tesseract OCR (Fast)
- Processing time: ~1 second per label
- Meets critical 5-second requirement
- Good accuracy on clean text
- May struggle with decorative/script fonts

### Optional: Ollama AI (Accurate)
- Processing time: ~60 seconds per label  
- Superior accuracy on complex labels
- Handles decorative fonts better
- Use with `--accurate` flag

### Why Hybrid?

The project requirements contain a fundamental tension:
- **5-second performance requirement** (critical per stakeholder interview)
- **AI-powered verification** (project title)
- **Local execution** (firewall constraints)

Current AI vision models running locally cannot meet the 5-second requirement
(~60 seconds observed). Rather than fail one requirement to meet another, we
provide both options and let users choose based on their needs.

**Recommendation:** Use Tesseract for routine processing. Use AI mode for
complex or disputed cases where accuracy is more important than speed.
```

### Production Recommendations

**Near-term (6-12 months):**
1. **GPU Acceleration:** Deploy on GPU instances (g4dn.xlarge)
   - Could reduce Ollama time from 60s → 10-15s
   - Still unlikely to reach 5-second target with full models

2. **Model Optimization:**
   - Quantize llama3.2-vision (8-bit or 4-bit)
   - Try smaller models (moondream, etc.)
   - Custom fine-tuned model for label-specific task

3. **Hybrid Workflow:**
   - Tesseract for initial screening
   - AI verification only for flagged cases
   - Reduces overall processing time

**Long-term (12+ months):**
1. **Custom Trained Model:**
   - Purpose-built lightweight model for alcohol labels
   - Train on 10,000+ real TTB labels
   - Could achieve 2-5 second inference with high accuracy

2. **Hardware Acceleration:**
   - Dedicated inference hardware (NVIDIA T4, Coral TPU)
   - Batch optimization for 200-300 label imports
   - Could make AI mode practical for routine use

3. **Standardized Labels:**
   - Work with industry to standardize label formats
   - Make OCR easier with consistent fonts/layouts
   - Could improve Tesseract accuracy to 90%+

### Implications

**For Development:**
- Build OCR abstraction layer (already done in `ocr_backends.py`)
- Both backends working and tested
- Easy to add new backends as technology improves

**For Users:**
- Clear choice: fast vs accurate
- Documented tradeoffs
- Flexibility for different use cases

**For Evaluation:**
- Demonstrates understanding of conflicting requirements
- Shows engineering judgment about tradeoffs
- Provides working solution that respects all constraints
- Honest about technological limitations

**For TTB Deployment:**
- Start with Tesseract default (meets speed requirement)
- Collect usage data on accuracy issues
- Invest in GPU infrastructure if AI mode proves valuable
- Clear upgrade path as technology improves

### Success Metrics

- [✅] Tesseract backend functional and < 5 seconds
- [✅] Ollama backend functional (tested with llama3.2-vision)
- [✅] OCR abstraction layer supports both backends
- [ ] CLI supports `--accurate` flag for backend selection
- [ ] Web UI includes "Use AI for accuracy" checkbox
- [ ] Documentation clearly explains tradeoff
- [ ] Testing on 40-label golden dataset quantifies accuracy difference

### References
- Testing results: `OCR_ANALYSIS.md` (to be created)
- Stakeholder interviews: `Take-Home Project_ AI-Powered Alcohol Label Verification App.docx`
- OCR backends implementation: `ocr_backends.py`
- Sarah Chen quote (5-second requirement): Lines 66-67 of .docx
- Marcus Williams quote (firewall): Lines 85-87 of .docx

---

## Decision 011: Remove Pretty-Print Option - JSON-Only Output

**Date:** 2026-02-16  
**Status:** ✅ Decided  
**Decision:** Remove `--pretty` flag and TTY detection from CLI. Always output compact JSON with no indentation.

### Context
- Original CLI had `--pretty` flag that auto-detected TTY and pretty-printed JSON
- Moving to API-first architecture with FastAPI
- APIs should output consistent, compact JSON regardless of client
- Pretty-printing adds complexity and inconsistency between CLI and API usage

### Options Considered

#### Option 1: Keep --pretty as Debug Option
**Pros:**
- Helpful for manual debugging
- Backward compatible with existing scripts

**Cons:**
- Inconsistent behavior between CLI and API
- Additional code complexity
- Users can pipe to `jq` or `python -m json.tool` for pretty-printing

#### Option 2: Always Compact JSON ✅ SELECTED
**Pros:**
- Consistent output format (matches API behavior)
- Simpler code (remove 4+ lines of logic)
- Smaller output size for pipelines
- Industry standard for APIs
- Users can pretty-print externally if needed

**Cons:**
- Less readable for human inspection (mitigated by external tools)

### Decision Rationale
Selected **Option 2** because:
1. **API-First Design:** CLI will be wrapper around core validation logic used by API
2. **Consistency:** Same JSON format whether called via CLI, API, or programmatically
3. **Simplicity:** Removes conditional logic and flags
4. **Best Practice:** APIs return compact JSON; clients handle formatting
5. **External Tools:** `jq`, `python -m json.tool`, IDE formatters available

### Implications
- **Code Changes:** Remove `--pretty` argument, TTY detection, conditional formatting
- **Test Updates:** Update `run_tests.sh` TEST 7 to check for compact JSON
- **Documentation:** Update CLI docs to note JSON-only output
- **User Impact:** Users wanting pretty output must use external tools (one-liner: `| python -m json.tool`)

### Success Metrics
- ✅ CLI outputs identical JSON format as API
- ✅ All tests pass with compact JSON
- ✅ Code simplified (fewer conditionals)
- ✅ Documentation updated

### References
- `verify_label.py` lines 249-250, 254-256, 276, 287
- API design best practices: compact JSON for machine consumption

---

## Decision 012: Docker Strategy with Separate Ollama Service

**Date:** 2026-02-16  
**Status:** ✅ Decided  
**Decision:** Use multi-stage Docker build for main app (~500MB) with Ollama as separate service in docker-compose

### Context
- Need to containerize application for deployment
- Ollama AI vision models are ~7.9GB (llama3.2-vision)
- Want to support both fast (Tesseract) and accurate (Ollama) OCR options
- All-in-one image would be ~10GB (slow build/push, violates Docker best practices)
- Must support local development and production deployment

### Options Considered

#### Option 1: Ollama as Separate Docker Service ✅ SELECTED
**Architecture:**
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
  verifier:
    build: .
    environment:
      - OLLAMA_HOST=http://ollama:11434
```

**Pros:**
- ✅ Main app image stays lean (~500MB)
- ✅ Uses official Ollama container (well-maintained)
- ✅ Services can scale independently
- ✅ Easy GPU passthrough for Ollama
- ✅ Models cached in Docker volume (survive restarts)
- ✅ Clear separation of concerns

**Cons:**
- ⚠️ Requires docker-compose (acceptable for deployment)
- ⚠️ Minimal network overhead between containers

#### Option 2: Ollama on EC2 Host
**Pros:**
- Simplest Docker setup
- Uses host GPU directly

**Cons:**
- ❌ Not fully containerized
- ❌ Manual installation required on each host
- ❌ Host dependency reduces portability

#### Option 3: All-In-One Image
**Cons:**
- ❌ Image size ~10GB (7.9GB model + base)
- ❌ Slow build times (30+ minutes)
- ❌ Slow push/pull to registry
- ❌ Violates Docker best practices (one concern per container)
- ❌ Wastes bandwidth for users not using Ollama

### Decision Rationale
Selected **Option 1** because:
1. **Lean Images:** Main app stays ~500MB (Tesseract + Python deps)
2. **Official Images:** Ollama maintained by Ollama team, always up-to-date
3. **Flexibility:** Can run verifier without Ollama for Tesseract-only deployments
4. **Scalability:** Can scale Ollama separately if it becomes bottleneck
5. **Best Practices:** Each service has single responsibility
6. **GPU Support:** Official Ollama image handles GPU passthrough correctly
7. **Model Management:** Ollama handles model downloads/updates

### Implementation Details

**Multi-Stage Dockerfile:**
```
Stage 1: base (Python 3.12-slim + Tesseract)
Stage 2: builder (install Python dependencies)
Stage 3: test (run pytest with 80% coverage requirement)
Stage 4: production (minimal runtime)
```

**docker-compose.yml:**
- Ollama service with GPU support and health checks
- Verifier service depends on Ollama (can override for Tesseract-only)
- Shared network for service communication
- Volume for Ollama models (persist across restarts)

**Environment Configuration:**
- `OLLAMA_HOST` configurable via .env
- Defaults to docker-compose service name
- Can override for external Ollama instance

### Implications
- **Development:** Requires Docker Compose for local dev with Ollama
- **Testing:** Multi-stage build runs pytest automatically (fails if <80% coverage)
- **Deployment:** Two containers deployed together via docker-compose or orchestrator
- **Image Size:** Main app ~500MB, Ollama ~4GB (one-time pull)
- **Startup Time:** Ollama takes ~10-30s to start, verifier waits via health check
- **Graceful Degradation:** If Ollama unavailable, verifier falls back to Tesseract

### Success Metrics
- ✅ Main image size <600MB
- ✅ Docker build completes in <5 minutes (excluding model pull)
- ✅ Both services start successfully via docker-compose
- ✅ Health checks pass for both services
- ✅ Can run verifier with or without Ollama
- ✅ GPU passthrough works for Ollama (when available)

### References
- Ollama Docker image: https://hub.docker.com/r/ollama/ollama
- Docker multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- Docker Compose health checks: https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck

---

## Decision 013: Pytest Test Suite with 80% Coverage Target

**Date:** 2026-02-16  
**Status:** ✅ Decided  
**Decision:** Implement comprehensive pytest suite with 80% minimum coverage, integrated into Docker build. Keep existing bash tests for smoke testing.

### Context
- Currently have bash test script (`run_tests.sh`) with 24 tests across 8 categories
- Moving to containerized deployment requires proper CI/CD testing
- Need unit tests, integration tests, and API tests
- Docker multi-stage build should fail if tests fail or coverage too low
- Want to maintain both developer-friendly smoke tests and rigorous CI/CD tests

### Options Considered

#### Option 1: Keep Both Bash and Pytest ✅ SELECTED
**Bash Tests:**
- Quick smoke tests for local development
- Human-readable colored output
- Direct CLI testing
- Fast feedback (~30 seconds with --quick)

**Pytest Suite:**
- Comprehensive unit + integration + API tests
- Code coverage metrics
- Runs in Docker build (fails build if tests fail)
- CI/CD integration ready
- 80% minimum coverage requirement

**Pros:**
- ✅ Best of both worlds
- ✅ Bash tests remain useful for quick local checks
- ✅ Pytest provides rigor for CI/CD
- ✅ Different tools for different purposes

**Cons:**
- ⚠️ Two test suites to maintain (acceptable - different purposes)

#### Option 2: Pytest Only
**Cons:**
- ❌ Loses convenient colored CLI output for developers
- ❌ Bash tests already written and working

#### Option 3: Bash Only
**Cons:**
- ❌ Not suitable for CI/CD
- ❌ No code coverage metrics
- ❌ Harder to run in Docker

### Decision Rationale
Selected **Option 1** because:
1. **Complementary Tools:** Bash for quick dev feedback, pytest for thorough testing
2. **Developer Experience:** Bash tests provide instant visual feedback
3. **CI/CD Ready:** Pytest integrates with Docker, generates coverage reports
4. **Coverage Enforcement:** 80% minimum prevents regressions
5. **API Testing:** pytest + httpx ideal for FastAPI testing
6. **Existing Work:** Bash tests already provide value, no reason to discard

### Test Structure

```
tests/
├── conftest.py (shared fixtures)
├── test_unit/ (90% coverage target)
│   ├── test_field_validators.py
│   ├── test_label_extractor.py
│   ├── test_ocr_backends.py
│   └── test_label_validator.py
├── test_integration/ (70% coverage target)
│   ├── test_cli.py
│   └── test_end_to_end.py
└── test_api/ (95% coverage target)
    └── test_fastapi_endpoints.py
```

### Coverage Targets by Module
- `field_validators.py`: 90% (fuzzy matching, ABV tolerance, edge cases)
- `label_extractor.py`: 85% (regex patterns, field extraction)
- `ocr_backends.py`: 70% (mock Ollama, test Tesseract)
- `label_validator.py`: 90% (Tier 1/2 validation, graceful degradation)
- `verify_label.py`: 60% (CLI integration via subprocess)
- `api.py`: 95% (all endpoints, error handling)
- **Overall Target: 80%+**

### Test Against Golden Samples
- Use existing 40 golden samples (20 GOOD + 20 BAD)
- 4.9MB dataset included in Docker image
- Tests verify both Tesseract and Ollama backends
- Users can replace samples with their own (document in `docs/GOLDEN_SAMPLES.md`)

### Implications
- **Docker Build:** Test stage runs pytest automatically
- **Build Failures:** Build fails if tests fail or coverage <80%
- **Development Workflow:** Developers run bash tests locally, pytest before push
- **CI/CD:** GitHub Actions runs Docker build (includes tests)
- **Coverage Reports:** Generated in Docker, can be exported as artifacts
- **Test Fixtures:** Shared fixtures in conftest.py (golden sample paths, mock OCR)

### Success Metrics
- ✅ 80%+ code coverage achieved
- ✅ All tests pass in Docker build
- ✅ Tests complete in <2 minutes (excluding Ollama tests)
- ✅ Bash tests remain functional for quick dev checks
- ✅ API tests cover all endpoints and error conditions
- ✅ Tests catch regressions (e.g., graceful degradation working)

### References
- pytest: https://docs.pytest.org/
- pytest-cov: https://pytest-cov.readthedocs.io/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/

---

## Decision 014: FastAPI with Open Access and Minimal Observability

**Date:** 2026-02-16  
**Status:** ✅ Decided  
**Decision:** Implement FastAPI with open access (no authentication), CORS allow-all, logging to stdout only. No metrics, tracing, or API versioning at this stage.

### Context
- Building prototype to demonstrate label verification capability
- Need REST API with file upload for web UI integration
- May eventually use AWS API Gateway for production (handles auth, rate limiting, etc.)
- Want to keep prototype simple and focused on core functionality
- Containerized deployment captures stdout logs automatically

### API Design

**Endpoints:**
- `POST /verify` - Single label verification (synchronous, image + optional ground truth)
- `POST /verify/async` - Single label verification (async, queue-based, CloudFront-safe)
- `GET /verify/async/{job_id}` - Poll async verify job status
- `POST /verify/retry/{job_id}` - Re-enqueue a failed async verify job
- `POST /verify/batch` - Batch verification (ZIP file, async)
- `GET /verify/batch/{job_id}` - Poll batch job status
- `GET /health` - Health check
- `GET /docs` - Auto-generated Swagger UI (`/redoc` is disabled)

**Request Limits:**
- Max file size: 10MB per image
- Max batch size: 50 images
- Allowed formats: .jpg, .jpeg, .tif, .tiff (PNG is **not** accepted — not a TTB COLA format)

**Batch ZIP Format:**
```
batch.zip
├── label_001.jpg
├── label_001.json (ground truth, optional)
├── label_002.tif
├── label_002.json
└── ...
```

JSON files must match image filenames (e.g., `label_001.jpg` → `label_001.json`)

### Security & Access Control

#### Authentication: Session-Based Auth ✅ IMPLEMENTED
**Rationale:**
- Session cookie authentication added (4-hour sessions, httponly cookies)
- Credentials stored in AWS Secrets Manager
- Host-header middleware enforces domain-only access (rejects direct ALB/IP access)
- Login endpoint: `POST /ui/login`

**Note:** The original design called for open access with authentication deferred to API Gateway. This was revised — a lightweight built-in auth layer was implemented to prevent unauthorized access to the prototype.

#### CORS: Allow All Origins
**Configuration:** `CORS_ORIGINS=["*"]`

**Rationale:**
- Prototype needs to work from any dev environment
- Frontend may be served from localhost, different ports, etc.
- Production will restrict to specific domains

**Future:**
```python
# Production CORS example (commented in code)
CORS_ORIGINS=[
    "https://ttb.gov",
    "https://cola.ttb.gov", 
    "https://label-verify.ttb.gov"
]
```

### Observability

#### Logging: Stdout Only ✅ SELECTED
**Implementation:**
- Structured logs to stdout
- Docker captures and forwards to log aggregator
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Log level configurable via env var (default: INFO)

**Rationale:**
- Docker best practice: log to stdout
- Syslog, CloudWatch, or other aggregators can capture stdout
- No file I/O reduces complexity
- Container-native approach

#### Metrics: None at This Stage
**Decision:** No Prometheus, StatsD, or custom metrics

**Rationale:**
- Prototype focuses on functionality
- AWS API Gateway provides metrics in production
- Can add `/metrics` endpoint later if needed (comment in code)

**Future Options (Commented):**
```python
# Option 1: Prometheus metrics
# from prometheus_fastapi_instrumentator import Instrumentator
# Instrumentator().instrument(app).expose(app)

# Option 2: CloudWatch via boto3
# Option 3: Custom metrics to external service
```

#### Tracing: None at This Stage
**Decision:** No distributed tracing (OpenTelemetry, Jaeger, etc.)

**Rationale:**
- Single service (verifier + Ollama)
- No microservices requiring tracing
- Adds complexity without current benefit

#### API Versioning: None at This Stage
**Decision:** No `/v1/` or `/v2/` prefix

**Rationale:**
- First version of API
- Breaking changes unlikely in prototype
- Can add versioning when needed

**Future Path:**
```python
# When versioning needed:
# app.include_router(v1_router, prefix="/v1")
# app.include_router(v2_router, prefix="/v2")
```

### Rate Limiting

**Decision:** No rate limiting in app code

**Rationale:**
- AWS API Gateway handles rate limiting in production
- Prototype deployed in controlled environment
- Can add `slowapi` if needed (comment in code)

**Future Implementation (Commented):**
```python
# from slowapi import Limiter
# limiter = Limiter(key_func=get_remote_address)
# @limiter.limit("100/hour")
# async def verify_label(...):
```

### Error Handling

**HTTP Status Codes:**
- `200 OK` - Successful validation (includes NON_COMPLIANT status in JSON)
- `400 Bad Request` - Invalid file format, malformed JSON
- `413 Payload Too Large` - File >10MB or batch >50 images
- `422 Unprocessable Entity` - Validation error (Pydantic)
- `500 Internal Server Error` - OCR failure, unexpected errors

**Error Response Format:**
```json
{
  "error": "File too large",
  "detail": "Maximum file size is 10MB",
  "timestamp": "2026-02-16T12:00:00Z"
}
```

### Implications
- **Development:** Simplified API without auth complexity
- **Testing:** Easy to test with curl, no tokens needed
- **Deployment:** Docker logs go to stdout (captured by orchestrator)
- **Production Path:** Clear migration to API Gateway for enterprise features
- **Documentation:** Must document prototype nature and production considerations
- **Future-Proofing:** Comments in code show where to add auth/metrics/versioning

### Success Metrics
- ✅ API endpoints work without authentication
- ✅ CORS allows requests from any origin
- ✅ Logs appear in Docker stdout
- ✅ File upload handles 10MB images
- ✅ Batch processing handles 50 images
- ✅ Error responses have consistent format
- ✅ Swagger UI auto-generated and functional

### References
- FastAPI CORS: https://fastapi.tiangolo.com/tutorial/cors/
- FastAPI file uploads: https://fastapi.tiangolo.com/tutorial/request-files/
- Docker logging: https://docs.docker.com/config/containers/logging/
- AWS API Gateway: https://aws.amazon.com/api-gateway/

---

## Decision 015: Container Registry - GitHub Container Registry (GHCR)

**Date:** 2026-02-16  
**Status:** ✅ Decided  
**Decision:** Use GitHub Container Registry (GHCR) for container image storage and distribution

### Context
- Need to deploy Docker images from CI/CD pipeline to AWS EC2 instances
- Must choose between GitHub Container Registry (GHCR) and AWS Elastic Container Registry (ECR)
- Project is in prototype/POC phase, deploying to AWS infrastructure
- Already using GitHub for source control
- Budget is not a constraint but simplicity is valued

### Options Considered

#### Option 1: GitHub Container Registry (GHCR) ✅ SELECTED
**Pros:**
- Native GitHub integration - single platform for code and containers
- GitHub Actions can push without credential configuration (uses `GITHUB_TOKEN`)
- Free for private repositories (500MB storage, unlimited bandwidth)
- Simpler CI/CD setup (5-10 minutes vs 20-30 minutes)
- Unified access control with GitHub repository permissions
- Packages linked directly to repository for easy discovery
- No separate billing or AWS account coordination needed

**Cons:**
- Not AWS-native - EC2 pulls over internet (slight latency vs VPC)
- Limited vulnerability scanning (basic only, not Inspector-grade)
- Fewer advanced registry features (lifecycle policies, immutable tags)
- Cross-region bandwidth charges (GHCR → AWS)

#### Option 2: AWS Elastic Container Registry (ECR)
**Pros:**
- AWS-native integration with EC2 (same network, VPC endpoints)
- Sub-second image pulls within same AWS region
- Native IAM integration (EC2 instance profiles)
- Advanced vulnerability scanning (Amazon Inspector)
- Image lifecycle policies for cost optimization
- Encryption at rest with AWS KMS
- Better for government compliance (FedRAMP, etc.)

**Cons:**
- Cost: ~$0.10 per GB/month storage + bandwidth charges (~$2-5/month)
- More complex CI/CD setup (AWS credentials in GitHub Secrets)
- Additional authentication steps (`aws ecr get-login-password`)
- More moving parts (IAM policies, ECR policies, credentials rotation)

### Decision Rationale

**GHCR was chosen for the following reasons:**

1. **Rapid Iteration Priority**: Currently in prototype/POC phase where speed of implementation matters more than production optimization
2. **Simplicity**: Unified GitHub workflow reduces complexity and maintenance burden
3. **Zero Additional Cost**: Free for private repositories eliminates budget approval delays
4. **Sufficient for Current Needs**: Basic vulnerability scanning and unlimited bandwidth meet prototype requirements
5. **Easy Migration Path**: Can migrate to ECR later if production deployment requires AWS-native features
6. **One Less Service**: Reduces operational overhead during development phase

### Implications

**Immediate:**
- CI/CD pipeline will be simpler and faster to implement
- No AWS credential management needed for container registry
- EC2 instances will pull images over internet (acceptable latency for prototype)

**Future Migration Path:**
- If production deployment requires ECR (compliance, performance, VPC isolation):
  - Migration is straightforward: re-tag and push existing images
  - GitHub Actions workflow changes are minimal (swap registry endpoint)
  - No code changes required in application

**Best Practice:**
- Use this prototype phase to validate the full deployment process
- Re-evaluate before production launch if:
  - Government compliance mandates AWS-only infrastructure
  - Image pull performance becomes critical (multi-region, high frequency)
  - Advanced registry features are needed (lifecycle policies, cross-region replication)

### Success Metrics
- ✅ CI/CD pipeline setup completed in <30 minutes
- ✅ Image build and push time <10 minutes
- ✅ EC2 image pull time <60 seconds (acceptable for prototype)
- ✅ Zero registry-related costs during development

### References
- [GHCR Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [AWS ECR Pricing](https://aws.amazon.com/ecr/pricing/)
- [docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md) - Updated with GHCR instructions

---

## Template for Future Decisions

**Date:** YYYY-MM-DD  
**Status:** 🔄 Pending | ✅ Decided | ❌ Rejected | 🔄 Revised  
**Decision:** [Clear statement of the decision]

### Context
[Why is this decision needed? What problem does it solve?]

### Options Considered
[List alternatives with pros/cons]

### Decision Rationale
[Why was this option chosen?]

### Implications
[What does this mean for the project?]

### Success Metrics
[How will we know this was the right choice?]

### References
[Links to relevant documentation or resources]

---

**Document Maintained By:** Project Team  
**Last Updated:** 2026-02-16  
**Recent Additions:**
- Decision 012: Docker Strategy with Separate Ollama Service  
- Decision 013: Pytest Test Suite with 80% Coverage Target
- Decision 014: FastAPI with Open Access and Minimal Observability
- Decision 015: Container Registry - GitHub Container Registry (GHCR)
