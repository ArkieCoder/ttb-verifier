# AI-Powered Alcohol Label Verification App - Requirements Document

## Project Overview

**Organization:** U.S. Treasury Department - Alcohol and Tobacco Tax and Trade Bureau (TTB)  
**Project Type:** Take-Home Assessment / Proof-of-Concept  
**Timeline:** One week from receipt  
**Context:** Prototype for AI-assisted label compliance verification to support TTB's Compliance Division

## Executive Summary

The TTB processes approximately 150,000 label applications annually with a team of 47 compliance agents. The current manual review process, while effective, requires agents to spend significant time on routine verification tasks that could be automated. This prototype aims to demonstrate how AI-powered verification could assist agents in checking alcohol beverage labels against submitted application data.

## Stakeholder Context

### Current State
- **Volume:** ~150,000 label applications/year
- **Team Size:** 47 compliance agents (down from 100+ in the 1980s)
- **Current System:** COLA system (online since 2003)
- **Review Time:** 5-10 minutes per simple application
- **Infrastructure:** Azure-based (.NET COLA system)
- **Team Demographics:** Mixed technical proficiency; approximately half the team is over 50

### Pain Points
1. Agents spend ~50% of time on routine data matching tasks
2. Previous vendor pilot failed due to 30-40 second processing times
3. No batch processing capability for high-volume importers
4. Manual, eyes-on verification for every field
5. Previous modernization attempts have failed due to complexity or cost

### Previous Failed Initiative
- **Vendor:** Scanning vendor pilot (last year)
- **Failure Reason:** 30-40 second processing time per label made it slower than manual review
- **Lesson Learned:** Performance is critical for adoption

## Functional Requirements

### Core Features (Must Have)

#### 1. Label Image Upload
- **FR-1.1:** System shall accept image uploads of alcohol beverage labels
- **FR-1.2:** System shall support common image formats (JPEG, PNG, etc.)
- **FR-1.3:** System shall provide clear visual feedback during upload process

#### 2. Application Data Input
- **FR-2.1:** System shall accept manual input of application data for verification
- **FR-2.2:** System shall support the following fields:
  - Brand Name
  - Class/Type Designation
  - Alcohol Content (ABV/Proof)
  - Net Contents
  - Name and Address of Bottler/Producer
  - Country of Origin (for imports)
  - Government Health Warning Statement

#### 3. Automated Verification
- **FR-3.1:** System shall extract text from uploaded label images using OCR/AI
- **FR-3.2:** System shall compare extracted text against provided application data
- **FR-3.3:** System shall identify matches and mismatches for each field
- **FR-3.4:** System shall flag missing required fields

#### 4. Government Warning Validation
- **FR-4.1:** System shall verify presence of government warning statement
- **FR-4.2:** System shall validate that "GOVERNMENT WARNING:" is in all caps and bold
- **FR-4.3:** System shall verify exact wording of warning text
- **FR-4.4:** System shall flag formatting variations (e.g., "Government Warning" in title case)

#### 5. Results Display
- **FR-5.1:** System shall display verification results in clear, easy-to-read format
- **FR-5.2:** System shall use visual indicators (colors, icons) to show pass/fail status
- **FR-5.3:** System shall highlight specific mismatches with details
- **FR-5.4:** System shall display extracted text alongside application data for agent review

### Enhanced Features (Should Have)

#### 6. Batch Processing
- **FR-6.1:** System should support batch upload of multiple labels
- **FR-6.2:** System should process batch uploads efficiently
- **FR-6.3:** System should provide aggregate results view for batch operations
- **FR-6.4:** System should allow individual review of batch items

#### 7. Intelligent Matching
- **FR-7.1:** System should handle minor formatting variations (e.g., "STONE'S THROW" vs "Stone's Throw")
- **FR-7.2:** System should provide confidence scores for matches
- **FR-7.3:** System should flag ambiguous cases for human review

#### 8. Image Quality Handling
- **FR-8.1:** System should handle labels photographed at angles
- **FR-8.2:** System should tolerate poor lighting conditions
- **FR-8.3:** System should handle glare on bottle images
- **FR-8.4:** System should provide feedback on image quality issues

## Non-Functional Requirements

