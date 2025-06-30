# Python Package Installation Troubleshooting Guide
## Restricted Environment Solutions

### Problem Summary
Installation of Python packages (pytest, pytest-asyncio, pytest-mock) in a containerized/sandboxed Nix-based environment where standard Python tooling is not available in the system PATH.

### Environment Analysis

#### Initial Diagnostic Results
```bash
# Standard commands failed - not in PATH
which python      # Exit code: 1 - not found
which python3     # Exit code: 1 - not found  
which pip         # Exit code: 1 - not found
which pip3        # Exit code: 1 - not found
```

#### System Environment Details
- **Operating System**: Linux 6.6
- **Environment Type**: Nix-based containerized/sandboxed system
- **PATH**: `/nix/store/.../code-oss/bin/remote-cli:/usr/bin:/usr/sbin:~/.global_modules/bin:/google/idx/builtins/bin:node_modules/.bin:/home/user/flutter/bin:/home/user/.pub-cache/bin:/opt/android/platform-tools`
- **Key Indicator**: Nix store paths in PATH indicating immutable filesystem management

### Systematic Python Discovery Process

#### Step 1: Search for Python Installations
```bash
# Search in standard locations (failed)
find /usr -name "python*" -type f -executable 2>/dev/null          # No results
find /usr/local -name "python*" -type f -executable 2>/dev/null    # No results

# Search in Nix store (successful)
find /nix -name "python*" -type f -executable 2>/dev/null | head -10
```

#### Step 2: Located Python Installations
```bash
# Found working Python installations:
/nix/store/604xv36l28g4xd79cfpx5n3y0nc1syr8-python3-3.11.8-env/bin/python
/nix/store/604xv36l28g4xd79cfpx5n3y0nc1syr8-python3-3.11.8-env/bin/python3
/nix/store/8w718rm43x7z73xhw9d6vh8s4snrq67h-python3-3.12.10/bin/python3.12
```

#### Step 3: Verify Python Functionality
```bash
# Test Python version
/nix/store/604xv36l28g4xd79cfpx5n3y0nc1syr8-python3-3.11.8-env/bin/python --version
# Output: Python 3.11.8
```

#### Step 4: Search for Pip Installations
```bash
# Find pip in Nix store
find /nix -name "pip*" -type f -executable 2>/dev/null | head -10

# Found pip installations:
/nix/store/7pr20cckw5ijr42aya7sjf85r0nk6v05-python3.11-pip-25.0.1/bin/pip
/nix/store/brz6ns6myghnxm27pfqlrig1bw2r8h6k-python3.11-pip-24.0/bin/pip
```

### Installation Method Attempts

#### Method 1: Direct pip Installation (FAILED)
```bash
/nix/store/7pr20cckw5ijr42aya7sjf85r0nk6v05-python3.11-pip-25.0.1/bin/pip install pytest==7.4.0

# Error: externally-managed-environment
# × This environment is externally managed
# ╰─> This command has been disabled as it tries to modify the immutable `/nix/store` filesystem.
```

#### Method 2: User-level Installation (FAILED)
```bash
/nix/store/7pr20cckw5ijr42aya7sjf85r0nk6v05-python3.11-pip-25.0.1/bin/pip install --user pytest==7.4.0

# Error: Same externally-managed-environment error
```

#### Method 3: Virtual Environment Creation (SUCCESSFUL)
```bash
# Create virtual environment
/nix/store/604xv36l28g4xd79cfpx5n3y0nc1syr8-python3-3.11.8-env/bin/python -m venv venv

# Activate and verify
source venv/bin/activate && pip --version
# Output: pip 24.0 from /home/user/vendora_unified/venv/lib/python3.11/site-packages/pip (python 3.11)

# Install packages successfully
source venv/bin/activate && pip install pytest==7.4.0
source venv/bin/activate && pip install pytest-asyncio==0.21.1
source venv/bin/activate && pip install pytest-mock==3.11.1
```

### Final Installation Results

#### Successfully Installed Packages
```bash
source venv/bin/activate && pip list

Package        Version
-------------- -------
iniconfig      2.1.0
packaging      25.0
pip            24.0
pluggy         1.6.0
pytest         7.4.0          ✅ TARGET PACKAGE
pytest-asyncio 0.21.1         ✅ TARGET PACKAGE  
pytest-mock    3.11.1         ✅ TARGET PACKAGE
setuptools     65.5.0
```

#### Verification
```bash
source venv/bin/activate && pytest --version
# Output: pytest 7.4.0
```

### Alternative Installation Methods for Similar Environments

