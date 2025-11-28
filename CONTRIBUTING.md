# Contributing to Verizon FiOS Router Integration

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Submission Guidelines](#submission-guidelines)
- [Coding Standards](#coding-standards)
- [Testing](#testing)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all.

### Our Standards

**Examples of behavior that contributes to creating a positive environment:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

---

## How Can I Contribute?

### Reporting Bugs

**Before submitting a bug report:**
- Check the [README](README.md) troubleshooting section
- Search [existing issues](https://github.com/skircr115/ha-verizonFiOS/issues) to see if it's already reported
- Test with the latest version
- Verify your router is compatible (CR1000A, CE1000A)

**When submitting a bug report, include:**
1. Home Assistant version
2. Integration version
3. Router model (CR1000A, CE1000A, etc.)
4. Number of extenders
5. Full error message from logs (enable debug logging)
6. Steps to reproduce
7. Expected vs actual behavior
8. Screenshots if applicable

**Example bug report:**
```markdown
**Environment:**
- HA Version: 2024.1.0
- Integration Version: 1.0.0
- Router Model: CR1000A
- Extenders: 1x CE1000A

**Bug Description:**
Extender sensors not updating after restart

**Steps to Reproduce:**
1. Restart Home Assistant
2. Check extender temperature sensor
3. Sensor shows "unavailable"

**Expected:** Sensor shows temperature
**Actual:** Sensor shows "unavailable"

**Logs (with debug enabled):**
```
[Paste relevant logs here]
```

**Screenshots:**
[If applicable]
```

### Suggesting Enhancements

**Enhancement suggestions are welcome!**

**Before suggesting:**
- Check if it's already suggested in [Discussions](https://github.com/skircr115/ha-verizonFiOS/discussions)
- Consider if it fits the project scope (Verizon FiOS routers only)

**When suggesting, include:**
1. **Clear description** of the enhancement
2. **Use case** - why is this needed?
3. **Examples** - how would it work?
4. **Router compatibility** - which models need this?
5. **Alternatives considered**

**Example enhancement request:**
```markdown
**Feature Request:** Add per-device signal strength sensors

**Use Case:**
I want to see signal strength for each connected device to identify 
devices with poor connectivity and potentially relocate them.

**Proposed Implementation:**
- Parse station_info for per-device signal strength
- Create sensor for top 10 weakest devices
- Use attributes to store all device signals

**Router Compatibility:**
Should work on all models that expose station_info

**Alternatives:**
- Could use markdown card with template to display manually
- Could create automation to track worst performers
```

### Contributing Code

**Types of contributions we're looking for:**
- 🐛 Bug fixes
- ✨ New features (router-related)
- 📝 Documentation improvements
- 🎨 Dashboard card examples
- 🔔 Automation examples
- 🧪 Tests
- 🔌 Support for additional router models
- 🌐 Translations

---

## Development Setup

### Prerequisites

- Home Assistant development environment or test instance
- Python 3.11+
- Git
- Text editor or IDE (VS Code recommended)
- Verizon FiOS router for testing (CR1000A or CE1000A)

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/ha-verizonFiOS.git
cd ha-verizonFiOS

# Add upstream remote
git remote add upstream https://github.com/skircr115/ha-verizonFiOS.git
```

### Set Up Development Environment

```bash
# Option 1: Copy to existing HA instance for testing
cp -r custom_components/verizon_fios /config/custom_components/

# Option 2: Use HA dev container
# (See Home Assistant documentation)

# Configure test credentials
# Settings → Devices & Services → Add Integration → Verizon FiOS Router
```

### Enable Debug Logging

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.verizon_fios: debug
```

### Testing Your Changes

1. Make changes to the code
2. Copy to HA test instance
3. Restart Home Assistant
4. Check Configuration → Devices & Services
5. Verify sensors appear and have values
6. Check logs for errors:
   ```
   Settings → System → Logs
   ```
7. Test manual updates:
   ```
   Developer Tools → Services → homeassistant.update_entity
   ```
8. Wait for automatic update (or adjust update interval)

---

## Submission Guidelines

### Pull Request Process

1. **Create a branch** for your changes
   ```bash
   git checkout -b feature/add-connection-quality-sensor
   ```

2. **Make your changes**
   - Follow coding standards (below)
   - Add/update documentation
   - Test thoroughly on real hardware
   - Consider backwards compatibility

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat(sensors): add per-band connection quality sensors"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/add-connection-quality-sensor
   ```

5. **Open a Pull Request**
   - Go to GitHub
   - Click "New Pull Request"
   - Fill out the template
   - Link related issues
   - Include before/after screenshots

### Commit Message Guidelines

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Scopes:**
- `sensors`: Sensor-related changes
- `api`: Router API changes
- `config`: Config flow changes
- `coordinator`: Data coordinator changes
- `auth`: Authentication changes
- `docs`: Documentation

**Examples:**
```
feat(sensors): add per-device bandwidth tracking

fix(auth): handle routers with non-standard token expiry

docs(readme): add troubleshooting section for extender connectivity

refactor(api): improve JavaScript parsing efficiency

style(sensors): format according to HA style guide
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring

## Router Compatibility
- [ ] Tested on CR1000A
- [ ] Tested on CE1000A (extender)
- [ ] Should work on other Verizon FiOS routers (explain why)
- [ ] Router-agnostic change

## Testing
- [ ] Tested in development environment
- [ ] All existing sensors still work
- [ ] New sensors populate correctly
- [ ] Attributes display properly
- [ ] No errors in logs (debug mode enabled)
- [ ] Manual update works
- [ ] Automatic updates work
- [ ] Device organization intact
- [ ] Config flow tested (for config changes)

## Screenshots
[Before/After screenshots if UI changes]

## Checklist
- [ ] Code follows Home Assistant style guidelines
- [ ] Code follows project conventions
- [ ] Documentation updated (README, docstrings)
- [ ] No breaking changes (or documented with migration guide)
- [ ] Commit messages follow guidelines
- [ ] All checks passing

## Related Issues
Fixes #123
Relates to #456
```

---

## Coding Standards

### Python (Home Assistant Custom Component)

**Follow Home Assistant Style Guide:**
- PEP 8 compliance
- 4 spaces for indentation (no tabs)
- Max line length: 88 characters (Black formatter)
- Type hints for all functions
- Descriptive variable names

**Good:**
```python
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Verizon FiOS Router sensors."""
    coordinator: VerizonRouterCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = []
    
    if coordinator.data:
        processed_data = await hass.async_add_executor_job(
            _process_router_data, coordinator.data, entry
        )
```

**Bad:**
```python
async def setup(hass, entry, add):
    coord = hass.data[DOMAIN][entry.entry_id]
    sensors=[]
    if coord.data:
        data=_process(coord.data,entry)
```

**Type Hints:**
```python
# Always use type hints
def _sanitize_name(name: str) -> str:
    """Sanitize name for entity ID."""
    safe = name.lower()
    return safe

# Return types too
async def fetch_router_data(self) -> dict[str, Any]:
    """Fetch all router data."""
    data = {}
    return data
```

**Error Handling:**
```python
# Always handle exceptions appropriately
try:
    response = await session.post(url, data=data)
    response.raise_for_status()
except aiohttp.ClientError as err:
    raise UpdateFailed(f"Error communicating with router: {err}") from err
```

**Logging:**
```python
# Use appropriate log levels
_LOGGER.debug("Fetching data from router at %s", self.router_url)
_LOGGER.info("Successfully updated router data")
_LOGGER.warning("Router response missing expected field: %s", field_name)
_LOGGER.error("Failed to authenticate with router: %s", error)
```

### Device Info Structure

```python
# Proper device info implementation
@property
def device_info(self) -> DeviceInfo:
    """Return device info for this sensor."""
    return DeviceInfo(
        identifiers={(DOMAIN, self._entry.entry_id)},
        name="Verizon Router",
        manufacturer="Verizon",
        model=self._router_model,
        sw_version=self._firmware_version,
    )
```

### Sensor Best Practices

```python
# Use appropriate device classes
self._attr_device_class = SensorDeviceClass.TEMPERATURE
self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH

# Use correct state classes
self._attr_state_class = SensorStateClass.MEASUREMENT
self._attr_state_class = SensorStateClass.TOTAL_INCREASING

# Use attributes for additional data
@property
def extra_state_attributes(self) -> dict[str, Any]:
    """Return extra state attributes."""
    return {
        "phone": 5,
        "tablet": 2,
        "computer": 8,
    }
```

### Documentation

**Docstrings (Google Style):**
```python
def _parse_js_value(self, js_content: str, variable_name: str) -> Any:
    """
    Parse JavaScript variable values from router response.
    
    The router returns data as JavaScript with addROD() calls.
    This function extracts the value for a given variable name.
    
    Args:
        js_content: The raw JavaScript content from router
        variable_name: The variable name to extract
        
    Returns:
        Parsed value (dict, list, str, etc.) or None if not found
        
    Example:
        >>> api._parse_js_value(js, "router_name")
        "My Verizon Router"
    """
```

**Inline Comments:**
```python
# Good: Explain why, not what
# Verizon uses non-standard ArcMD5: MD5 -> SHA512
arc_md5_result = self._arc_md5(password)

# Bad: State the obvious
# Hash the password
arc_md5_result = self._arc_md5(password)
```

### Configuration Flow

```python
# Use vol.Schema for validation
data_schema = vol.Schema(
    {
        vol.Required(CONF_ROUTER_URL, default=DEFAULT_ROUTER_URL): str,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

# Provide helpful error messages
if not await api.test_connection():
    errors["base"] = "cannot_connect"
```

---

## Testing

### Manual Testing Checklist

Before submitting a PR, verify:

**Installation:**
- [ ] Fresh install works
- [ ] Upgrade from previous version works
- [ ] Config flow completes successfully
- [ ] All files present in integration

**Router Device:**
- [ ] Router device created
- [ ] Correct name from router
- [ ] Correct model displayed
- [ ] Firmware version shown
- [ ] All router sensors present

**Extender Devices:**
- [ ] Extender device(s) created
- [ ] Show "via Router" connection
- [ ] Correct model and name
- [ ] All extender sensors present

**Sensors:**
- [ ] All sensors have values (not "unavailable")
- [ ] Temperature in °C
- [ ] Memory in MB
- [ ] Signal strength in dBm
- [ ] Device counts accurate
- [ ] Attributes display correctly
- [ ] SSIDs show correctly
- [ ] Network quality metrics present

**Functionality:**
- [ ] Login successful
- [ ] Data updates correctly
- [ ] Manual entity update works
- [ ] Automatic updates work (4 hour default)
- [ ] Config entry reload works
- [ ] Integration unload works

**Error Handling:**
- [ ] Wrong password handled gracefully
- [ ] Network error handled (unplug router briefly)
- [ ] Missing data doesn't crash integration
- [ ] Router reboot handled

**Device Analytics:**
- [ ] Device type breakdown in attributes
- [ ] Vendor breakdown in attributes
- [ ] OS breakdown in attributes
- [ ] Counts match reality

**Dashboard:**
- [ ] Device cards work
- [ ] Entity cards work
- [ ] Attribute display works
- [ ] Template sensors work

**Logs:**
- [ ] No Python errors
- [ ] No unexpected warnings
- [ ] Info messages appropriate
- [ ] Debug logs helpful

### Test Environments

**Minimum test:**
- Home Assistant Core 2023.1+
- CR1000A router
- Fresh configuration

**Ideal test:**
- Multiple HA versions (current + previous)
- CR1000A + CE1000A extender
- Different network configurations
- Various device types connected

### Router Data Testing

```python
# Test with sample router data
test_data = {
    'topology': {
        'nodes': [
            {
                'cpuT': 57,
                'memU': 531200,
                'sta_num': 12,
                # ... more fields
            }
        ]
    }
}

# Verify parsing
processed = _process_router_data(test_data, entry)
assert 'router_temperature' in processed
assert processed['router_temperature']['value'] == 57
```

---

## Adding New Sensors

### Sensor Development Process

1. **Identify data source** in router response
2. **Parse data** in `_process_router_data()`
3. **Create sensor definition** with proper attributes
4. **Test with real router**
5. **Document in README**

### Example: Adding New Sensor

```python
# In sensor.py, _process_node_metrics() function

# Add new sensor
sensors[f'{prefix}_channel_utilization'] = {
    "name": "Channel Utilization",
    "value": int(node.get('channel_util', 0)),
    "unit": "%",
    "device_class": None,
    "icon": "mdi:wifi-strength-outline",
    "device_key": device_key
}
```

### Sensor Naming Conventions

- **Router sensors**: `router_<metric_name>`
- **Extender sensors**: `extender_<n>_<metric_name>`
- **Network metrics**: `router_<band>_<metric>`
- **Device analytics**: `router_device_<category>`

### Units and Device Classes

Use standard Home Assistant conventions:
- Temperature: `°C` with `device_class: temperature`
- Memory: `MB` with `device_class: data_size`
- Signal: `dBm` with `device_class: signal_strength`
- Speed: `Mbps` with `device_class: data_rate`
- Count: `devices` with no device_class

---

## Documentation Guidelines

### README Updates

When adding features, update:
- Feature list (with description)
- Sensor table (with example values)
- Installation notes (if needed)
- Dashboard examples (if applicable)
- Troubleshooting (for known issues)

### Code Documentation

```python
# Module-level docstring
"""
Verizon FiOS Router Integration for Home Assistant.

This integration provides comprehensive monitoring of Verizon FiOS
CR1000A and CE1000A routers through local API access.
"""

# Function docstrings
def _sanitize_name(name: str) -> str:
    """
    Sanitize name for entity ID.
    
    Removes special characters and converts to lowercase
    to create valid Home Assistant entity IDs.
    
    Args:
        name: Raw name from router data
        
    Returns:
        Sanitized name safe for entity IDs
    """
```

---

## Review Process

### What We Look For

**✅ Good PRs:**
- Clear, descriptive title and description
- Single feature/fix per PR
- Well-tested on real hardware
- Documented changes
- Follows coding standards
- No breaking changes (or migration guide provided)
- Screenshots for UI changes

**❌ PRs That Need Work:**
- No description or unclear purpose
- Multiple unrelated changes
- Breaks existing functionality
- Missing documentation
- Not tested on router
- Style violations
- Merge conflicts

### Timeline

- We aim to review PRs within **1 week**
- Complex changes may take longer
- Hardware testing may delay review
- Questions/feedback will be provided
- Multiple review rounds may be needed

### Getting Your PR Merged

1. **Address feedback** promptly and thoroughly
2. **Keep PR updated** with main branch
3. **Test on hardware** if requested
4. **Be patient** - we want quality over speed
5. **Be responsive** to questions and comments
6. **Be respectful** in all discussions

---

## Supporting New Router Models

### Adding Router Support

If you have a different Verizon router:

1. **Capture router data**:
   - Enable debug logging
   - Check what endpoints exist
   - Document data structure

2. **Test compatibility**:
   - Try existing integration
   - Note what works/doesn't work

3. **Submit information**:
   - Open an issue with findings
   - Include router model
   - Share sanitized debug logs

4. **Contribute code**:
   - Fork repository
   - Add router-specific handling
   - Test thoroughly
   - Submit PR

---

## Community

### Where to Ask Questions

- 💬 [GitHub Discussions](https://github.com/skircr115/ha-verizonFiOS/discussions) - General questions, ideas
- 🐛 [GitHub Issues](https://github.com/skircr115/ha-verizonFiOS/issues) - Bug reports only
- 🏠 [Home Assistant Forum](https://community.home-assistant.io/) - HA-specific questions
- 💬 [Home Assistant Discord](https://discord.gg/home-assistant) - Real-time chat

### Getting Help

**Stuck on something?**
1. Read the documentation thoroughly
2. Search existing issues and discussions
3. Check Home Assistant documentation
4. Ask in Discussions (not Issues)
5. Be patient - we're volunteers!

**When asking for help:**
- Be specific about the problem
- Include relevant details (versions, models, logs)
- Show what you've tried
- Be respectful of time

---

## Recognition

### Contributors

All contributors will be:
- Listed in README contributors section
- Mentioned in release notes
- Credited in code comments (for major contributions)

### Hall of Fame

Significant contributors may be:
- Given collaborator access
- Invited to project planning discussions
- Recognized as co-maintainers

**Ways to become a significant contributor:**
- Multiple quality PRs
- Excellent documentation contributions
- Active issue triage and support
- New router model support
- Comprehensive testing

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

All contributions must:
- Be your original work or properly attributed
- Not violate any third-party licenses
- Not include proprietary or confidential information

---

## Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email the maintainer privately
2. Include detailed description
3. Provide steps to reproduce
4. Suggest a fix if possible

We will:
- Respond within 48 hours
- Work on a fix
- Credit you in the fix (if desired)
- Coordinate disclosure

### Security Best Practices

When contributing:
- Never commit credentials or API keys
- Use environment variables for secrets
- Validate all user input
- Use secure communication (HTTPS)
- Follow HA security guidelines

---

## Additional Resources

### Home Assistant Development

- [HA Developer Docs](https://developers.home-assistant.io/)
- [HA Architecture](https://developers.home-assistant.io/docs/architecture_index)
- [Integration Quality Scale](https://developers.home-assistant.io/docs/integration_quality_scale_index)

### Python Resources

- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Type Hints](https://docs.python.org/3/library/typing.html)
- [asyncio](https://docs.python.org/3/library/asyncio.html)

### Tools

- [Black](https://black.readthedocs.io/) - Code formatter
- [isort](https://pycqa.github.io/isort/) - Import sorter  
- [pylint](https://pylint.org/) - Code linter
- [mypy](http://mypy-lang.org/) - Static type checker

---

## Questions?

Don't hesitate to ask! We're here to help.

**Contact:**
- Open a [Discussion](https://github.com/skircr115/ha-verizonFiOS/discussions)
- Comment on an existing [Issue](https://github.com/skircr115/ha-verizonFiOS/issues)
- Reach out to [@skircr115](https://github.com/skircr115)

---

**Thank you for contributing! 🎉**

**Your contributions help make this integration better for everyone!**

---

**[← Back to README](README.md)**