### Performance
- **NFR-1.1:** System shall return verification results within 5 seconds per label (CRITICAL)
- **NFR-1.2:** System shall maintain performance under concurrent user load
- **NFR-1.3:** Batch processing shall not significantly degrade per-label processing time

### Usability
- **NFR-2.1:** Interface shall be intuitive enough for users with minimal technical experience
- **NFR-2.2:** UI shall follow "my 73-year-old mother" standard (simple, obvious, no hunting for buttons)
- **NFR-2.3:** System shall provide clear error messages and guidance
- **NFR-2.4:** System shall work on standard government workstations and browsers

### Reliability
- **NFR-3.1:** System shall handle errors gracefully without crashing
- **NFR-3.2:** System shall validate inputs and provide meaningful feedback
- **NFR-3.3:** System shall handle network interruptions appropriately

### Security (Prototype Scope)
- **NFR-4.1:** System shall not store sensitive PII beyond session scope
- **NFR-4.2:** System shall follow basic security best practices
- **NFR-4.3:** System design should consider future federal compliance requirements (FedRAMP, etc.)

### Deployment
- **NFR-5.1:** System shall be deployable to publicly accessible URL
- **NFR-5.2:** System shall include clear setup and deployment documentation
- **NFR-5.3:** System should be deployable without complex infrastructure requirements

## Technical Constraints

### Infrastructure
- **TC-1:** Prototype is standalone; no direct integration with COLA system required
- **TC-2:** Current production infrastructure is Azure-based (.NET)
- **TC-3:** Government networks may block outbound traffic to many domains
- **TC-4:** Consider firewall restrictions when using cloud APIs

### Standards & Compliance
- **TC-5:** Must follow TTB label requirements (reference: ttb.gov)
- **TC-6:** For production: PII considerations, document retention policies, federal compliance
- **TC-7:** For production: FedRAMP certification process required

## User Personas

### Dave Morrison - Senior Agent (Skeptical Veteran)
- **Experience:** 28 years at TTB
- **Tech Comfort:** Low (prints emails)
- **Needs:** Tools that don't make life harder; values judgment and nuance
- **Pain Points:** Has seen modernization projects fail; resistant to change
- **Quote:** "Just don't make my life harder in the process"

### Jenny Park - Junior Agent (Tech-Savvy Newcomer)
- **Experience:** 8 months at TTB
- **Tech Comfort:** High (could probably build the tool herself)
- **Needs:** Automation to reduce manual checking; modern workflow
- **Pain Points:** Shocked by manual process; uses printed checklist
- **Quote:** "It's 2024!"

### Sarah Chen - Deputy Director (Decision Maker)
- **Role:** Leadership, business perspective
- **Needs:** Efficiency gains; agent productivity; adoption by entire team
- **Constraints:** Budget limitations; diverse team capabilities
- **Success Criteria:** 5-second response time; intuitive interface

## Key Stakeholder Quotes

> "If we can't get results back in about 5 seconds, nobody's going to use it. We learned that the hard way." - Sarah Chen

> "We need something my mother could figure out—she's 73 and just learned to video call her grandkids last year." - Sarah Chen

> "The thing about label review is there's nuance. You can't just pattern match everything." - Dave Morrison

> "The warning statement has to be exact. Like, word-for-word, and the 'GOVERNMENT WARNING:' part has to be in all caps and bold." - Jenny Park

## Sample Test Data

### Example Distilled Spirits Label
```
Brand Name: "OLD TOM DISTILLERY"
Class/Type: "Kentucky Straight Bourbon Whiskey"
Alcohol Content: "45% Alc./Vol. (90 Proof)"
Net Contents: "750 mL"
Government Warning: [Standard government warning text]
Bottler: [Name and address]
Country of Origin: "USA"
```

### Test Scenarios to Support
1. **Perfect Match:** All fields match exactly
2. **Case Variation:** Brand name case differences (STONE'S THROW vs Stone's Throw)
3. **Warning Formatting:** Warning statement formatting violations
4. **Missing Fields:** Required fields absent from label
5. **Poor Image Quality:** Angled shots, glare, poor lighting
6. **Batch Processing:** 200-300 labels from single importer

## Deliverables

