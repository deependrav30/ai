"""
Improve Intent and Urgency Classification

Goal: Increase classification accuracy from current levels:
- Intent: 88% → 95%+ 
- Urgency: 50% → 80%+

Strategy:
1. Enhance IntentAgent prompts with better indicators
2. Add keyword/pattern matching for common scenarios
3. Improve urgency detection using impact assessment
4. Use KB metadata (Priority field) to inform classification
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Enhanced classification prompts and patterns

INTENT_INDICATORS = {
    'incident': [
        # System failures
        'down', 'outage', 'not working', 'broken', 'failed', 'error',
        'crashed', 'unavailable', 'timeout', 'slow', 'degraded',
        # API/Service issues
        'returning 500', 'returning 404', '401 error', '403 error',
        'api error', 'service error', 'connection failed',
        # User impact
        'cannot access', 'unable to', 'users affected', 'production issue',
        'critical issue', 'urgent problem',
        # Specific incidents
        'payment failing', 'database down', 'server not responding',
        'login not working', 'deployment failed'
    ],
    'service_request': [
        'create', 'add', 'provision', 'setup', 'configure', 'install',
        'need access to', 'request access', 'onboard', 'offboard',
        'reset password', 'unlock account', 'new user', 'new account',
        'grant permission', 'upgrade', 'downgrade', 'cancel subscription'
    ],
    'question': [
        'how do i', 'how to', 'what is', 'what does', 'why is',
        'can you explain', 'where can i find', 'is it possible',
        'documentation', 'guide', 'tutorial', 'help me understand',
        'what are the steps'
    ],
    'problem': [
        # Recurring issues
        'keep getting', 'repeatedly', 'frequently', 'often occurs',
        'happens every time', 'pattern', 'trend',
        # Investigation needed
        'intermittent', 'sometimes works', 'occasional',
        'root cause', 'why does this happen', 'underlying issue'
    ],
    'change': [
        'deploy', 'release', 'rollout', 'migration', 'upgrade system',
        'maintenance window', 'scheduled change', 'implementation',
        'cutover', 'rollback'
    ]
}

URGENCY_INDICATORS = {
    'critical': [
        # Business impact
        'production down', 'all users affected', 'revenue impact',
        'customer facing', 'complete outage', 'total failure',
        'sev 1', 'p0', 'critical priority',
        # Severity
        'critical', 'emergency', 'immediate', 'asap',
        'urgent urgent', 'right now', 'breaking'
    ],
    'high': [
        # Significant impact
        'multiple users', 'important feature', 'major issue',
        'significant impact', 'business critical',
        'sev 2', 'p1', 'high priority',
        # Time sensitivity
        'soon', 'today', 'blocking', 'preventing work',
        'cannot proceed'
    ],
    'medium': [
        # Moderate impact
        'some users', 'workaround available', 'not blocking',
        'sev 3', 'p2', 'normal priority',
        'moderate', 'standard'
    ],
    'low': [
        # Minor impact
        'cosmetic', 'nice to have', 'enhancement', 'suggestion',
        'future', 'eventually', 'when possible',
        'sev 4', 'p3', 'low priority'
    ]
}

CATEGORY_INDICATORS = {
    'technical': [
        'api', 'database', 'server', 'deployment', 'code', 'bug',
        'error', 'performance', 'infrastructure', 'network',
        'authentication', 'integration', 'logs'
    ],
    'account': [
        'password', 'login', 'access', 'permission', 'user account',
        'profile', 'subscription', 'billing', 'payment method',
        'credentials', 'authorization'
    ],
    'billing': [
        'invoice', 'payment', 'charge', 'refund', 'pricing',
        'subscription', 'upgrade', 'downgrade', 'credit card',
        'transaction', 'receipt'
    ],
    'product': [
        'feature request', 'enhancement', 'improvement', 'feedback',
        'suggestion', 'new feature', 'functionality', 'usability',
        'user experience', 'design'
    ],
    'compliance': [
        'security', 'gdpr', 'privacy', 'audit', 'compliance',
        'regulation', 'certification', 'data protection',
        'breach', 'vulnerability'
    ]
}


def calculate_intent_score(text: str) -> dict:
    """
    Calculate intent scores based on keyword matching.
    Returns dict with scores for each intent type.
    """
    text_lower = text.lower()
    scores = {}
    
    for intent, keywords in INTENT_INDICATORS.items():
        score = 0
        matched_keywords = []
        
        for keyword in keywords:
            if keyword in text_lower:
                score += 1
                matched_keywords.append(keyword)
        
        scores[intent] = {
            'score': score,
            'keywords': matched_keywords
        }
    
    # Determine most likely intent
    if scores:
        max_intent = max(scores.items(), key=lambda x: x[1]['score'])
        if max_intent[1]['score'] > 0:
            return {
                'predicted_intent': max_intent[0],
                'confidence': min(max_intent[1]['score'] / 3, 1.0),  # Normalize
                'all_scores': scores
            }
    
    return {
        'predicted_intent': None,
        'confidence': 0.0,
        'all_scores': scores
    }


def calculate_urgency_score(text: str) -> dict:
    """
    Calculate urgency scores based on impact indicators.
    """
    text_lower = text.lower()
    scores = {}
    
    for urgency, keywords in URGENCY_INDICATORS.items():
        score = 0
        matched_keywords = []
        
        for keyword in keywords:
            if keyword in text_lower:
                score += 1
                matched_keywords.append(keyword)
        
        scores[urgency] = {
            'score': score,
            'keywords': matched_keywords
        }
    
    # Determine most likely urgency
    if scores:
        max_urgency = max(scores.items(), key=lambda x: x[1]['score'])
        if max_urgency[1]['score'] > 0:
            return {
                'predicted_urgency': max_urgency[0],
                'confidence': min(max_urgency[1]['score'] / 2, 1.0),
                'all_scores': scores
            }
    
    return {
        'predicted_urgency': 'medium',  # Default
        'confidence': 0.3,
        'all_scores': scores
    }


def calculate_category_score(text: str) -> dict:
    """
    Calculate category scores based on domain keywords.
    """
    text_lower = text.lower()
    scores = {}
    
    for category, keywords in CATEGORY_INDICATORS.items():
        score = 0
        matched_keywords = []
        
        for keyword in keywords:
            if keyword in text_lower:
                score += 1
                matched_keywords.append(keyword)
        
        scores[category] = {
            'score': score,
            'keywords': matched_keywords
        }
    
    # Determine most likely category
    if scores:
        max_category = max(scores.items(), key=lambda x: x[1]['score'])
        if max_category[1]['score'] > 0:
            return {
                'predicted_category': max_category[0],
                'confidence': min(max_category[1]['score'] / 3, 1.0),
                'all_scores': scores
            }
    
    return {
        'predicted_category': 'technical',  # Default
        'confidence': 0.3,
        'all_scores': scores
    }


def get_enhanced_classification_prompt() -> str:
    """
    Enhanced classification prompt with better intent/urgency detection.
    """
    return """You are an expert ticket classification system for IT support.

