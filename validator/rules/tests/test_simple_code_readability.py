"""
Tests for Simple Code Readability Validator (Rules 253-280)

Tests the human-understandable code validation ensuring 8th-grade readability.
"""

import unittest
import ast
from validator.rules.simple_code_readability import SimpleCodeReadabilityValidator
from validator.models import Severity


class TestSimpleCodeReadabilityValidator(unittest.TestCase):
    """Test suite for simple code readability rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = SimpleCodeReadabilityValidator()
    
    # Rule 253: Plain English Variable Names
    def test_rule_253_plain_english_valid(self):
        """Test Rule 253: Valid plain English variable names."""
        content = '''
user_account_manager = "admin"
database_connections = []
settings_manager = {}
calculate_total_price = lambda x, y: x * y
'''
        violations = self.validator._validate_plain_english_names(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_253_plain_english_violation_abbreviation(self):
        """Test Rule 253: Abbreviated variable names."""
        content = '''
usr_ctx_mgr = "admin"
db_conn_pool = []
cfg_mgr = {}
calc_total = lambda x, y: x * y
'''
        violations = self.validator._validate_plain_english_names(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R253')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn('abbreviation', violations[0].message.lower())
    
    def test_rule_253_plain_english_violation_technical_jargon(self):
        """Test Rule 253: Technical jargon in variable names."""
        content = '''
user_entity_manager = "admin"
database_connection_pool = []
configuration_manager = {}
'''
        violations = self.validator._validate_plain_english_names(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R253')
    
    # Rule 254: Self-Documenting Code
    def test_rule_254_self_documenting_valid(self):
        """Test Rule 254: Valid self-documenting code."""
        content = '''
if user_age_is_valid and score_is_within_range:
    return calculate_total_price(quantity, unit_price, tax_rate)

def validate_user_email_and_save_to_database():
    pass
'''
        violations = self.validator._validate_self_documenting_code(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_254_self_documenting_violation_cryptic(self):
        """Test Rule 254: Cryptic variable names and function calls."""
        content = '''
if x > 0 and y < 100:
    return calc(a, b, c)

def processUserData():
    pass
'''
        violations = self.validator._validate_self_documenting_code(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R254')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 255: One Concept Per Function
    def test_rule_255_one_concept_valid(self):
        """Test Rule 255: Valid single-concept functions."""
        content = '''
def calculate_total_price(quantity, unit_price):
    """Calculate the total price for items."""
    return quantity * unit_price

def validate_email_address(email):
    """Check if email format is valid."""
    return "@" in email
'''
        violations = self.validator._validate_one_concept_per_function(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_255_one_concept_violation_too_long(self):
        """Test Rule 255: Function exceeds 20 lines."""
        content = '''
def complex_function():
    """This function does too many things."""
    # Line 1
    x = 1
    # Line 2
    y = 2
    # Line 3
    z = 3
    # Line 4
    a = 4
    # Line 5
    b = 5
    # Line 6
    c = 6
    # Line 7
    d = 7
    # Line 8
    e = 8
    # Line 9
    f = 9
    # Line 10
    g = 10
    # Line 11
    h = 11
    # Line 12
    i = 12
    # Line 13
    j = 13
    # Line 14
    k = 14
    # Line 15
    l = 15
    # Line 16
    m = 16
    # Line 17
    n = 17
    # Line 18
    o = 18
    # Line 19
    p = 19
    # Line 20
    q = 20
    # Line 21 - exceeds limit
    r = 21
    return r
'''
        violations = self.validator._validate_one_concept_per_function(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R255')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn('20 lines', violations[0].message)
    
    def test_rule_255_one_concept_violation_multiple_concepts(self):
        """Test Rule 255: Function does multiple things."""
        content = '''
def process_user_data_and_send_email(user_data):
    """This function does two different things."""
    # First concept: process data
    processed_data = user_data.upper()
    # Second concept: send email
    email_service.send(processed_data)
    return processed_data
'''
        violations = self.validator._validate_one_concept_per_function(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R255')
    
    # Rule 256: Explain the "Why", Not Just the "What"
    def test_rule_256_explain_why_valid(self):
        """Test Rule 256: Valid comments explaining why."""
        content = '''
# Count failed login attempts to detect brute force attacks
failed_attempts = 0

# Check each customer's payment status to identify overdue accounts
for customer in customers:
    if customer.payment_due:
        send_reminder(customer)
'''
        violations = self.validator._validate_comment_why_not_what(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_256_explain_why_violation_what_only(self):
        """Test Rule 256: Comments only explain what, not why."""
        content = '''
# Increment counter
counter += 1

# Loop through array
for item in items:
    process(item)
'''
        violations = self.validator._validate_comment_why_not_what(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R256')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 257: Avoid Mental Gymnastics
    def test_rule_257_avoid_mental_gymnastics_valid(self):
        """Test Rule 257: Valid simple control flow."""
        content = '''
if user_is_logged_in:
    if user_has_permission:
        allow_access()
    else:
        deny_access()
else:
    redirect_to_login()
'''
        violations = self.validator._validate_avoid_mental_gymnastics(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_257_avoid_mental_gymnastics_violation_nested_ternary(self):
        """Test Rule 257: Nested ternary operators."""
        content = '''
result = a if condition1 else b if condition2 else c if condition3 else d
'''
        violations = self.validator._validate_avoid_mental_gymnastics(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R257')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn('nested ternary', violations[0].message.lower())
    
    def test_rule_257_avoid_mental_gymnastics_violation_complex_oneliner(self):
        """Test Rule 257: Complex one-liner."""
        content = '''
return x and y and z and process() if all_conditions_met else None
'''
        violations = self.validator._validate_avoid_mental_gymnastics(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R257')
    
    # Rule 258: Use Real-World Analogies
    def test_rule_258_real_world_analogies_valid(self):
        """Test Rule 258: Valid real-world analogies in comments."""
        content = '''
# Like a taxi stand - cars wait for passengers instead of creating new ones each time
connection_pool = []

# Like a bouncer at a club - only letting in a certain number of people per minute
rate_limiter = RateLimiter(max_requests=100)
'''
        violations = self.validator._validate_real_world_analogies(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_258_real_world_analogies_violation_technical_jargon(self):
        """Test Rule 258: Technical jargon without analogies."""
        content = '''
# Database connection pooling
connection_pool = []

# API rate limiting
rate_limiter = RateLimiter(max_requests=100)
'''
        violations = self.validator._validate_real_world_analogies(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R258')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 259: Progressive Complexity
    def test_rule_259_progressive_complexity_valid(self):
        """Test Rule 259: Valid progressive complexity."""
        content = '''
def calculate_base_price(quantity, unit_price):
    """Calculate the base price."""
    return quantity * unit_price

def add_tax(base_price, tax_rate):
    """Add tax to base price."""
    return base_price * (1 + tax_rate)

def calculate_final_price(quantity, unit_price, tax_rate):
    """Calculate final price with tax."""
    base = calculate_base_price(quantity, unit_price)
    return add_tax(base, tax_rate)
'''
        violations = self.validator._validate_progressive_complexity(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_259_progressive_complexity_violation_monolithic(self):
        """Test Rule 259: Monolithic function doing everything."""
        content = '''
def calculate_everything(quantity, unit_price, tax_rate, discount_rate, shipping_cost):
    """This function does everything in one place."""
    base_price = quantity * unit_price
    tax_amount = base_price * tax_rate
    discount_amount = base_price * discount_rate
    subtotal = base_price + tax_amount - discount_amount
    final_total = subtotal + shipping_cost
    return {
        'base_price': base_price,
        'tax_amount': tax_amount,
        'discount_amount': discount_amount,
        'subtotal': subtotal,
        'final_total': final_total
    }
'''
        violations = self.validator._validate_progressive_complexity(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R259')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 260: Visual Code Layout
    def test_rule_260_visual_layout_valid(self):
        """Test Rule 260: Valid visual code layout."""
        content = '''
def process_user_data(user_data):
    """Process user data with clear layout."""
    
    # Validate input
    if not user_data:
        return None
    
    # Extract information
    name = user_data.get('name')
    email = user_data.get('email')
    
    # Process data
    processed_name = name.strip().title()
    processed_email = email.strip().lower()
    
    # Return result
    return {
        'name': processed_name,
        'email': processed_email
    }
'''
        violations = self.validator._validate_visual_layout(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_260_visual_layout_violation_no_whitespace(self):
        """Test Rule 260: Poor visual layout with no whitespace."""
        content = '''
def process_user_data(user_data):
    if not user_data:
        return None
    name = user_data.get('name')
    email = user_data.get('email')
    processed_name = name.strip().title()
    processed_email = email.strip().lower()
    return {'name': processed_name, 'email': processed_email}
'''
        violations = self.validator._validate_visual_layout(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R260')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 261: Error Messages That Help
    def test_rule_261_helpful_error_messages_valid(self):
        """Test Rule 261: Valid helpful error messages."""
        content = '''
def validate_email(email):
    """Validate email address."""
    if not email:
        raise ValueError("Email address is required. Please enter your email.")
    
    if '@' not in email:
        raise ValueError("Email address '{}' is missing the @ symbol. Please enter a complete email like 'user@example.com'.".format(email))
    
    if '.' not in email.split('@')[1]:
        raise ValueError("Email address '{}' is missing the domain part. Please enter a complete email like 'user@example.com'.".format(email))
'''
        violations = self.validator._validate_helpful_error_messages(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_261_helpful_error_messages_violation_cryptic(self):
        """Test Rule 261: Cryptic error messages."""
        content = '''
def validate_email(email):
    """Validate email address."""
    if not email:
        raise ValueError("Error 500")
    
    if '@' not in email:
        raise ValueError("Invalid format")
    
    if '.' not in email.split('@')[1]:
        raise ValueError("Null pointer exception")
'''
        violations = self.validator._validate_helpful_error_messages(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R261')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 262: Consistent Naming Patterns
    def test_rule_262_consistent_naming_valid(self):
        """Test Rule 262: Valid consistent naming patterns."""
        content = '''
def get_user_data(user_id):
    """Get user data."""
    user = database.get_user(user_id)
    return user

def save_user_data(user_data):
    """Save user data."""
    database.save_user(user_data)
'''
        violations = self.validator._validate_consistent_naming(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_262_consistent_naming_violation_mixed_terms(self):
        """Test Rule 262: Mixed naming terms for same concept."""
        content = '''
def get_user_data(user_id):
    """Get user data."""
    usr = database.get_user(user_id)
    return usr

def fetch_customer_data(customer_id):
    """Fetch customer data."""
    client = database.get_customer(customer_id)
    return client
'''
        violations = self.validator._validate_consistent_naming(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R262')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 263: Avoid Abbreviations
    def test_rule_263_avoid_abbreviations_valid(self):
        """Test Rule 263: Valid full words (no abbreviations)."""
        content = '''
user_identifier = "12345"
database_url = "postgresql://localhost/db"
application_programming_interface = "https://api.example.com"
'''
        violations = self.validator._validate_avoid_abbreviations(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_263_avoid_abbreviations_violation_abbreviated(self):
        """Test Rule 263: Abbreviated words."""
        content = '''
usr_id = "12345"
db_url = "postgresql://localhost/db"
api_endpoint = "https://api.example.com"
calc_result = 42
mgr_instance = Manager()
ctx_data = {}
'''
        violations = self.validator._validate_avoid_abbreviations(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R263')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_263_avoid_abbreviations_allowed_common(self):
        """Test Rule 263: Common abbreviations are allowed."""
        content = '''
user_id = "12345"
database_url = "postgresql://localhost/db"
api_key = "secret"
db_connection = Connection()
'''
        violations = self.validator._validate_avoid_abbreviations(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    # Rule 264: Business Language Over Technical Language
    def test_rule_264_business_language_valid(self):
        """Test Rule 264: Valid business language."""
        content = '''
def save_customer_order(order_data):
    """Save the customer's order."""
    database.save_order(order_data)

