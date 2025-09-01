"""
LLM Service for Legal AI
Provides intelligent document analysis, redlining suggestions, and legal insights
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM-powered legal document analysis"""
    
    def __init__(self):
        """Initialize the LLM service"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        
        # Load legal terms and phrases
        self.legal_terms = self._load_legal_data("legal_terms.json")
        self.legal_phrases = self._load_legal_data("legal_phrases.json")
        
        # Initialize OpenAI client
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
            self.enabled = True
            logger.info("LLM service initialized with OpenAI")
        else:
            self.enabled = False
            logger.warning("LLM service disabled - no OpenAI API key")
    
    def _load_legal_data(self, filename: str) -> Dict[str, Any]:
        """Load legal data from JSON files"""
        try:
            filepath = Path(__file__).parent.parent / "data" / filename
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            return {}
    
    def _call_openai(self, prompt: str, system_message: str = None) -> Optional[str]:
        """Make a call to OpenAI API"""
        if not self.enabled:
            return None
            
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return None
    
    def analyze_document(self, content: str) -> Dict[str, Any]:
        """
        Analyze legal document for key terms, risks, and insights
        
        Args:
            content: Document content to analyze
            
        Returns:
            Dictionary with analysis results in LLMAnalysisResponse format
        """
        import time
        start_time = time.time()
        
        if not self.enabled:
            return self._fallback_analysis(content, start_time)
        
        system_message = """You are an expert legal AI assistant specializing in contract analysis. Your role is to provide clear, structured, and actionable legal insights.

IMPORTANT: Structure your response as a JSON object with the following exact format:
{
  "key_terms": ["specific term 1", "specific term 2", "specific term 3", "specific term 4", "specific term 5"],
  "risks": ["specific risk 1", "specific risk 2", "specific risk 3", "specific risk 4"],
  "document_type": "exact document type",
  "summary": "concise 2-3 sentence summary of document purpose and key elements",
  "recommendations": ["specific actionable recommendation 1", "specific actionable recommendation 2", "specific actionable recommendation 3"]
}

Guidelines:
- Extract 5-8 MOST IMPORTANT and SPECIFIC legal terms from THIS document (not generic terms)
- Identify 3-5 SPECIFIC legal risks or concerns found in THIS document
- Determine the EXACT document type based on content analysis
- Provide a concise summary specific to THIS document's purpose and key elements
- Give 3-5 SPECIFIC, ACTIONABLE recommendations tailored to THIS document's content
- Each term, risk, and recommendation must be UNIQUE and SPECIFIC to the document
- Avoid generic responses - be specific to the actual content"""
        
        prompt = f"""Analyze this legal document and provide structured insights:

{content[:4000]}

Please provide a JSON response with:
1. KEY TERMS: List 5-8 most important legal terms/clauses SPECIFIC to this document (not generic terms)
2. RISKS: Identify 3-5 specific legal risks or potential issues FOUND IN THIS DOCUMENT
3. DOCUMENT TYPE: Classify the specific type of legal document based on its content
4. SUMMARY: 2-3 sentence overview of THIS document's purpose and key provisions
5. RECOMMENDATIONS: 3-5 specific, actionable recommendations tailored to THIS document's content

CRITICAL: Each term, risk, and recommendation must be UNIQUE and SPECIFIC to this document. Avoid generic responses."""
        
        response = self._call_openai(prompt, system_message)
        
        if response:
            return self._parse_analysis_response(response, content, start_time)
        else:
            return self._fallback_analysis(content, start_time)
    
    def suggest_improvements(self, content: str) -> List[Dict[str, str]]:
        """
        Suggest legal language improvements
        
        Args:
            content: Document content to improve
            
        Returns:
            List of improvement suggestions
        """
        if not self.enabled:
            return self._fallback_suggestions(content)
        
        system_message = """You are a legal language expert. Review the provided legal document and suggest improvements for:
1. Clarity and readability
2. Legal precision
3. Standard legal language
4. Risk mitigation
5. Consistency and structure

Provide specific, actionable suggestions with examples."""
        
        prompt = f"""Please review this legal document and suggest improvements:

{content[:3000]}...

