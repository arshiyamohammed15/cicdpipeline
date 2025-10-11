"""
Configuration Generator for ZEROUI Extension
Generates package.json, tsconfig.json, and other config files from database
Following Constitution Rules:
- Rule 4: Use Settings Files, Not Hardcoded Numbers
- Rule 5: Keep Good Records + Keep Good Logs
- Rule 8: Make Things Fast + Respect People's Time
"""

import json
import os
from pathlib import Path
from config_manager import ConfigManager

class ConfigGenerator:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = config_manager.logger
    
    def generate_package_json(self, output_path: str = "package.json") -> bool:
        """
        Generate package.json from database configuration
        
        Args:
            output_path: Path to write package.json
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get extension configuration
            ext_config = self.config_manager.get_all_configs('extension_config')
            build_config = self.config_manager.get_all_configs('build_config')
            runtime_config = self.config_manager.get_all_configs('runtime_config')
            
            # Build package.json structure
            package_data = {
                "name": ext_config.get('name', 'zeroui'),
                "displayName": ext_config.get('displayName', 'ZEROUI 2.0 Constitution Validator'),
                "description": ext_config.get('description', 'VS Code extension for ZEROUI 2.0 Constitution validation'),
                "version": ext_config.get('version', '1.0.0'),
                "publisher": ext_config.get('publisher', 'zeroui'),
                "engines": {
                    "vscode": ext_config.get('vscode_engine', '^1.74.0')
                },
                "categories": [
                    "Linters",
                    "Other"
                ],
                "activationEvents": [
                    ext_config.get('activation_event', 'onStartupFinished')
                ],
                "main": ext_config.get('main_file', './out/extension.js'),
                "contributes": {
                    "commands": [
                        {
                            "command": "zeroui.showDecisionPanel",
                            "title": "Show Decision Panel",
                            "category": "ZEROUI"
                        },
                        {
                            "command": "zeroui.validateFile",
                            "title": "Validate Current File",
                            "category": "ZEROUI"
                        },
                        {
                            "command": "zeroui.validateWorkspace",
                            "title": "Validate Workspace",
                            "category": "ZEROUI"
                        }
                    ],
                    "menus": {
                        "commandPalette": [
                            {
                                "command": "zeroui.showDecisionPanel",
                                "when": "true"
                            },
                            {
                                "command": "zeroui.validateFile",
                                "when": "editorTextFocus"
                            },
                            {
                                "command": "zeroui.validateWorkspace",
                                "when": "workspaceFolderCount > 0"
                            }
                        ],
                        "editor/context": [
                            {
                                "command": "zeroui.validateFile",
                                "group": "zeroui",
                                "when": "editorTextFocus"
                            }
                        ]
                    },
                    "configuration": {
                        "title": "ZEROUI",
                        "properties": {
                            "zeroui.enableValidation": {
                                "type": "boolean",
                                "default": runtime_config.get('enable_validation', 'true').lower() == 'true',
                                "description": "Enable ZEROUI 2.0 Constitution validation"
                            },
                            "zeroui.showStatusBar": {
                                "type": "boolean",
                                "default": runtime_config.get('show_status_bar', 'true').lower() == 'true',
                                "description": "Show status bar item"
                            },
                            "zeroui.autoValidate": {
                                "type": "boolean",
                                "default": runtime_config.get('auto_validate', 'false').lower() == 'true',
                                "description": "Automatically validate files on save"
                            },
                            "zeroui.severityLevel": {
                                "type": "string",
                                "enum": ["error", "warning", "info"],
                                "default": runtime_config.get('severity_level', 'warning'),
                                "description": "Minimum severity level to show in status bar"
                            }
                        }
                    }
                },
                "scripts": {
                    "vscode:prepublish": build_config.get('prepublish_command', 'npm run compile'),
                    "compile": build_config.get('compile_command', 'tsc -p ./'),
                    "watch": build_config.get('watch_command', 'tsc -watch -p ./')
                },
                "devDependencies": {
                    "@types/vscode": "^1.74.0",
                    "@types/node": "16.x",
                    "typescript": "^4.9.4"
                }
            }
            
            # Write to file
            with open(output_path, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            self.logger.info(f"Generated package.json at {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate package.json: {e}")
            return False
    
    def generate_tsconfig_json(self, output_path: str = "tsconfig.json") -> bool:
        """
        Generate tsconfig.json from database configuration
        
        Args:
            output_path: Path to write tsconfig.json
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get TypeScript configuration
            ts_config = self.config_manager.get_all_configs('typescript_config')
            
            # Build tsconfig.json structure
            tsconfig_data = {
                "compilerOptions": {
                    "module": ts_config.get('module', 'commonjs'),
                    "target": ts_config.get('target', 'ES2020'),
                    "outDir": ts_config.get('outDir', './out'),
                    "lib": json.loads(ts_config.get('lib', '["ES2020"]')),
                    "sourceMap": ts_config.get('sourceMap', 'true').lower() == 'true',
                    "rootDir": ts_config.get('rootDir', './src'),
                    "strict": ts_config.get('strict', 'true').lower() == 'true'
                },
                "exclude": [
                    "node_modules",
                    ".vscode-test"
                ]
            }
            
            # Write to file
            with open(output_path, 'w') as f:
                json.dump(tsconfig_data, f, indent=2)
            
            self.logger.info(f"Generated tsconfig.json at {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate tsconfig.json: {e}")
            return False
    
    def generate_all_configs(self, output_dir: str = ".") -> bool:
        """
        Generate all configuration files
        
        Args:
            output_dir: Directory to write configuration files
            
        Returns:
            True if all successful, False otherwise
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            success = True
            
            # Generate package.json
            if not self.generate_package_json(str(output_path / "package.json")):
                success = False
            
            # Generate tsconfig.json
            if not self.generate_tsconfig_json(str(output_path / "tsconfig.json")):
                success = False
            
            if success:
                self.logger.info("All configuration files generated successfully")
            else:
                self.logger.error("Some configuration files failed to generate")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to generate all configs: {e}")
            return False

def main():
    """Main function to generate configuration files"""
    try:
        # Initialize configuration manager
        config_manager = ConfigManager()
        
        # Create generator
        generator = ConfigGenerator(config_manager)
        
        # Generate all configuration files
        success = generator.generate_all_configs()
        
        if success:
            print("Configuration files generated successfully!")
            print("Generated files:")
            print("- package.json")
            print("- tsconfig.json")
        else:
            print("Some configuration files failed to generate")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error generating configuration files: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