def create_user_account(user_info):
    """Create a new user account."""
    account = UserAccount(user_info)
    return account
'''
        violations = self.validator._validate_business_language(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_264_business_language_violation_technical(self):
        """Test Rule 264: Technical language instead of business language."""
        content = '''
def execute_database_transaction(order_data):
    """Execute database transaction."""
    database.transaction(order_data)

def initialize_object_instance(user_info):
    """Initialize object instance."""
    instance = UserAccount(user_info)
    return instance
'''
        violations = self.validator._validate_business_language(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R264')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 265: Show Your Work
    def test_rule_265_show_work_valid(self):
        """Test Rule 265: Valid step-by-step calculations."""
        content = '''
def calculate_final_price(quantity, unit_price, tax_rate, discount_rate):
    """Calculate final price with tax and discount."""
    # Calculate the base cost before tax
    base_price = quantity * unit_price
    
    # Calculate tax amount
    tax_amount = base_price * tax_rate
    
    # Calculate discount amount
    discount_amount = base_price * discount_rate
    
    # Calculate final price
    final_price = base_price + tax_amount - discount_amount
    
    return final_price
'''
        violations = self.validator._validate_show_work(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_265_show_work_violation_complex_expression(self):
        """Test Rule 265: Complex expression without intermediate steps."""
        content = '''