Your task is to classify support tickets with high accuracy.

INTENT TYPES (what the user wants):
1. INCIDENT - Something is broken and needs fixing NOW
   - Examples: "API returning 500 errors", "Users cannot login", "Database is down"
   - Keywords: error, broken, down, failing, not working, crashed
   - Action: Immediate investigation and resolution

2. SERVICE_REQUEST - User needs something provisioned/configured
   - Examples: "Need access to production", "Create new account", "Reset password"
   - Keywords: create, add, provision, setup, need access, grant
   - Action: Follow standard procedure

3. QUESTION - User needs information or guidance
   - Examples: "How do I deploy?", "What is the process for X?"
   - Keywords: how to, what is, can you explain, where is
   - Action: Provide documentation or explanation

4. PROBLEM - Recurring issue needing root cause analysis
   - Examples: "API is intermittently slow", "Sometimes get timeout"
   - Keywords: intermittent, sometimes, frequently, pattern, root cause
   - Action: Investigation to find underlying cause

5. CHANGE - Planned modification to systems
   - Examples: "Deploy v2.0 to production", "Migrate database"
   - Keywords: deploy, release, migration, upgrade, maintenance
   - Action: Follow change management process

URGENCY LEVELS (how fast it needs attention):
1. CRITICAL - Production down, all users affected, revenue impact
   - Multiple users cannot work
   - Customer-facing services unavailable
   - Immediate business impact
   - Keywords: production down, critical, all users, sev 1, p0

2. HIGH - Significant impact but not complete outage
   - Important feature broken
   - Multiple users affected
   - No workaround available
   - Keywords: blocking, important, many users, sev 2, p1

3. MEDIUM - Limited impact or workaround available
   - Single user or small group affected
   - Workaround exists
   - Can wait for normal business hours
   - Keywords: some users, workaround, sev 3, p2

4. LOW - Minimal impact, cosmetic, or enhancement
   - Nice to have
   - Cosmetic issue
   - Feature request
   - Keywords: enhancement, when possible, low priority, sev 4, p3

