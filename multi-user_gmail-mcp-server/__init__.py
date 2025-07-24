import server
import asyncio
import argparse

def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description='Gmail API MCP Server')
    parser.add_argument('--creds-file-path',
                        required=True,
                       help='OAuth 2.0 credentials file path')

    args = parser.parse_args()
    asyncio.run(server.main(args.creds_file_path))

# Optionally expose other important items at package level
__all__ = ['main', 'server']