def calculate_final_price(quantity, unit_price, tax_rate, discount_rate):
    """Calculate final price."""
    return (quantity * unit_price) + (quantity * unit_price * tax_rate) - (quantity * unit_price * discount_rate)
'''
        violations = self.validator._validate_show_work(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R265')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 266: Fail Gracefully with Helpful Messages
    def test_rule_266_fail_gracefully_valid(self):
        """Test Rule 266: Valid graceful failure with helpful messages."""
        content = '''
def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return {
            'valid': False,
            'message': 'The password must be at least 8 characters long. Please add {} more characters.'.format(8 - len(password))
        }
    
    if not any(c.isupper() for c in password):
        return {
            'valid': False,
            'message': 'The password must contain at least one uppercase letter. Please add an uppercase letter.'
        }
    
    return {'valid': True, 'message': 'Password is strong enough.'}
'''
        violations = self.validator._validate_fail_gracefully(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_266_fail_gracefully_violation_cryptic_error(self):
        """Test Rule 266: Cryptic error messages without guidance."""
        content = '''
def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        raise ValueError("Validation failed")
    
    if not any(c.isupper() for c in password):
        raise ValueError("Invalid format")
    
    return True
'''
        violations = self.validator._validate_fail_gracefully(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R266')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 267: Code as Documentation
    def test_rule_267_code_as_documentation_valid(self):
        """Test Rule 267: Valid self-documenting code with minimal comments."""
        content = '''
