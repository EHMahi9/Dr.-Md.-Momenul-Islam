# Problem Statement: Dr. Md. Momenul Islam

## 1. Background
People often need health information before they are able or willing to consult a healthcare professional. While the internet contains an enormous amount of health information, the fundamental challenge is not a lack of data. Instead, users struggle to find trustworthy sources, understand professional medical terminology, distinguish reliable information from misinformation, and know when a symptom requires urgent professional attention. The project focuses on bridging the gap between the mere existence of health information and a person's ability to safely understand and use that information.

## 2. Bangladesh Context
This project is specifically focused on the healthcare information landscape in Bangladesh. The problem must be examined within this context rather than treating it as a generic global issue.

Key areas of concern in Bangladesh include:
* Accessibility of understandable health information for the general public.
* The quality and availability of health information in the Bangla language.
* Trends in digital health-information usage.
* The prevalence of misinformation and conflicting health advice.
* Challenges users face when trying to understand medical terminology.
* The critical importance of knowing when to seek professional healthcare.

*(Note: Statistical claims regarding digital health literacy, internet penetration, and health information seeking behaviors in Bangladesh are currently marked as **[Research Required]** and will be supported by authoritative sources such as government agencies, WHO, or peer-reviewed research in the future).*

## 3. Core Problem
The core problem is that individuals seeking health information face significant cognitive and safety hurdles:
* Finding trustworthy health information amidst a sea of unverified content.
* Understanding medical information that is often written for professionals.
* Distinguishing reliable, evidence-based information from misinformation.
* Determining which piece of information is actually relevant to their specific question.
* Recognizing when a symptom may require professional medical attention.
* Interpreting information consistently across different websites, social media posts, videos, or general AI chatbots.
* Accessing useful, reliable health information comfortably in Bangla.

## 4. Limitations of Current Information-Seeking Methods
Ordinary search-engine-based health information has distinct limitations for the average user:
* Search results contain information of highly variable quality.
* Users carry the burden of deciding which sources are trustworthy.
* Medical information may be fragmented across multiple pages, requiring the user to synthesize it.
* Technical and clinical language can be difficult to interpret.
* Search results are not inherently personalized to the user's specific phrasing or situation.
* Search engines do not guarantee that the information shown is medically appropriate for the user's context.
* Users frequently encounter conflicting information from different sources.

*While search engines are not universally unsafe or inaccurate, the core issue is that the user must independently evaluate, interpret, and synthesize complex medical data.*

## 5. Limitations of General-Purpose LLMs
Simply connecting a user to a general-purpose Large Language Model (LLM) is insufficient and potentially unsafe for health information because:
* LLMs can generate incorrect information (hallucinations).
* LLMs often produce confident-sounding answers even when the information is highly uncertain.
* A general-purpose model may not consistently cite the specific medical sources used to generate its response.
* The model's internal training knowledge may not be sufficient, current, or localized for every medical question.
* Users may misinterpret a fluent, conversational response as professional medical advice.
* A general LLM does not automatically guarantee adherence to strict safety policies required for health information.

*(Note: While Retrieval-Augmented Generation (RAG) is a proposed solution to some of these issues, it does not completely eliminate hallucination or guarantee absolute medical correctness).*

## 6. Identified Gap
The proposed system addresses the gap between **unstructured, scattered health information** and a **clear, evidence-grounded health information experience**. 

The flow to address this gap is structured as:
User Question → Safety-Aware Processing → Trusted Medical Knowledge Retrieval → Relevant Evidence → AI-Assisted Explanation → Clear Uncertainty Communication → Sources and Warning Signs.

The goal is not to create a replacement doctor, but to create a safer, more understandable way of accessing general health information.

## 7. Proposed Direction
The project intends to address the core problem through a strategic combination of:
* **Trusted Knowledge Sources:** Utilizing a controlled collection of approved medical and public-health sources rather than arbitrary internet content.
* **Retrieval-Augmented Generation (RAG):** Retrieving relevant evidence from the approved knowledge base before generating a response.
* **Safety Layer:** Introducing explicit safety rules to handle potentially urgent or unsafe situations conservatively.
* **Uncertainty Communication:** Clearly distinguishing between known information, possible explanations, uncertainty, and situations requiring professional evaluation.
* **Source Attribution:** Providing transparent citations for any retrieved material used in the answer.
* **Bangla + English Support:** Allowing users to interact comfortably in both Bangla and English.

## 8. Project Boundary
**The problem being solved is:**
*"How can a software system help people in Bangladesh access understandable, source-grounded health information while clearly communicating uncertainty and encouraging appropriate professional care?"*

**The problem is NOT:**
*"How can we build an AI that replaces doctors?"*

## 9. Research Gaps / Evidence Required
To fully validate the problem statement and guide the project's requirements, the following areas require external, authoritative evidence:
* **[Research Required]** Bangladesh digital health information context and demographics.
* **[Research Required]** Availability, quality, and accessibility of Bangla health information online.
* **[Research Required]** Health misinformation concerns specific to the region.
* **[Research Required]** Digital health literacy considerations among the target demographic.
* **[Research Required]** Efficacy and risks of existing patient-facing medical AI systems.
* **[Research Required]** Documented limitations and risks of general-purpose LLMs in medical contexts.
* **[Research Required]** Relevant safety considerations and guidelines for medical AI. 

*(All future numerical claims or studies added to this document must be verified with authoritative and recent sources, avoiding fabricated statistics).*
