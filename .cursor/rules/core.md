---
description: Core development rules that should always be applied to this project
globs:
alwaysApply: true
---

# Core Rules

This file contains core development rules that should always be applied when working on the ha_strava Home Assistant custom component.

## Project Context

This is a Home Assistant custom component that integrates with the Strava API to provide activity data, summary statistics, and photos from Strava activities. The component supports multiple users and uses OAuth2 authentication with webhook-driven updates.

## Core Principles

1. **Home Assistant Integration Standards**: Follow Home Assistant's custom component architecture patterns
2. **Multi-User Support**: All new features must support multiple Strava users
3. **Event-Driven Architecture**: Use Home Assistant events for data flow between components
4. **OAuth2 Security**: Maintain secure OAuth2 implementation for Strava API access
5. **Webhook-First Updates**: Prioritize webhook-driven updates over polling when possible

## Code Quality Standards

- Follow PEP 8 guidelines with 120 character line length
- Use type hints for all function parameters and return values
- Implement proper error handling with specific exception types
- Use async/await patterns consistently
- Follow the existing logging patterns with appropriate log levels

## Architecture Patterns

- Use DataUpdateCoordinator for data management
- Implement proper entity lifecycle management
- Follow Home Assistant's entity naming conventions
- Use constants from const.py for all configuration keys
- Implement proper device information for entity grouping

## Security Considerations

- Never log sensitive data (tokens, API keys, personal information)
- Validate all external API responses
- Use proper error handling for network requests
- Implement rate limiting where appropriate