def calculate_total_with_tax(quantity, unit_price, tax_rate):
    """Calculate total price including tax."""
    base_price = quantity * unit_price
    tax_amount = base_price * tax_rate
    return base_price + tax_amount
'''
        violations = self.validator._validate_code_as_documentation(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_267_code_as_documentation_violation_excessive_comments(self):
        """Test Rule 267: Excessive comments explaining what code does."""
        content = '''
def calculate_total_with_tax(quantity, unit_price, tax_rate):
    """Calculate total price including tax."""
    # Multiply quantity by unit price to get base price
    base_price = quantity * unit_price
    # Multiply base price by tax rate to get tax amount
    tax_amount = base_price * tax_rate
    # Add base price and tax amount to get total
    return base_price + tax_amount
'''
        violations = self.validator._validate_code_as_documentation(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R267')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 268: Test Names That Tell a Story
    def test_rule_268_test_names_valid(self):
        """Test Rule 268: Valid descriptive test names."""
        content = '''
def test_user_can_login_with_valid_credentials():
    """Test that user can login with valid credentials."""
    pass

def test_system_shows_helpful_message_when_email_is_invalid():
    """Test that system shows helpful message when email is invalid."""
    pass
'''
        violations = self.validator._validate_test_names(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_268_test_names_violation_generic(self):
        """Test Rule 268: Generic test names."""
        content = '''
def test_user():
    """Test user functionality."""
    pass

def test_error():
    """Test error handling."""
    pass
'''
        violations = self.validator._validate_test_names(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R268')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 269: Constants That Explain Themselves
    def test_rule_269_constants_explain_valid(self):
        """Test Rule 269: Valid self-explaining constants."""
        content = '''
MINIMUM_ADULT_AGE = 18
FIVE_SECONDS_IN_MILLISECONDS = 5000
MAXIMUM_FILE_SIZE_IN_BYTES = 1048576
DEFAULT_TIMEOUT_IN_SECONDS = 30
'''
        violations = self.validator._validate_constants_explain(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_269_constants_explain_violation_magic_numbers(self):
        """Test Rule 269: Magic numbers without explanation."""
        content = '''
if age > 18:
    allow_access()

timeout = 5000
max_size = 1048576
default_timeout = 30
'''
        violations = self.validator._validate_constants_explain(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R269')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    # Rule 270: NO Advanced Programming Concepts
    def test_rule_270_no_advanced_concepts_valid(self):
        """Test Rule 270: Valid simple programming concepts."""
        content = '''
def simple_function(x, y):
    """Simple function with basic logic."""
    if x > 0:
        return y * 2
    else:
        return 0

class SimpleClass:
    """Simple class with basic methods."""
    def __init__(self, value):
        self.value = value
    
    def get_value(self):
        return self.value