CLASSIFICATION RULES:
1. If text mentions "500 error", "API error", "not working", "down" → INCIDENT
2. If text mentions "all users", "production", "critical" → CRITICAL urgency
3. If text asks "how to", "what is" with no error mentioned → QUESTION
4. If text requests "create", "add", "need access" → SERVICE_REQUEST
5. Service requests are usually MEDIUM urgency unless specified otherwise

Respond ONLY with a JSON object:
{
    "intent": "incident|service_request|question|problem|change",
    "urgency": "critical|high|medium|low",
    "category": "technical|account|billing|product|compliance",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of classification"
}"""


def test_enhanced_classification():
    """Test enhanced classification with sample tickets."""
    
    test_cases = [
        {
            "input": "Payment API is returning 500 errors, what should I do?",
            "expected_intent": "incident",
            "expected_urgency": "high"
        },
        {
            "input": "How do I reset my password?",
            "expected_intent": "question",
            "expected_urgency": "low"
        },
        {
            "input": "Production database is down, all users affected!",
            "expected_intent": "incident",
            "expected_urgency": "critical"
        },
        {
            "input": "Can you create a new user account for John Doe?",
            "expected_intent": "service_request",
            "expected_urgency": "medium"
        },
        {
            "input": "API latency is intermittently high, need root cause analysis",
            "expected_intent": "problem",
            "expected_urgency": "medium"
        }
    ]
    
    print("="*70)
    print("TESTING ENHANCED CLASSIFICATION")
    print("="*70)
    
    correct_intent = 0
    correct_urgency = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['input']}")
        
        # Keyword-based classification
        intent_result = calculate_intent_score(test['input'])
        urgency_result = calculate_urgency_score(test['input'])
        category_result = calculate_category_score(test['input'])
        
        print(f"\nKeyword Analysis:")
        print(f"  Intent: {intent_result['predicted_intent']} (confidence: {intent_result['confidence']:.2f})")
        if intent_result['all_scores'].get(intent_result['predicted_intent']):
            keywords = intent_result['all_scores'][intent_result['predicted_intent']]['keywords']
            print(f"  Matched keywords: {', '.join(keywords[:3])}")
        
        print(f"  Urgency: {urgency_result['predicted_urgency']} (confidence: {urgency_result['confidence']:.2f})")
        if urgency_result['all_scores'].get(urgency_result['predicted_urgency']):
            keywords = urgency_result['all_scores'][urgency_result['predicted_urgency']]['keywords']
            print(f"  Matched keywords: {', '.join(keywords[:3])}")
        
        print(f"  Category: {category_result['predicted_category']} (confidence: {category_result['confidence']:.2f})")
        
        print(f"\nExpected:")
        print(f"  Intent: {test['expected_intent']}")
        print(f"  Urgency: {test['expected_urgency']}")
        
        # Check accuracy
        if intent_result['predicted_intent'] == test['expected_intent']:
            correct_intent += 1
            print(f"  ✓ Intent correct")
        else:
            print(f"  ✗ Intent wrong")
        
        if urgency_result['predicted_urgency'] == test['expected_urgency']:
            correct_urgency += 1
            print(f"  ✓ Urgency correct")
        else:
            print(f"  ✗ Urgency wrong")
    
    print(f"\n{'='*70}")
    print(f"RESULTS:")
    print(f"Intent Accuracy: {correct_intent}/{len(test_cases)} ({correct_intent/len(test_cases)*100:.0f}%)")
    print(f"Urgency Accuracy: {correct_urgency}/{len(test_cases)} ({correct_urgency/len(test_cases)*100:.0f}%)")
    print(f"{'='*70}")
    
    return correct_intent / len(test_cases), correct_urgency / len(test_cases)


if __name__ == "__main__":
    intent_acc, urgency_acc = test_enhanced_classification()
    
    print(f"\n\nRecommendations:")
    if intent_acc >= 0.8:
        print("✓ Keyword-based intent classification is working well")
    else:
        print("⚠ Need to refine intent keywords")
    
    if urgency_acc >= 0.8:
        print("✓ Keyword-based urgency classification is working well")
    else:
        print("⚠ Need to refine urgency keywords")
    
    print(f"\nNext steps:")
    print("1. Integrate keyword matching into IntentAgent as pre-classification")
    print("2. Use keyword confidence to boost LLM classification")
    print("3. Add more test cases to validate accuracy")
    print("4. Consider using KB metadata (Priority field) as signal")