Focus on:
- Legal language improvements
- Clarity enhancements
- Standard legal phrases
- Risk mitigation
- Consistency issues"""
        
        response = self._call_openai(prompt, system_message)
        
        if response:
            return self._parse_suggestions_response(response)
        else:
            return self._fallback_suggestions(content)
    
    def extract_legal_terms(self, content: str) -> List[Dict[str, str]]:
        """
        Extract legal terms and their context
        
        Args:
            content: Document content to analyze
            
        Returns:
            List of legal terms with context
        """
        if not self.enabled:
            return self._fallback_term_extraction(content)
        
        system_message = """You are a legal term extraction specialist. Identify legal terms, clauses, and concepts in the document. For each term:
1. Provide the exact term
2. Give its legal meaning
3. Identify the context where it appears
4. Note any potential implications"""
        
        prompt = f"""Please extract legal terms from this document:

{content[:3000]}...

Identify and explain:
- Legal terms and definitions
- Clauses and provisions
- Legal concepts and principles
- Context and implications"""
        
        response = self._call_openai(prompt, system_message)
        
        if response:
            return self._parse_terms_response(response)
        else:
            return self._fallback_term_extraction(content)
    
    def classify_document(self, content: str) -> Dict[str, Any]:
        """
        Classify legal document type and category
        
        Args:
            content: Document content to classify
            
        Returns:
            Classification results
        """
        if not self.enabled:
            return self._fallback_classification(content)
        
        system_message = """You are a legal document classification expert. Analyze the document and determine:
1. Primary document type
2. Legal category
3. Industry/sector
4. Complexity level
5. Key characteristics"""
        
        prompt = f"""Please classify this legal document:

{content[:3000]}...