'''
        violations = self.validator._validate_no_advanced_concepts(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_270_no_advanced_concepts_violation_lambda(self):
        """Test Rule 270: Lambda functions are banned."""
        content = '''
# Lambda function is banned
square = lambda x: x * x

# List comprehension with lambda is banned
squares = list(map(lambda x: x * x, [1, 2, 3, 4]))
'''
        violations = self.validator._validate_no_advanced_concepts(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R270')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn('lambda', violations[0].message.lower())
    
    def test_rule_270_no_advanced_concepts_violation_decorator(self):
        """Test Rule 270: Decorators are banned."""
        content = '''
@staticmethod
def static_method():
    """Static method with decorator."""
    return "banned"

@property
def property_method(self):
    """Property with decorator."""
    return self._value
'''
        violations = self.validator._validate_no_advanced_concepts(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R270')
    
    def test_rule_270_no_advanced_concepts_violation_async(self):
        """Test Rule 270: Async/await is banned."""
        content = '''
async def async_function():
    """Async function is banned."""
    await some_operation()
    return "result"
'''
        violations = self.validator._validate_no_advanced_concepts(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R270')
    
    # Rule 271: NO Complex Data Structures
    def test_rule_271_no_complex_data_structures_valid(self):
        """Test Rule 271: Valid simple data structures."""
        content = '''
# Simple list
user_names = ["alice", "bob", "charlie"]

# Simple dictionary with 2-3 properties
user_info = {
    "name": "alice",
    "age": 25
}

# Simple string
message = "Hello world"
'''
        violations = self.validator._validate_no_complex_data_structures(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_271_no_complex_data_structures_violation_nested_dict(self):
        """Test Rule 271: Nested dictionaries are banned."""
        content = '''
# Nested dictionary is banned
complex_data = {
    "users": {
        "alice": {
            "profile": {
                "name": "Alice",
                "settings": {
                    "theme": "dark"
                }
            }
        }
    }
}
'''
        violations = self.validator._validate_no_complex_data_structures(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R271')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_271_no_complex_data_structures_violation_array_of_objects(self):
        """Test Rule 271: Array of objects is banned."""
        content = '''
# Array of objects is banned
users = [
    {"name": "alice", "age": 25, "email": "alice@example.com"},
    {"name": "bob", "age": 30, "email": "bob@example.com"},
    {"name": "charlie", "age": 35, "email": "charlie@example.com"}
]
'''
        violations = self.validator._validate_no_complex_data_structures(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R271')
    
    # Rule 272: NO Advanced String Manipulation
    def test_rule_272_no_advanced_string_manipulation_valid(self):
        """Test Rule 272: Valid simple string operations."""
        content = '''
# Simple string concatenation
full_name = first_name + " " + last_name

# Simple string replacement
clean_text = text.replace("old", "new")

# Simple length check
if len(text) > 100:
    print("Text is too long")
'''
        violations = self.validator._validate_no_advanced_string_manipulation(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_272_no_advanced_string_manipulation_violation_regex(self):
        """Test Rule 272: Regular expressions are banned."""
        content = '''
import re

# Regular expression is banned
pattern = re.compile(r'^[a-zA-Z0-9]+$')
match = pattern.match(text)
'''
        violations = self.validator._validate_no_advanced_string_manipulation(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R272')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn('regex', violations[0].message.lower())
    
    def test_rule_272_no_advanced_string_manipulation_violation_template_literals(self):
        """Test Rule 272: Template literals are banned."""
        content = '''
# Template literals are banned
message = f"Hello {name}, you have {count} messages"
formatted = "User: {}, Age: {}".format(name, age)
'''
        violations = self.validator._validate_no_advanced_string_manipulation(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R272')
    
    # Rule 273: NO Complex Error Handling
    def test_rule_273_no_complex_error_handling_valid(self):
        """Test Rule 273: Valid simple error handling."""
        content = '''
def validate_input(value):
    """Validate input with simple checks."""
    if not value:
        return False, "Value is required"
    
    if value < 0:
        return False, "Value must be positive"
    
    return True, "Valid"
'''
        violations = self.validator._validate_no_complex_error_handling(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_273_no_complex_error_handling_violation_try_catch(self):
        """Test Rule 273: Try-catch blocks are banned."""
        content = '''
def risky_operation():
    """Function with try-catch is banned."""
    try:
        result = dangerous_operation()
        return result
    except Exception as e:
        return None
