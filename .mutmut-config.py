"""
Configuration for mutmut (mutation testing)
"""


def pre_mutation(context):
    """Called before each mutation"""
    # Skip mutations in test files
    if 'test_' in context.filename:
        context.skip = True
    
    # Skip mutations in __init__.py files
    if context.filename.endswith('__init__.py'):
        context.skip = True
    
    # Skip mutations in demo files
    if 'demo.py' in context.filename or 'app.py' in context.filename:
        context.skip = True
