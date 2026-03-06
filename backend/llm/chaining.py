"""
Prompt Chaining framework.
Allows running a sequence of prompts where output of one feeds into the next.
"""

import logging
import json
from typing import Callable, Any
from backend.llm.llm_manager import get_llm

logger = logging.getLogger(__name__)

class PromptChain:
    """Executes a chain of LLM steps."""
    
    def __init__(self):
        self.steps = []
        self.llm = get_llm()
        
    def add_step(self, name: str, prompt_template: str, expected_json: bool = False, parser: Callable | None = None):
        """
        Add a step to the chain.
        template context can use {prev_output} to inject the result of the previous step.
        """
        self.steps.append({
            "name": name,
            "template": prompt_template,
            "json": expected_json,
            "parser": parser
        })
        return self
        
    def run(self, initial_context: dict) -> dict:
        """Run the chain sequentially."""
        context = dict(initial_context)
        context["prev_output"] = ""
        
        results = {}
        
        for step in self.steps:
            prompt = step["template"].format(**context)
            
            logger.info(f"Chain step: {step['name']}")
            try:
                # Usually chains require logic/extraction, keeping temp low
                response_text = self.llm.generate(prompt, temperature=0.1)
                
                # Parse if needed
                if step["json"]:
                    from backend.core.safety import validate_llm_json
                    parsed = validate_llm_json(response_text)
                    if not parsed:
                         logger.warning(f"Chain step {step['name']} failed to return valid JSON.")
                         parsed = {}
                    result = parsed
                elif step["parser"]:
                    result = step["parser"](response_text)
                else:
                    result = response_text
                    
            except Exception as e:
                logger.error(f"Chain step {step['name']} failed: {e}")
                result = None
                
            results[step["name"]] = result
            
            # Update context for next step
            context["prev_output"] = result if isinstance(result, str) else json.dumps(result)
            # Also expose the step result directly by name in the context
            context[step["name"]] = result
            
        return results