'''
        violations = self.validator._validate_no_complex_error_handling(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R273')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn('try-catch', violations[0].message.lower())
    
    def test_rule_273_no_complex_error_handling_violation_custom_exception(self):
        """Test Rule 273: Custom exceptions are banned."""
        content = '''
class CustomException(Exception):
    """Custom exception is banned."""
    pass

def function_with_custom_exception():
    """Function using custom exception."""
    raise CustomException("Something went wrong")
'''
        violations = self.validator._validate_no_complex_error_handling(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R273')
    
    # Rule 274: NO Advanced Control Flow
    def test_rule_274_no_advanced_control_flow_valid(self):
        """Test Rule 274: Valid simple control flow."""
        content = '''
def simple_decision(value):
    """Simple decision making."""
    if value > 0:
        return "positive"
    else:
        return "negative or zero"

def simple_loop(items):
    """Simple loop."""
    for item in items:
        process_item(item)
'''
        violations = self.validator._validate_no_advanced_control_flow(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_274_no_advanced_control_flow_violation_switch(self):
        """Test Rule 274: Switch statements are banned."""
        content = '''
def switch_like_function(value):
    """Function with switch-like logic is banned."""
    if value == 1:
        return "one"
    elif value == 2:
        return "two"
    elif value == 3:
        return "three"
    else:
        return "other"
'''
        violations = self.validator._validate_no_advanced_control_flow(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R274')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_274_no_advanced_control_flow_violation_recursion(self):
        """Test Rule 274: Recursion is banned."""
        content = '''
def recursive_function(n):
    """Recursive function is banned."""
    if n <= 1:
        return 1
    else:
        return n * recursive_function(n - 1)
'''
        violations = self.validator._validate_no_advanced_control_flow(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R274')
    
    # Rule 275: NO Advanced Functions
    def test_rule_275_no_advanced_functions_valid(self):
        """Test Rule 275: Valid simple functions."""
        content = '''
def simple_function(x, y):
    """Simple function with basic parameters."""
    return x + y

def another_function(name):
    """Another simple function."""
    return "Hello " + name
'''
        violations = self.validator._validate_no_advanced_functions(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_275_no_advanced_functions_violation_default_parameters(self):
        """Test Rule 275: Default parameters are banned."""
        content = '''
def function_with_defaults(x, y=10, z=20):
    """Function with default parameters is banned."""
    return x + y + z
'''
        violations = self.validator._validate_no_advanced_functions(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R275')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_275_no_advanced_functions_violation_higher_order(self):
        """Test Rule 275: Higher-order functions are banned."""
        content = '''
def higher_order_function(func, x):
    """Higher-order function is banned."""
    return func(x)

def apply_function(func, data):
    """Function that takes another function is banned."""
    return [func(item) for item in data]
'''
        violations = self.validator._validate_no_advanced_functions(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R275')
    
    # Rule 276: NO Advanced Array Operations
    def test_rule_276_no_advanced_array_operations_valid(self):
        """Test Rule 276: Valid simple array operations."""
        content = '''
def process_items(items):
    """Process items with simple loop."""
    for i in range(len(items)):
        items[i] = items[i] * 2
    return items

def find_item(items, target):
    """Find item with simple loop."""
    for i in range(len(items)):
        if items[i] == target:
            return i
    return -1
'''
        violations = self.validator._validate_no_advanced_array_operations(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_276_no_advanced_array_operations_violation_map(self):
        """Test Rule 276: Array methods like map are banned."""
        content = '''
def process_with_map(items):
    """Using map is banned."""
    return list(map(lambda x: x * 2, items))

def filter_items(items):
    """Using filter is banned."""
    return list(filter(lambda x: x > 0, items))
'''
        violations = self.validator._validate_no_advanced_array_operations(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R276')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn('map', violations[0].message.lower())
    
    def test_rule_276_no_advanced_array_operations_violation_list_comprehension(self):
        """Test Rule 276: List comprehensions are banned."""
        content = '''
def process_with_comprehension(items):
    """List comprehension is banned."""
    return [x * 2 for x in items if x > 0]
'''
        violations = self.validator._validate_no_advanced_array_operations(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R276')
    
    # Rule 277: NO Advanced Logic
    def test_rule_277_no_advanced_logic_valid(self):
        """Test Rule 277: Valid simple logic."""
        content = '''