Determine:
- Document type (contract, agreement, etc.)
- Legal category
- Industry/sector
- Complexity level
- Key characteristics"""
        
        response = self._call_openai(prompt, system_message)
        
        if response:
            return self._parse_classification_response(response)
        else:
            return self._fallback_classification(content)
    
    def semantic_search(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform semantic search across documents
        
        Args:
            query: Search query
            documents: List of documents to search
            
        Returns:
            Ranked search results
        """
        if not self.enabled:
            return self._fallback_semantic_search(query, documents)
        
        system_message = """You are a legal search specialist. Analyze the search query and rank documents by relevance. 

IMPORTANT: Your response should list the document IDs in order of relevance, like this:
"Most relevant documents: ID: 1, ID: 3, ID: 2"

Consider:
1. Semantic meaning and legal concepts
2. Context relevance to the query
3. Document type and legal category
4. Term matching and legal terminology
5. Overall legal significance"""
        
        # Create document summaries for analysis
        doc_summaries = []
        for doc in documents:
            summary = f"ID: {doc.get('id')}, Title: {doc.get('title')}, Content: {doc.get('content', '')[:500]}..."
            doc_summaries.append(summary)
        
        prompt = f"""Search Query: "{query}"

Available Documents:
{chr(10).join(doc_summaries)}

Please analyze the search query and rank the documents by relevance. Consider semantic meaning, legal concepts, and context relevance.

Respond with: "Most relevant documents: ID: [number], ID: [number], ID: [number]" in order of relevance."""
        
        response = self._call_openai(prompt, system_message)
        
        if response:
            return self._parse_semantic_search_response(response, documents)
        else:
            return self._fallback_semantic_search(query, documents)
    
    # Fallback methods when LLM is not available
    def _fallback_analysis(self, content: str, start_time: float) -> Dict[str, Any]:
        """Fallback document analysis using rule-based approach"""
        import time
        processing_time = time.time() - start_time
        
        # Extract key terms and risks
        key_terms = self._extract_terms_rule_based(content)
        risks = self._identify_risks_rule_based(content)
        doc_type = self._classify_document_rule_based(content)
        
        # Create structured summary
        summary = f"This is a {doc_type.lower()} document. "
        if "agreement" in content.lower() or "contract" in content.lower():
            summary += "The document establishes terms and conditions between parties. "
        if "payment" in content.lower():
            summary += "It includes payment terms and obligations. "
        if "termination" in content.lower():
            summary += "The document contains termination provisions."
        
        # Create specific recommendations based on content analysis
        recommendations = []
        content_lower = content.lower()
        
        if not any(word in content_lower for word in ["payment", "compensation", "fee", "rate"]):
            recommendations.append("Add clear payment terms specifying amount, schedule, and method of payment")
        if not any(word in content_lower for word in ["termination", "expiration", "end", "cancel"]):
            recommendations.append("Include termination clause with specific conditions and notice requirements")
        if not any(word in content_lower for word in ["liability", "indemnification", "damages", "responsibility"]):
            recommendations.append("Add liability and indemnification provisions to protect both parties")
        if not any(word in content_lower for word in ["dispute", "arbitration", "mediation", "resolution"]):
            recommendations.append("Include dispute resolution mechanism with specific procedures")
        if not any(word in content_lower for word in ["confidentiality", "privacy", "proprietary", "secret"]):
            recommendations.append("Add confidentiality provisions to protect sensitive information")
        if not any(word in content_lower for word in ["intellectual property", "copyright", "trademark", "patent"]):
            recommendations.append("Include intellectual property rights and ownership clauses")
        if not recommendations:
            recommendations = [
                "Consider adding force majeure clause for unforeseen circumstances",
                "Include governing law and jurisdiction provisions",
                "Add amendment procedures for future contract modifications"
            ]
        
        return {
            "analysis": {
                "key_terms": key_terms,
                "risks": risks,
                "document_type": doc_type,
                "summary": summary.strip(),
                "recommendations": recommendations,
                "source": "rule_based"
            },
            "suggestions": [
                {
                    "type": "clarity",
                    "suggestion": "Use precise legal language throughout the document",
                    "example": "Use 'shall' instead of 'will' for obligations",
                    "source": "rule_based"
                },
                {
                    "type": "structure",
                    "suggestion": "Organize clauses in logical order for better readability",
                    "example": "Group related terms and conditions together",
                    "source": "rule_based"
                },
                {
                    "type": "completeness",
                    "suggestion": "Ensure all essential legal elements are included",
                    "example": "Add missing termination, payment, and liability clauses",
                    "source": "rule_based"
                }
            ],
            "terms": [
                {
                    "term": term,
                    "meaning": self._get_term_meaning(term, doc_type),
                    "context": f"Found in {doc_type.lower()} document",
                    "implications": self._get_term_implications(term),
                    "source": "rule_based"
                } for term in key_terms[:5]  # Limit to top 5 terms
            ],
            "classification": {
                "document_type": doc_type,
                "category": "legal",
                "complexity": "high" if len(risks) > 3 else "medium",
                "confidence": 0.7,
                "source": "rule_based"
            },
            "llm_enabled": False,
            "processing_time": processing_time
        }
    
    def _fallback_suggestions(self, content: str) -> List[Dict[str, str]]:
        """Fallback improvement suggestions"""
        return [
            {"type": "clarity", "suggestion": "Consider using more precise legal language", "example": "Use 'shall' instead of 'will' for obligations"},
            {"type": "structure", "suggestion": "Organize clauses in logical order", "example": "Group related terms together"},
            {"type": "consistency", "suggestion": "Maintain consistent terminology throughout", "example": "Use the same term for the same concept"}
        ]
    
    def _fallback_term_extraction(self, content: str) -> List[Dict[str, str]]:
        """Fallback term extraction"""
        terms = []
        for term in self.legal_terms.get("legal_terms", {}).get("contract_terms", []):
            if term.lower() in content.lower():
                terms.append({
                    "term": term,
                    "meaning": f"Standard legal term: {term}",
                    "context": "Found in document",
                    "implications": "Standard legal concept"
                })
        return terms
    
    def _fallback_classification(self, content: str) -> Dict[str, Any]:
        """Fallback document classification"""
        content_lower = content.lower()
        
        # Simple rule-based classification
        if "agreement" in content_lower:
            doc_type = "agreement"
        elif "contract" in content_lower:
            doc_type = "contract"
        elif "memo" in content_lower or "memorandum" in content_lower:
            doc_type = "memorandum"
        else:
            doc_type = "legal document"
        
        return {
            "document_type": doc_type,
            "category": "legal",
            "complexity": "medium",
            "confidence": 0.7
        }
    
    def _fallback_semantic_search(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback semantic search"""
        # Simple keyword matching
        query_terms = query.lower().split()
        results = []
        
        for doc in documents:
            content = doc.get('content', '').lower()
            title = doc.get('title', '').lower()
            
            score = 0
            for term in query_terms:
                if term in content:
                    score += 1
                if term in title:
                    score += 2
            
            if score > 0:
                results.append({
                    **doc,
                    "relevance_score": score,
                    "search_method": "keyword_fallback"
                })
        
        return sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def _extract_terms_rule_based(self, content: str) -> List[str]:
        """Extract terms using rule-based approach"""
        terms = []
        for term in self.legal_terms.get("legal_terms", {}).get("contract_terms", []):
            if term.lower() in content.lower():
                terms.append(term)
        return terms
    
    def _identify_risks_rule_based(self, content: str) -> List[str]:
        """Identify risks using rule-based approach"""
        risks = []
        for risk in self.legal_terms.get("legal_terms", {}).get("risk_indicators", []):
            if risk.lower() in content.lower():
                risks.append(risk)
        return risks
    
    def _classify_document_rule_based(self, content: str) -> str:
        """Classify document using rule-based approach"""
        content_lower = content.lower()
        
        for doc_type in self.legal_terms.get("legal_terms", {}).get("document_types", []):
            if doc_type.lower() in content_lower:
                return doc_type
        
        return "legal document"
    
    def _get_term_meaning(self, term: str, doc_type: str) -> str:
        """Get specific meaning for a legal term"""
        term_lower = term.lower()
        
        if "payment" in term_lower or "compensation" in term_lower:
            return "Financial compensation and payment structure"
        elif "termination" in term_lower or "expiration" in term_lower:
            return "Contract ending and termination procedures"
        elif "liability" in term_lower or "responsibility" in term_lower:
            return "Legal responsibility and risk allocation"
        elif "confidentiality" in term_lower or "privacy" in term_lower:
            return "Information protection and confidentiality obligations"
        elif "indemnification" in term_lower or "indemnity" in term_lower:
            return "Protection against legal claims and damages"
        elif "intellectual property" in term_lower or "ip" in term_lower:
            return "Intellectual property rights and ownership"
        elif "dispute" in term_lower or "arbitration" in term_lower:
            return "Dispute resolution and conflict management"
        elif "governing law" in term_lower or "jurisdiction" in term_lower:
            return "Legal framework and applicable laws"
        else:
            return f"Important legal concept in {doc_type.lower()}"
    
    def _get_term_implications(self, term: str) -> str:
        """Get specific implications for a legal term"""
        term_lower = term.lower()
        
        if "payment" in term_lower or "compensation" in term_lower:
            return "Critical for financial obligations and dispute resolution"
        elif "termination" in term_lower or "expiration" in term_lower:
            return "Essential for legally ending the agreement"
        elif "liability" in term_lower or "responsibility" in term_lower:
            return "Protects parties from legal exposure and risk"
        elif "confidentiality" in term_lower or "privacy" in term_lower:
            return "Safeguards sensitive business and personal information"
        elif "indemnification" in term_lower or "indemnity" in term_lower:
            return "Risk transfer mechanism between contracting parties"
        elif "intellectual property" in term_lower or "ip" in term_lower:
            return "Defines ownership and usage rights of creative works"
        elif "dispute" in term_lower or "arbitration" in term_lower:
            return "Provides structured approach to resolving conflicts"
        elif "governing law" in term_lower or "jurisdiction" in term_lower:
            return "Determines which legal system applies to the contract"
        else:
            return "Important for legal compliance and enforcement"
    
    # Response parsing methods
    def _parse_analysis_response(self, response: str, content: str, start_time: float) -> Dict[str, Any]:
        """Parse LLM analysis response"""
        import time
        import json
        import re
        processing_time = time.time() - start_time
        
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                
                # Extract structured data
                key_terms = parsed_data.get('key_terms', [])
                risks = parsed_data.get('risks', [])
                document_type = parsed_data.get('document_type', 'Unknown')
                summary = parsed_data.get('summary', 'No summary provided')
                recommendations = parsed_data.get('recommendations', [])
                
                # Create structured suggestions from recommendations
                suggestions = []
                suggestion_types = ["clarity", "structure", "completeness", "risk_mitigation", "compliance"]
                for i, rec in enumerate(recommendations):
                    suggestion_type = suggestion_types[i % len(suggestion_types)]
                    suggestions.append({
                        "type": suggestion_type,
                        "suggestion": rec,
                        "example": f"Specific improvement for this document: {rec[:50]}...",
                        "source": "llm"
                    })
                
                # Create structured terms from key terms with specific meanings
                terms = []
                for i, term in enumerate(key_terms):
                    # Create specific meanings based on term content
                    if "payment" in term.lower():
                        meaning = "Payment terms and compensation structure"
                        implications = "Critical for financial obligations and dispute resolution"
                    elif "termination" in term.lower():
                        meaning = "Contract termination and exit provisions"
                        implications = "Essential for ending the agreement legally"
                    elif "liability" in term.lower():
                        meaning = "Legal responsibility and risk allocation"
                        implications = "Protects parties from legal exposure"
                    elif "confidentiality" in term.lower():
                        meaning = "Information protection and privacy obligations"
                        implications = "Safeguards sensitive business information"
                    elif "indemnification" in term.lower():
                        meaning = "Protection against legal claims and damages"
                        implications = "Risk transfer mechanism between parties"
                    else:
                        meaning = f"Important legal concept: {term}"
                        implications = "Key term for legal compliance and enforcement"
                    
                    terms.append({
                        "term": term,
                        "meaning": meaning,
                        "context": f"Found in {document_type.lower()}",
                        "implications": implications,
                        "source": "llm"
                    })
                
                return {
                    "analysis": {
                        "key_terms": key_terms,
                        "risks": risks,
                        "document_type": document_type,
                        "summary": summary,
                        "recommendations": recommendations,
                        "source": "llm"
                    },
                    "suggestions": suggestions,
                    "terms": terms,
                    "classification": {
                        "document_type": document_type,
                        "category": "legal",
                        "complexity": "medium" if len(risks) < 3 else "high",
                        "confidence": 0.9,
                        "source": "llm"
                    },
                    "llm_enabled": True,
                    "processing_time": processing_time
                }
            else:
                # Fallback if JSON parsing fails
                return self._fallback_analysis(content, start_time)
                
        except (json.JSONDecodeError, KeyError, Exception) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Fallback to rule-based analysis
            return self._fallback_analysis(content, start_time)
    
    def _parse_suggestions_response(self, response: str) -> List[Dict[str, str]]:
        """Parse LLM suggestions response"""
        try:
            # Try to extract structured suggestions
            return [
                {
                    "type": "llm_suggestion",
                    "suggestion": response,
                    "example": "LLM-generated improvement",
                    "source": "llm"
                }
            ]
        except:
            return [
                {
                    "type": "llm_suggestion",
                    "suggestion": response,
                    "example": "LLM-generated improvement",
                    "source": "llm"
                }
            ]
    
    def _parse_terms_response(self, response: str) -> List[Dict[str, str]]:
        """Parse LLM terms response"""
        try:
            return [
                {
                    "term": "LLM Analysis",
                    "meaning": response,
                    "context": "Full document analysis",
                    "implications": "Comprehensive legal review",
                    "source": "llm"
                }
            ]
        except:
            return [
                {
                    "term": "LLM Analysis",
                    "meaning": response,
                    "context": "Full document analysis",
                    "implications": "Comprehensive legal review",
                    "source": "llm"
                }
            ]
    
    def _parse_classification_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM classification response"""
        try:
            return {
                "classification": response,
                "parsed": True,
                "source": "llm"
            }
        except:
            return {
                "classification": response,
                "parsed": False,
                "source": "llm"
            }
    
    def _parse_semantic_search_response(self, response: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse LLM semantic search response"""
        try:
            # Try to extract document IDs from the response
            import re
            doc_ids = re.findall(r'ID:\s*(\d+)', response)
            
            if doc_ids:
                # Return documents in the order mentioned by LLM
                results = []
                for doc_id in doc_ids:
                    doc_id = int(doc_id)
                    for doc in documents:
                        if doc.get('id') == doc_id:
                            results.append({
                                **doc,
                                "relevance_score": 0.9 - (len(results) * 0.1),  # Decreasing relevance
                                "search_method": "llm_semantic",
                                "llm_analysis": response
                            })
                            break
                return results[:5]  # Limit to top 5
            else:
                # Fallback: return all documents with LLM analysis
                return [
                    {
                        **doc,
                        "relevance_score": 0.8,
                        "search_method": "llm_semantic",
                        "llm_analysis": response
                    }
                    for doc in documents[:5]
                ]
        except Exception as e:
            logger.error(f"Failed to parse semantic search response: {e}")
            # Fallback to keyword search
            return self._fallback_semantic_search("", documents)

    def get_status(self) -> Dict[str, Any]:
        """Get LLM service status and configuration."""
        return {
            "enabled": self.enabled,
            "model": self.model if self.enabled else None,
            "max_tokens": self.max_tokens if self.enabled else None,
            "temperature": self.temperature if self.enabled else None,
            "api_key_configured": bool(self.api_key),
            "legal_terms_loaded": len(self.legal_terms) > 0,
            "legal_phrases_loaded": len(self.legal_phrases) > 0
        }
