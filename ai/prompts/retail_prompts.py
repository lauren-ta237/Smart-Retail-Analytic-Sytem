# this prompts guide on how AI produce structured insights

from backend.app.models.interaction_model import interaction


def store_analysis_prompt(data):
    #Prompt used to analyze general store performance.

    prompt = f"""
    You are an expert retail analyst.
    Analyze the following retail analytics data.

    DATA:
    {data}

    Provide:
    1. Key insights about customer behavior
    2. Zones with highest traffic
    3. Potential problems
    4. Recommendations to improve sales
    """
    return prompt


def product_analysis_prompt(data):
    #Prompt used for analyzing product interactions.

    prompt = f"""
    Analyze this product interaction data.
    {data}

    Explain:
    - Which products attract the most customers
    - Which shelves receive little attention
    - Suggestions to increase engagement
    """
    return prompt


def staffing_prompt(data):
    #AI recommendation for staffing optimization.
    
    prompt = f"""
    Analyze store traffic data.

    {data}

    Recommend:
    - Ideal staff allocation
    - Peak hours
    - Ways to reduce customer wait time
    """
    return prompt


def interactive_store_prompt(question, live_data, historical_data, recommended_actions=None):
    # Prompt used for answering real-time questions with historical intelligence.

    recommended_actions = recommended_actions or []

    prompt = f"""
    You are connected to a smart retail analytics system.

    LIVE DATA:
    {live_data}

    HISTORICAL INTELLIGENCE:
    {historical_data}

    RECOMMENDED ACTIONS:
    {recommended_actions}

    USER QUESTION:
    {question}

    Respond in four short sections:
    1. Direct answer
    2. Evidence from the data
    3. What the trend suggests
    4. Recommended action for the store team

    Keep the answer concise, practical, and grounded only in the provided data.
    """
    return prompt