def simple_condition(x, y):
    """Simple condition check."""
    if x > 0 and y > 0:
        return True
    else:
        return False

def basic_comparison(a, b):
    """Basic comparison."""
    return a == b
'''
        violations = self.validator._validate_no_advanced_logic(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_277_no_advanced_logic_violation_bitwise(self):
        """Test Rule 277: Bitwise operations are banned."""
        content = '''
def bitwise_operations(x, y):
    """Bitwise operations are banned."""
    result = x & y  # Bitwise AND
    result = x | y  # Bitwise OR
    result = x ^ y  # Bitwise XOR
    return result
'''
        violations = self.validator._validate_no_advanced_logic(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R277')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn('bitwise', violations[0].message.lower())
    
    def test_rule_277_no_advanced_logic_violation_complex_boolean(self):
        """Test Rule 277: Complex boolean algebra is banned."""
        content = '''
def complex_boolean_logic(a, b, c, d):
    """Complex boolean logic is banned."""
    return (a and b) or (c and not d) and (a or c)
'''
        violations = self.validator._validate_no_advanced_logic(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R277')
    
    # Rule 278: NO Advanced Language Features
    def test_rule_278_no_advanced_language_features_valid(self):
        """Test Rule 278: Valid basic language features."""
        content = '''
def basic_function(x):
    """Basic function with simple logic."""
    if x > 0:
        return x * 2
    return 0

class BasicClass:
    """Basic class with simple methods."""
    def __init__(self, value):
        self.value = value
'''
        violations = self.validator._validate_no_advanced_language_features(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_278_no_advanced_language_features_violation_generics(self):
        """Test Rule 278: Generics are banned."""
        content = '''
from typing import List, Dict, Optional

def generic_function(items: List[str]) -> Optional[str]:
    """Generic function is banned."""
    if items:
        return items[0]
    return None
'''
        violations = self.validator._validate_no_advanced_language_features(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R278')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn('generic', violations[0].message.lower())
    
    def test_rule_278_no_advanced_language_features_violation_metaclass(self):
        """Test Rule 278: Metaclasses are banned."""
        content = '''
class Meta(type):
    """Metaclass is banned."""
    pass

class MyClass(metaclass=Meta):
    """Class with metaclass is banned."""
    pass
'''
        violations = self.validator._validate_no_advanced_language_features(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R278')
    
    # Rule 279: NO Advanced Libraries
    def test_rule_279_no_advanced_libraries_valid(self):
        """Test Rule 279: Valid basic built-in usage."""
        content = '''
import os
import sys

def basic_file_operation():
    """Basic file operation with built-ins."""
    if os.path.exists("file.txt"):
        with open("file.txt", "r") as f:
            content = f.read()
        return content
    return None
'''
        violations = self.validator._validate_no_advanced_libraries(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_279_no_advanced_libraries_violation_third_party(self):
        """Test Rule 279: Third-party libraries are banned."""
        content = '''
import pandas as pd
import numpy as np
import requests

def use_third_party_libraries():
    """Using third-party libraries is banned."""
    df = pd.DataFrame({'A': [1, 2, 3]})
    arr = np.array([1, 2, 3])
    response = requests.get('https://api.example.com')
    return df, arr, response
'''
        violations = self.validator._validate_no_advanced_libraries(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R279')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn('third-party', violations[0].message.lower())
    
    def test_rule_279_no_advanced_libraries_violation_framework(self):
        """Test Rule 279: Frameworks are banned."""
        content = '''
from django.http import HttpResponse
from flask import Flask
import fastapi

def use_frameworks():
    """Using frameworks is banned."""
    app = Flask(__name__)
    return app
'''
        violations = self.validator._validate_no_advanced_libraries(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R279')
    
    # Rule 280: ENFORCE Simple Level
    def test_rule_280_enforce_simple_level_valid(self):
        """Test Rule 280: Valid simple, understandable code."""
        content = '''
def calculate_total_price(quantity, unit_price):
    """Calculate the total price for items."""
    # Calculate the base cost
    base_price = quantity * unit_price
    
    # Return the total
    return base_price

def check_user_age(age):
    """Check if user is old enough."""
    minimum_age = 18
    
    if age >= minimum_age:
        return True
    else:
        return False
'''
        violations = self.validator._validate_enforce_simple_level(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_rule_280_enforce_simple_level_violation_complex(self):
        """Test Rule 280: Complex code that 8th grader can't understand."""
        content = '''