#### Option 1: Virtual Environment (Recommended)
```bash
# Find Python executable
find /nix -name "python*" -type f -executable 2>/dev/null | grep -E "python3?$" | head -1

# Create virtual environment
PYTHON_PATH=$(find /nix -name "python*" -type f -executable 2>/dev/null | grep -E "python3?$" | head -1)
$PYTHON_PATH -m venv venv
source venv/bin/activate
pip install <packages>
```

#### Option 2: Force Installation (NOT RECOMMENDED)
```bash
# Override system protection (dangerous)
pip install --break-system-packages <package>
# Warning: This can break system Python installations
```

#### Option 3: Local Package Installation
```bash
# Download and install locally
pip download <package>
python setup.py install --user
```

#### Option 4: Conda/Mamba Alternative
```bash
# If conda/mamba available
conda create -n myenv python=3.11
conda activate myenv
conda install pytest pytest-asyncio pytest-mock
```

### Environment-Specific Troubleshooting Strategies

#### For Nix-based Environments
1. **Search Strategy**: Always search in `/nix/store/` for Python installations
2. **Virtual Environments**: Use virtual environments to bypass immutable filesystem restrictions
3. **Path Discovery**: Use `find` commands rather than `which` for executable discovery

#### For Docker/Container Environments
1. **Check for package managers**: `apt`, `yum`, `apk`, etc.
2. **User-level installations**: Try `pip install --user`
3. **Multi-user installations**: Check `/usr/local/` and `/opt/`

#### For Restricted Corporate Environments
1. **Proxy settings**: Configure pip proxy settings
2. **Certificate issues**: Use `--trusted-host` flags
3. **Internal repositories**: Configure custom PyPI indices

### Permission and Security Considerations

#### File Permissions Check
```bash
# Check write permissions
ls -la ~/
touch ~/test_write && rm ~/test_write || echo "No write permission in home"

# Check virtual environment creation permissions
python -m venv test_venv && rm -rf test_venv || echo "Cannot create virtual environments"
```

#### Security Implications
- Virtual environments provide isolated package installation
- Avoid `--break-system-packages` in production environments
- Use specific package versions for reproducibility
- Document all package installations for security auditing

### Fallback Strategies

#### Strategy 1: Manual Package Installation
```bash
# Download package files manually
wget https://files.pythonhosted.org/packages/.../pytest-7.4.0-py3-none-any.whl
pip install ./pytest-7.4.0-py3-none-any.whl
```

#### Strategy 2: Development Container
```bash
# Create development container with required packages
# Use devcontainer.json or Dockerfile approach
```

#### Strategy 3: Alternative Testing Tools
```bash
# If pytest installation fails, consider alternatives:
python -m unittest  # Built-in testing framework
nose2               # Alternative test runner
```

### Usage Instructions

#### Activating the Environment
```bash
# Navigate to project directory
cd /home/user/vendora_unified

# Activate virtual environment
source venv/bin/activate

# Verify installation
pytest --version
python -c "import pytest_asyncio, pytest_mock; print('All packages available')"
```

#### Running Tests
```bash
# With virtual environment activated
source venv/bin/activate

# Run tests
pytest tests/                           # Run all tests
pytest tests/test_specific.py          # Run specific test file
pytest -v --tb=short                   # Verbose output with short traceback
pytest --asyncio-mode=auto            # Auto-detect async tests
```

### Environment Documentation Template

For future troubleshooting, document:

```bash
# Environment Information
echo "OS: $(uname -a)"
echo "Python locations: $(find /usr /opt /nix -name 'python*' -type f -executable 2>/dev/null | head -5)"
echo "Current PATH: $PATH"
echo "Python executable: $(which python || echo 'Not in PATH')"
echo "Pip executable: $(which pip || echo 'Not in PATH')"
echo "Virtual env support: $(python -c 'import venv; print("Available")' 2>/dev/null || echo 'Not available')"
```

### Success Criteria Checklist

- ✅ Python executable located and functional
- ✅ Pip installation method identified
- ✅ Virtual environment created successfully
- ✅ pytest==7.4.0 installed and verified
- ✅ pytest-asyncio==0.21.1 installed and verified
- ✅ pytest-mock==3.11.1 installed and verified
- ✅ All packages importable in Python
- ✅ pytest command line tool functional

### Lessons Learned

1. **Environment Detection**: Identify environment type (Nix, Docker, etc.) early
2. **Search Strategy**: Use comprehensive search rather than relying on PATH
3. **Virtual Environments**: Often the most reliable solution in restricted environments
4. **Documentation**: Document working solutions for team reproduction
5. **Fallback Planning**: Always have multiple installation strategies ready