### 1. Source Code Repository
- All application source code
- README with setup and run instructions
- Documentation covering:
  - Architectural approach
  - Tools and frameworks used
  - Key assumptions made
  - Known limitations and trade-offs
  - Future enhancement recommendations

### 2. Deployed Application
- Working prototype accessible via public URL
- Stable and testable by evaluation team
- Includes sample data or test labels

## Evaluation Criteria

1. **Correctness and Completeness** - Core requirements implemented and working
2. **Code Quality and Organization** - Clean, maintainable, well-structured code
3. **Technical Choices** - Appropriate technology selections for scope and constraints
4. **User Experience** - Intuitive interface, clear feedback, error handling
5. **Attention to Requirements** - Understanding and addressing stakeholder needs
6. **Creative Problem-Solving** - Thoughtful approaches to challenges and edge cases

## Priorities

### Critical (Must Deliver)
- Image upload and OCR text extraction
- Field-by-field comparison and verification
- Government warning validation
- Clear results display
- < 5 second response time
- Simple, intuitive interface

### Important (Should Deliver)
- Batch processing capability
- Intelligent matching (case variations, etc.)
- Good error handling and user feedback
- Clean code and documentation

### Nice to Have (Could Deliver)
- Image quality handling and feedback
- Confidence scoring
- Advanced matching algorithms
- Additional beverage type support

## Assumptions and Clarifications Needed

### Assumptions
1. Prototype does not require authentication/authorization
2. Data does not need to persist between sessions
3. Can use third-party AI/ML services (if network allows)
4. Government warning text standard is publicly available
5. Test labels can be generated or sourced independently

### Open Questions
1. Is there a standard government warning text template to validate against?
2. Are there specific beverage types to prioritize (beer, wine, or spirits)?
3. Should the system handle multiple languages?
4. What level of matching tolerance is acceptable for numeric fields (ABV)?
5. Should rejected labels provide specific guidance on how to fix issues?

## Success Metrics

### Technical Success
- Response time < 5 seconds per label
- Successful text extraction from clear label images
- Accurate field matching (manual verification)
- Stable performance across test scenarios

### User Success
- Interface can be navigated without documentation
- Clear understanding of verification results
- Efficient workflow (faster than manual review)
- Positive feedback from stakeholder perspective

## Out of Scope (for Prototype)

- Direct integration with COLA system
- User authentication and role-based access
- Persistent data storage and retrieval
- Full production security compliance
- Support for all beverage types and edge cases
- Mobile application
- Multi-language support
- Advanced image enhancement/correction
- Audit trail and compliance reporting
- API for external system integration

## Technical Implementation Notes

### Recommended Considerations
1. **AI/ML Services:** Consider OpenAI GPT-4 Vision, Google Cloud Vision, Azure Computer Vision
2. **Framework:** Modern web framework (React, Vue, Next.js, etc.)
3. **Backend:** Node.js, Python, or similar for API layer
4. **Deployment:** Vercel, Netlify, Azure, AWS, or similar
5. **Image Processing:** Consider pre-processing for image quality improvements
6. **Performance:** Optimize API calls, consider caching strategies

### Risk Mitigation
- **Network Restrictions:** Have fallback if cloud APIs are blocked in production
- **Performance:** Implement timeout handling and progress indicators
- **Accuracy:** Provide confidence scores; allow agent override
- **Adoption:** Prioritize simplicity and clear value demonstration

## Timeline

**Total Duration:** One week from receipt

### Suggested Breakdown
- **Day 1-2:** Requirements analysis, technical design, setup
- **Day 3-4:** Core feature implementation (upload, OCR, comparison)
- **Day 5:** Enhanced features (batch processing, intelligent matching)
- **Day 6:** Testing, refinement, documentation
- **Day 7:** Deployment, final testing, submission preparation

## References

- TTB Label Requirements: ttb.gov
- COLA System: Current TTB application system (online since 2003)
- FedRAMP: Federal Risk and Authorization Management Program
- Azure Government: Current TTB infrastructure platform

---

**Document Version:** 1.0  
**Last Updated:** [Date]  
**Prepared For:** US Treasury Department - TTB Take-Home Assessment  
**Status:** Ready for Implementation
