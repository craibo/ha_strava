---
description: Index of all development rules and patterns for the ha_strava project
globs:
alwaysApply: true
---

# Ha-Strava Development Rules Index

This file serves as the central index for all development rules and patterns for the ha_strava Home Assistant custom component project.

## Project Overview

The ha_strava project is a Home Assistant custom component that integrates with the Strava API to provide:

- Activity data and statistics
- Summary statistics (recent, year-to-date, all-time)
- Activity photos and images
- Multi-user support
- Real-time updates via webhooks

## Rule Files

### Core Rules

- **[core.md](core.md)** - Core development rules that should always be applied
- **[index.md](index.md)** - This index file (always applied)

### Architecture and Patterns

- **[home-assistant-patterns.md](home-assistant-patterns.md)** - Home Assistant integration patterns and best practices
- **[architecture-patterns.md](architecture-patterns.md)** - OAuth2, webhooks, coordinators, and multi-user architecture
- **[multi-user-support.md](multi-user-support.md)** - Multi-user support patterns and implementation
- **[credential-validation.md](credential-validation.md)** - Credential validation and uniqueness enforcement
- **[migration.md](migration.md)** - ConfigEntry migration patterns and implementation

### Code Quality and Standards

- **[code-quality.md](code-quality.md)** - Code quality standards, formatting, and style guidelines
- **[testing-patterns.md](testing-patterns.md)** - Testing patterns and guidelines using pytest-homeassistant-custom-component

### API Integration

- **[api-integration.md](api-integration.md)** - Strava API integration patterns and external service integration

## Quick Reference

### When to Use Each Rule File

**Always Applied:**

- `core.md` - Contains core principles and standards that apply to all development work

**For Home Assistant Development:**

- `home-assistant-patterns.md` - When working on component structure, entities, config flows, or OAuth2
- `architecture-patterns.md` - When implementing coordinators, webhooks, or data flow patterns

**For Code Quality:**

- `code-quality.md` - When writing or reviewing code for style, formatting, and best practices
- `testing-patterns.md` - When writing or maintaining tests

**For API Work:**

- `api-integration.md` - When working with Strava API, webhooks, or external services

**For Multi-User Features:**

- `multi-user-support.md` - When implementing or modifying multi-user functionality
- `credential-validation.md` - When implementing credential validation and uniqueness enforcement

## Project-Specific Guidelines

### Technology Stack

- **Home Assistant** - Custom component framework
- **Python 3.9+** - Programming language
- **Strava API v3** - External API integration
- **OAuth2** - Authentication
- **aiohttp** - Async HTTP client
- **pytest-homeassistant-custom-component** - Testing framework

### Key Architecture Principles

1. **Multi-User Support** - All features must support multiple Strava users
2. **Unique Credentials Per User** - Each user must have their own unique Strava app credentials
3. **Individual Webhook Registration** - Each user registers their own webhook subscription
4. **Event-Driven Architecture** - Use Home Assistant events for data flow
5. **Webhook-First Updates** - Prioritize webhook-driven updates over polling
6. **OAuth2 Security** - Maintain secure authentication patterns
7. **Centralized Data Management** - Use coordinators for data fetching and caching

### Development Workflow

1. Follow the patterns defined in the relevant rule files
2. Use the existing codebase as a reference for consistent implementation
3. Ensure all new features support multiple users
4. Write comprehensive tests for new functionality
5. Follow the established error handling and logging patterns

### Code Quality Standards

- **Line Length**: 120 characters (Black configuration)
- **Type Hints**: Required for all function parameters and return values
- **Logging**: Use appropriate log levels with user context
- **Error Handling**: Comprehensive error handling with specific exception types
- **Testing**: Aim for >90% code coverage

### Security Considerations

- Never log sensitive data (tokens, API keys, personal information)
- Validate all external API responses
- Use proper OAuth2 session management
- Implement rate limiting where appropriate
- Sanitize user inputs and API responses

## File Organization

### Source Code Structure

```
custom_components/ha_strava/
├── __init__.py          # Main entry point and webhook handling
├── manifest.json        # Component metadata
├── config_flow.py       # OAuth2 and options configuration
├── const.py            # All constants and configuration keys
├── coordinator.py      # Data update coordinator
├── sensor.py           # Sensor platform implementation
├── camera.py           # Camera platform implementation
└── translations/       # Internationalization support
```

### Test Structure

```
tests/
├── conftest.py         # Test configuration and fixtures
└── custom_components/ha_strava/
    ├── test_config_flow.py
    ├── test_coordinator.py
    ├── test_sensor.py
    ├── test_camera.py
    └── test_init.py
```

## Contributing Guidelines

### Before Making Changes

1. Review the relevant rule files for the area you're working on
2. Understand the existing patterns and architecture
3. Ensure your changes support multi-user functionality
4. Plan your testing approach

### During Development

1. Follow the established patterns and conventions
2. Use the existing code as a reference for consistency
3. Implement proper error handling and logging
4. Write tests for new functionality
5. Consider performance implications for multiple users

### After Implementation

1. Run the full test suite
2. Check code coverage
3. Verify multi-user functionality works correctly
4. Test webhook functionality
5. Review code quality and style

## Maintenance and Updates

### Regular Maintenance Tasks

- Update dependencies in `manifest.json` and `requirements_*.txt`
- Review and update test coverage
- Check for deprecated Home Assistant patterns
- Update documentation and rule files as needed
- Monitor Strava API changes and updates

### Version Updates

- Follow semantic versioning
- Update version in `manifest.json`
- Update changelog and documentation
- Test with multiple Home Assistant versions
- Verify backward compatibility

## Support and Resources

### Home Assistant Resources

- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
- [Custom Component Development](https://developers.home-assistant.io/docs/creating_integration/)
- [Entity Platform Documentation](https://developers.home-assistant.io/docs/core/entity/)

### Strava API Resources

- [Strava API Documentation](https://developers.strava.com/)
- [Strava API Reference](https://developers.strava.com/docs/reference/)
- [Strava Webhooks](https://developers.strava.com/docs/webhooks/)

### Testing Resources

- [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
- [Home Assistant Testing](https://developers.home-assistant.io/docs/development_testing/)