def complex_calculation(x, y, z):
    """Complex calculation with advanced concepts."""
    # This uses advanced concepts that are hard to understand
    result = (x * y) + (y * z) - (x * z) / (x + y + z) if (x + y + z) != 0 else 0
    return result

def advanced_logic(a, b, c):
    """Advanced logic with complex conditions."""
    return (a and b) or (c and not a) and (b or c) if a > 0 else False
'''
        violations = self.validator._validate_enforce_simple_level(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R280')
        self.assertEqual(violations[0].severity, Severity.ERROR)
        self.assertIn('8th grader', violations[0].message.lower())
    
    def test_rule_280_enforce_simple_level_violation_technical_jargon(self):
        """Test Rule 280: Technical jargon without explanation."""
        content = '''
def process_entity_aggregation(entity_collection):
    """Process entity aggregation with technical terms."""
    # Technical jargon without explanation
    aggregated_entities = []
    for entity in entity_collection:
        if entity.is_valid():
            aggregated_entities.append(entity)
    return aggregated_entities
'''
        violations = self.validator._validate_enforce_simple_level(content, "test.py")
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R280')
    
    # Integration Tests
    def test_multiple_rule_violations(self):
        """Test multiple rule violations in one file."""
        content = '''
# Multiple violations in one file
usr_mgr = "admin"  # R253: abbreviation
if x > 0 and y < 100:  # R254: cryptic variables
    return calc(a, b, c)  # R254: cryptic function

@staticmethod  # R270: decorator
def complex_function():  # R255: will be too long
    # Line 1
    x = 1
    # Line 2
    y = 2
    # ... (continues to exceed 20 lines)
    # Line 21
    z = 21
    return z
'''
        violations = self.validator.validate(content, "test.py")
        
        # Should have multiple violations
        self.assertGreater(len(violations), 3)
        
        # Check specific rule violations
        rule_ids = [v.rule_id for v in violations]
        self.assertIn('R253', rule_ids)  # Abbreviation
        self.assertIn('R254', rule_ids)  # Cryptic code
        self.assertIn('R270', rule_ids)  # Decorator
    
    def test_no_violations_clean_code(self):
        """Test clean code with no violations."""
        content = '''
def calculate_total_price(quantity, unit_price):
    """Calculate the total price for items."""
    # Calculate the base cost before tax
    base_price = quantity * unit_price
    
    # Return the total price
    return base_price

def validate_user_age(age):
    """Check if user is old enough to access the system."""
    minimum_adult_age = 18
    
    if age >= minimum_adult_age:
        return True
    else:
        return False

def process_user_data(user_data):
    """Process user data with clear steps."""
    # Extract user information
    user_name = user_data.get('name')
    user_email = user_data.get('email')
    
    # Validate the information
    if not user_name:
        return False, "User name is required. Please enter your name."
    
    if not user_email:
        return False, "User email is required. Please enter your email address."
    
    # Return success
    return True, "User data is valid"
'''
        violations = self.validator.validate(content, "test.py")
        self.assertEqual(len(violations), 0)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty file
        violations = self.validator.validate("", "empty.py")
        self.assertEqual(len(violations), 0)
        
        # Single line comment
        violations = self.validator.validate("# This is a comment", "comment.py")
        self.assertEqual(len(violations), 0)
        
        # Single line code
        violations = self.validator.validate("x = 1", "single.py")
        self.assertEqual(len(violations), 0)
        
        # Exactly 20 lines (boundary test for R255)
        content = '''
def exactly_twenty_lines():
    """Function with exactly 20 lines."""
    # Line 1
    a = 1
    # Line 2
    b = 2
    # Line 3
    c = 3
    # Line 4
    d = 4
    # Line 5
    e = 5
    # Line 6
    f = 6
    # Line 7
    g = 7
    # Line 8
    h = 8
    # Line 9
    i = 9
    # Line 10
    j = 10
    # Line 11
    k = 11
    # Line 12
    l = 12
    # Line 13
    m = 13
    # Line 14
    n = 14
    # Line 15
    o = 15
    # Line 16
    p = 16
    # Line 17
    q = 17
    # Line 18
    r = 18
    # Line 19
    s = 19
    # Line 20
    t = 20
    return t
'''
        violations = self.validator._validate_one_concept_per_function(content, "test.py")
        self.assertEqual(len(violations), 0)  # Should pass at exactly 20 lines


if __name__ == '__main__':
    unittest.main()
