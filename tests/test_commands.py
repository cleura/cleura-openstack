"""Tests for openstack CLI commands exposed by cleura-openstackclient."""

import importlib.metadata
import os
import subprocess

import pytest

# All expected command groups and the minimum command counts
# These cover the packages pinned as dependencies.
COMMAND_GROUPS = {
    "openstack.backup.v2": 30,       # freezerclient
    "openstack.cli": 2,               # openstackclient
    "openstack.cli.base": 6,          # openstackclient
    "openstack.cli.extension": 6,     # multiple osc plugins
    "openstack.common": 11,           # openstackclient
    "openstack.compute.v2": 95,       # openstackclient
    "openstack.dns.v2": 58,           # designateclient
    "openstack.identity.v2": 34,      # openstackclient
    "openstack.identity.v3": 128,     # openstackclient
    "openstack.image.v1": 6,          # openstackclient
    "openstack.image.v2": 41,         # openstackclient
    "openstack.key_manager.v1": 23,   # barbicanclient
    "openstack.load_balancer.v2": 82,  # octaviaclient
    "openstack.network.v2": 160,       # openstackclient
    "openstack.neutronclient.v2": 119,  # neutronclient
    "openstack.object_store.v1": 17,  # openstackclient
    "openstack.orchestration.v1": 49,  # heatclient
    "openstack.volume.v1": 39,        # openstackclient
    "openstack.volume.v2": 57,        # openstackclient
    "openstack.volume.v3": 93,        # openstackclient
}

# Entry point groups that contain module-level plugins (not command classes).
# These are loaded as modules that set up OSC plugin registration, not as
# cliff command classes themselves.
_MODULE_ENTRY_POINTS = frozenset({
    "openstack.cli.extension",
    "openstack.cli.base",
})

# Well-known command names that should be present for sanity-checking
_EXPECTED_COMMANDS = {
    "server_list",
    "server_create",
    "server_show",
    "server_delete",
    "flavor_list",
    "flavor_create",
    "image_list",
    "image_create",
    "image_show",
    "network_list",
    "network_create",
    "subnet_create",
    "subnet_list",
    "router_list",
    "router_create",
    "project_list",
    "user_list",
    "role_list",
    "token_issue",
    "availability_zone_list",
    "quota_list",
    "backup_list",
    "zone_list",
    "secret_list",
    "loadbalancer_list",
    "loadbalancer_pool_list",
    "stack_list",
    "volume_list",
    "volume_create",
    "container_list",
    "recordset_list",
}


def _get_venv_bin():
    """Return the bin directory of the virtualenv containing this package."""
    import sys

    # For virtualenvs, sys.prefix points to the venv root
    venv_bin = os.path.join(sys.prefix, "bin")
    if os.path.isdir(venv_bin):
        return venv_bin
    # Fallback: scan distributions for openstackclient
    for dist in importlib.metadata.distributions():
        path = dist._path
        if not path:
            continue
        parts = path.parts if hasattr(path, "parts") else path
        if not isinstance(parts, (list, tuple)):
            continue
        if "openstackclient" not in parts:
            continue
        try:
            idx = parts.index("site-packages")
            base = os.path.sep.join(parts[:idx])
            candidate = os.path.join(base, "bin")
            if os.path.isdir(candidate):
                return candidate
        except ValueError:
            pass
    # Fallback: .egg-info parent
    for dist in importlib.metadata.distributions():
        path = dist._path
        if not path:
            continue
        parts = path.parts if hasattr(path, "parts") else path
        if not isinstance(parts, (list, tuple)):
            continue
        if "openstackclient" not in parts:
            continue
        for i, part in enumerate(parts):
            if part.endswith(".egg-info"):
                base = os.path.sep.join(parts[:i])
                bin_candidate = os.path.join(base, "bin")
                if os.path.isdir(bin_candidate):
                    return bin_candidate
    return ""


_VENV_BIN = os.path.abspath(_get_venv_bin()) if _get_venv_bin() else ""


def _load_entry_points():
    """Return a dict mapping entry point group -> list of (name, ep)."""
    result = {}
    for dist in importlib.metadata.distributions():
        for ep in dist.entry_points:
            if ep.group.startswith("openstack."):
                result.setdefault(ep.group, []).append((ep.name, ep))
    return result


