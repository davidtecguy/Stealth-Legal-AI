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
            openai.api_key = self.api_key
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
            
            response = openai.ChatCompletion.create(
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
            Dictionary with analysis results
        """
        if not self.enabled:
            return self._fallback_analysis(content)
        
        system_message = """You are a legal AI assistant. Analyze the provided legal document and extract:
1. Key legal terms and clauses
2. Potential legal risks
3. Document type and category
4. Summary of main points
5. Recommendations for improvement

Provide your analysis in a structured, professional manner."""
        
        prompt = f"""Please analyze this legal document:

{content[:3000]}...

Provide a comprehensive analysis covering:
- Key legal terms identified
- Potential risks or concerns
- Document classification
- Summary of main provisions
- Recommendations for improvement"""
        
        response = self._call_openai(prompt, system_message)
        
        if response:
            return self._parse_analysis_response(response)
        else:
            return self._fallback_analysis(content)
    
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
        
        system_message = """You are a legal search specialist. Analyze the search query and rank documents by relevance. Consider:
1. Semantic meaning
2. Legal concepts
3. Context relevance
4. Term matching
5. Document type relevance"""
        
        # Create document summaries for analysis
        doc_summaries = []
        for doc in documents:
            summary = f"ID: {doc.get('id')}, Title: {doc.get('title')}, Content: {doc.get('content', '')[:500]}..."
            doc_summaries.append(summary)
        
        prompt = f"""Search Query: {query}

Available Documents:
{chr(10).join(doc_summaries)}

Please rank these documents by relevance to the search query, considering semantic meaning and legal context."""
        
        response = self._call_openai(prompt, system_message)
        
        if response:
            return self._parse_semantic_search_response(response, documents)
        else:
            return self._fallback_semantic_search(query, documents)
    
    # Fallback methods when LLM is not available
    def _fallback_analysis(self, content: str) -> Dict[str, Any]:
        """Fallback document analysis using rule-based approach"""
        return {
            "key_terms": self._extract_terms_rule_based(content),
            "risks": self._identify_risks_rule_based(content),
            "document_type": self._classify_document_rule_based(content),
            "summary": content[:200] + "..." if len(content) > 200 else content,
            "recommendations": ["Consider legal review", "Ensure clarity", "Check consistency"]
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
    
    # Response parsing methods
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM analysis response"""
        try:
            # Try to extract structured information
            return {
                "analysis": response,
                "parsed": True,
                "source": "llm"
            }
        except:
            return {
                "analysis": response,
                "parsed": False,
                "source": "llm"
            }
    
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
        # For now, return documents with LLM analysis
        return [
            {
                **doc,
                "llm_analysis": response,
                "search_method": "llm_semantic"
            }
            for doc in documents[:5]  # Limit results
        ]
