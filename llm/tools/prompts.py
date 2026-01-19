DEFAULT_TOOL_PROMPT = """
Use the provided tool to retrieve missing information

CRITICAL RULES:
1. If you cannot determine the required arguments for the tool, respond ONLY with: "I don't know how to generate arguments for this tool: [reason]"
2. NEVER hallucinate or guess argument values
3. ONLY call the tool if you have ALL required arguments
4. When you receive tool results, extract and return ONLY minimal relevant information:
   - Database tools: Only table names or column names (e.g., "Tables: payments, users")
   - API tools: Only endpoint paths (e.g., "Endpoints: POST /payments/retry")
   - DO NOT include full raw outputs or irrelevant details"""
