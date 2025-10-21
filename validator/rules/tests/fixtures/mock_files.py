"""
Mock file structures for validator tests.

Contains mock file paths and directory structures for testing.
"""

MOCK_FILE_STRUCTURES = {
    'valid_project': {
        'src/': {
            'main.py': 'from services import UserService',
            'services/': {
                'user_service.py': 'class UserService: pass',
                '__init__.py': ''
            },
            'models/': {
                'user.py': 'class User: pass',
                '__init__.py': ''
            }
        },
        'tests/': {
            'test_user.py': 'def test_user(): pass'
        }
    },
    
    'mixed_concerns': {
        'ui/': {
            'user_view.py': '''
import database

def render_user(user_id):
    # Bad: Data access in UI
    user = database.query("SELECT * FROM users WHERE id=?", user_id)
    return f"<div>{user['name']}</div>"
'''
        }
    },
    
    'storage_paths': {
        'ide/': {
            'agent/': {
                'receipts/': {
                    'repo-123/': {
                        '2025/': {
                            '10/': {
                                'events.jsonl': ''
                            }
                        }
                    }
                }
            }
        },
        'tenant/': {
            'evidence/': {
                'receipts/': {
                    'dt=2025-10-20/': {
                        'data.jsonl': ''
                    }
                }
            }
        }
    }
}

MOCK_FILE_PATHS = {
    'valid_python': 'src/services/user_service.py',
    'test_file': 'tests/test_user_service.py',
    'ui_file': 'src/ui/components/user_view.py',
    'agent_file': 'src/agent/processor.py',
    'storage_receipt': 'storage/ide/agent/receipts/repo-id/2025/10/events.jsonl',
    'openapi_spec': 'api/openapi.yaml',
    'config_file': 'config/settings.json',
}