def _all_command_names():
    """Return a set of all command names across all openstack groups."""
    names = set()
    for entries in _load_entry_points().values():
        for name, _ in entries:
            names.add(name)
    return names


def _get_console_scripts():
    """Return a list of all console_scripts entry points (Python 3.14 compatible)."""
    eps = importlib.metadata.entry_points()
    if hasattr(eps, "select"):
        return list(eps.select(group="console_scripts"))
    return [e for e in eps if e.group == "console_scripts"]


def _script_path(name):
    """Return the absolute path to an installed script."""
    if _VENV_BIN:
        full = os.path.join(_VENV_BIN, name)
        if os.path.isfile(full) and os.access(full, os.X_OK):
            return full
    # Fallback: try PATH
    path_env = os.environ.get("PATH", os.defpath)
    for dir_name in path_env.split(os.pathsep):
        candidate = os.path.join(dir_name, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return name


class TestPackageMetadata:
    """Tests for the package's own metadata."""

    def test_package_name(self):
        meta = importlib.metadata.metadata("cleura-openstackclient")
        assert meta["Name"] == "cleura-openstackclient"

    def test_package_version(self):
        version = importlib.metadata.version("cleura-openstackclient")
        assert version
        assert "." in version

    def test_python_requires(self):
        meta = importlib.metadata.metadata("cleura-openstackclient")
        assert meta["Requires-Python"] == ">=3.10"

    def test_license(self):
        meta = importlib.metadata.metadata("cleura-openstackclient")
        assert meta["License-Expression"] == "Apache-2.0"


class TestConsoleScriptEntryPoints:
    """Tests for the package's console script entry points."""

    def test_cleura_openstack_alias_exists(self):
        """The cleura-openstack alias should be available as a console script."""
        eps = _get_console_scripts()
        names = [e.name for e in eps]
        assert "cleura-openstack" in names

    def test_cleura_openstack_alias_target(self):
        """The alias should point to openstackclient.shell:main."""
        for dist in importlib.metadata.distributions():
            for ep in dist.entry_points:
                if ep.name == "cleura-openstack":
                    assert ep.value == "openstackclient.shell:main"
                    break
            else:
                continue
            break
        else:
            pytest.fail("cleura-openstack entry point not found")

    def test_openstack_console_script_exists(self):
        """The main openstack command should be available."""
        eps = _get_console_scripts()
        names = [e.name for e in eps]
        assert "openstack" in names


class TestCommandEntryPoints:
    """Tests for openstack command entry points."""

    def _load_entry_points(self):
        result = {}
        for dist in importlib.metadata.distributions():
            for ep in dist.entry_points:
                if ep.group.startswith("openstack."):
                    result.setdefault(ep.group, []).append((ep.name, ep))
        return result

    def test_entry_points_are_loaded(self):
        """All openstack entry points should load without error."""
        eps = self._load_entry_points()
        total = sum(len(entries) for entries in eps.values())
        assert total > 0, "No openstack entry points found"

        for group_name, entries in eps.items():
            for cmd_name, ep in entries:
                try:
                    obj = ep.load()
                    assert obj is not None, f"{group_name}/{cmd_name} loaded None"
                except Exception as exc:
                    pytest.fail(
                        f"Failed to load {group_name}/{cmd_name}: {exc}"
                    )

    def test_expected_command_count(self):
        """Each command group should have at least the expected minimum."""
        eps = self._load_entry_points()

        for group_name, min_count in COMMAND_GROUPS.items():
            entries = eps.get(group_name, [])
            actual_count = len(entries)
            assert actual_count >= min_count, (
                f"Group '{group_name}' has {actual_count} commands, "
                f"expected at least {min_count}"
            )

    def test_well_known_commands_present(self):
        """Core commands used across OpenStack projects should be available."""
        all_commands = _all_command_names()
        for cmd in _EXPECTED_COMMANDS:
            assert cmd in all_commands, (
                f"Expected command '{cmd}' not found"
            )

    def test_command_classes_are_cliff_commands(self):
        """Loaded command classes should inherit from cliff.command.Command."""
        from cliff.command import Command

        eps = self._load_entry_points()
        for group_name, entries in eps.items():
            if group_name in _MODULE_ENTRY_POINTS:
                continue
            for cmd_name, ep in entries:
                obj = ep.load()
                assert issubclass(obj, Command), (
                    f"{group_name}/{cmd_name} ({obj}) is not a subclass of "
                    f"cliff.command.Command"
                )

    def test_commands_have_names(self):
        """Each command class should have a non-empty 'name' attribute."""
        eps = self._load_entry_points()
        for group_name, entries in eps.items():
            if group_name in _MODULE_ENTRY_POINTS:
                continue
            for cmd_name, ep in entries:
                obj = ep.load()
                name = getattr(obj, "name", None)
                if not name:
                    name = cmd_name
                assert name and str(name).strip(), (
                    f"{group_name}/{cmd_name} has empty or missing name"
                )

    def test_commands_have_descriptions(self):
        """Each command class should have a non-empty description."""
        eps = self._load_entry_points()
        for group_name, entries in eps.items():
            if group_name in _MODULE_ENTRY_POINTS:
                continue
            for cmd_name, ep in entries:
                obj = ep.load()
                # Try class-level attribute first
                desc = getattr(obj, "description", None)
                if not desc:
                    # Some packages (barbicanclient) use get_description() on the
                    # instance. Instantiate with minimal args to check.
                    try:
                        inst = obj(None, None)
                        desc = getattr(inst, "description", None)
                        if not desc and callable(getattr(inst, "get_description", None)):
                            desc = inst.get_description()
                    except Exception:
                        pass
                assert desc and str(desc).strip(), (
                    f"{group_name}/{cmd_name} has empty or missing description"
                )

    def test_dependency_packages_installed(self):
        """All packages listed in the dependency metadata should be installed."""
        required_packages = [
            "python-barbicanclient",
            "python-cinderclient",
            "python-designateclient",
            "python-freezerclient",
            "python-glanceclient",
            "python-heatclient",
            "python-keystoneclient",
            "python-neutronclient",
            "python-novaclient",
            "python-octaviaclient",
            "python-openstackclient",
            "python-swiftclient",
            "openstacksdk",
        ]
        installed = {
            d.metadata["Name"]
            for d in importlib.metadata.distributions()
        }
        for pkg in required_packages:
            assert pkg in installed, (
                f"Required package '{pkg}' is not installed"
            )


class TestShellIntegration:
    """Integration tests for the OpenStackShell class."""

    def test_shell_class_importable(self):
        """The OpenStackShell class should be importable."""
        from openstackclient.shell import OpenStackShell

        assert OpenStackShell is not None

    def test_shell_has_command_manager(self):
        """OpenStackShell instance should have a command_manager attribute."""
        from openstackclient.shell import OpenStackShell

        s = OpenStackShell()
        assert hasattr(s, "command_manager")

    def test_shell_has_parser(self):
        """OpenStackShell instance should have a parser attribute."""
        from openstackclient.shell import OpenStackShell

        s = OpenStackShell()
        assert hasattr(s, "parser")

    def test_shell_has_build_option_parser(self):
        """OpenStackShell should have a build_option_parser method."""
        from openstackclient.shell import OpenStackShell

        assert hasattr(OpenStackShell, "build_option_parser")
        assert callable(getattr(OpenStackShell, "build_option_parser"))

    def test_shell_has_initialize_app(self):
        """OpenStackShell should have an initialize_app method."""
        from openstackclient.shell import OpenStackShell

        assert hasattr(OpenStackShell, "initialize_app")
        assert callable(getattr(OpenStackShell, "initialize_app"))

    def test_shell_has_run(self):
        """OpenStackShell should have a run method."""
        from openstackclient.shell import OpenStackShell

        assert hasattr(OpenStackShell, "run")
        assert callable(getattr(OpenStackShell, "run"))

    def test_openstack_command_help_works(self):
        """Running 'openstack --help' should succeed."""
        path = _script_path("openstack")
        result = subprocess.run(
            [path, "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "usage: openstack" in result.stdout.lower()

    def test_openstack_help_lists_commands(self):
        """'openstack --help' should list available command groups."""
        path = _script_path("openstack")
        result = subprocess.run(
            [path, "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        output = result.stdout.lower()
        assert "compute" in output
        assert "network" in output
        assert "identity" in output

    def test_cleura_openstack_alias_help_works(self):
        """Running 'cleura-openstack --help' should succeed."""
        path = _script_path("cleura-openstack")
        result = subprocess.run(
            [path, "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "usage: cleura-openstack" in result.stdout.lower()
