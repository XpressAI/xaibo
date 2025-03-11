from pathlib import Path
from ruamel.yaml import YAML
from xaibo import AgentConfig

def _read_yaml_config(filename):
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    yaml = YAML(typ='safe')
    with open(resources_dir / "yaml" / filename) as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
        raw_yaml = yaml.load(content)
    return config, raw_yaml

def _assert_modules_match(config, raw_yaml):
    """Helper to verify modules match between config and raw YAML"""
    assert config.id == raw_yaml["id"]
    
    # Account for implicit response module
    raw_modules = list(raw_yaml["modules"])
    if not any(m["id"] == "__response__" for m in raw_modules):
        raw_modules.append({
            "module": "xaibo.primitives.modules.ResponseHandler",
            "id": "__response__",
            "provides": ["ResponseProtocol"]
        })
    
    assert len(config.modules) == len(raw_modules)
    
    # Test all modules match their raw YAML
    for module, yaml_module in zip(config.modules, raw_modules):
        assert module.module == yaml_module["module"]
        assert module.id == yaml_module["id"]
        # Test optional fields if present
        if "provides" in yaml_module:
            assert module.provides == yaml_module["provides"]
        if "uses" in yaml_module:
            assert module.uses == yaml_module["uses"]
        # Test all config values match
        for key, value in yaml_module.get("config", {}).items():
            assert module.config[key] == value

def _assert_exchange_matches(config, raw_yaml):
    """Helper to verify exchange entries match between config and raw YAML"""
    # Account for implicit exchanges being added
    if "exchange" in raw_yaml:
        raw_exchanges = raw_yaml["exchange"]
    else:
        raw_exchanges = []
        
    # All explicit exchanges should be present
    for yaml_exchange in raw_exchanges:
        matching = [ex for ex in config.exchange 
                   if ex.module == yaml_exchange["module"]
                   and ex.protocol == yaml_exchange["protocol"]
                   and ex.provider == yaml_exchange["provider"]]
        assert len(matching) == 1

def test_load_echo_minimal():
    config, raw_yaml = _read_yaml_config("echo.yaml")
    _assert_modules_match(config, raw_yaml)
    _assert_exchange_matches(config, raw_yaml)

def test_load_echo_complete():
    config, raw_yaml = _read_yaml_config("echo_complete.yaml")
    _assert_modules_match(config, raw_yaml)
    _assert_exchange_matches(config, raw_yaml)

def test_load_stressing_tool():
    config, raw_yaml = _read_yaml_config("stressing_tool_user.yaml")
    _assert_modules_match(config, raw_yaml)
    _assert_exchange_matches(config, raw_yaml)

def test_load_directory():
    """Test loading multiple agent configs from a directory"""
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    yaml_dir = resources_dir / "yaml"
    
    configs = AgentConfig.load_directory(str(yaml_dir))
    
    # Verify expected files were loaded
    expected_files = [
        str(yaml_dir / "echo.yaml"),
        str(yaml_dir / "echo_complete.yaml"),
        str(yaml_dir / "stressing_tool_user.yaml")
    ]

    yaml = YAML(typ='safe')
    for file in expected_files:
        assert file in configs
        
        # Verify each config was loaded correctly
        with open(file) as f:
            raw_yaml = yaml.load(f.read())
            config = configs[file]
            
            _assert_modules_match(config, raw_yaml)
            _assert_exchange_matches(config, raw_yaml)
